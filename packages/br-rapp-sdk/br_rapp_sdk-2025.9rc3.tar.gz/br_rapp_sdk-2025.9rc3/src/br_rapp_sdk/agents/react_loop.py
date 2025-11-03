from .chat_model_client import ChatModelClient
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage
from typing import List, Optional, Type
from .graph import AgentGraph
from .state import AgentState
from .state import AgentTaskResult
from langchain_core.runnables import RunnableGenerator, RunnableConfig
from typing import Literal
from typing_extensions import override, AsyncIterable, AsyncGenerator
from pydantic import ValidationError

class ReActLoop(AgentGraph):
    """ReActLoop implements a ReAct-style loop using a ChatModelClient with associated tools.

        The available tools must be registered in the ChatModelClient used to create the ReActLoop.
        The loop continues until the chat model produces a final answer without any tool calls.

        Args:
            state_schema (Type[AgentState]): The AgentState schema used in the loop.
            loop_name (str): The name of the loop.
            chat_model_client (ChatModelClient): The chat model client to use.
            input_key (str, optional): A key pointing to a string or HumanMessage in the state. Defaults to "input".
                The value at this key is used as input to the ChatModelClient on the first call of the loop.
            output_key (str, optional): A key pointing to a string in the state. Defaults to "output".
                The value at this key is set to the final answer from the ChatModelClient when the loop completes.
            messages_key (str, optional): A key pointing to a List[BaseMessage] in the state. Defaults to None.
                If provided, the value at this key is used as the conversation history for the ChatModelClient.
                The conversation history is updated **in-place** with each response from the ChatModelClient.
            status_key (str, optional): A key pointing to a string in the state. Defaults to None.
                If provided, the value at this key is updated with the current status of the loop.
                Useful to beautify the streamed output of the loop.

        Methods:
            as_runnable() -> RunnableGenerator: Returns a RunnableGenerator for the ReactLoop, wrapping
                the `astream` method. Allows the ReActLoop to be used as a node (subgraph) in a larger graph.
        
        Example:
            ```python
            from br_rapp_sdk.agents import AgentGraph, AgentState, ChatModelClient, ReActLoop
            from langchain.tools import tool

            class RNGClient(ChatModelClient):
                ...
            
            class RNGAgentState(AgentState):
                user_input: str
                model_output: str
                conversation_history: List[BaseMessage] = []
                agent_status: Optional[str] = None
                ...
            
            @tool
            def generate_random_numbers(int min: int, int max: int, int n: int) -> str:
                ""\"Generate n random numbers between min and max (inclusive).""\"
                ...
            
            class RNGAgentGraph(AgentGraph):
                def __init__(self):
                    self.rng_client = RNGClient(tools=[generate_random_numbers])
                    self.rng_loop = ReActLoop(
                        state_schema=RNGAgentState,
                        loop_name="rng_loop",
                        chat_model_client=self.rng_client,
                        input_key="user_input",
                        output_key="model_output",
                        messages_key="conversation_history",
                        status_key="agent_status",
                    )
                    graph_builder = StateGraph(RNGAgentState)
                    ...
                    graph_builder.add_node("rng_loop", self.rng_loop.as_runnable())
                    ...
                    super().__init__(graph_builder, ...)
            ```
    """
    def __init__(
        self,
        state_schema: Type[AgentState],
        loop_name: str,
        chat_model_client: ChatModelClient,
        input_key: str = "input",
        output_key: str = "output",
        messages_key: Optional[str] = None,
        status_key: Optional[str] = None,
    ) -> None:
        self.parent_state_schema = state_schema
        self.loop_name = loop_name
        self.chat_model_client = chat_model_client
        self.input_key = input_key
        self.output_key = output_key
        self.messages_key = messages_key
        self.status_key = status_key
        self._internal_messages_key = messages_key or f"{loop_name}.messages"

        def _tools_or_cleanup(state) -> Literal["tools", "cleanup"]:
            if state.br_rapp_sdk_buffer:
                return "tools"
            return "cleanup"

        graph_builder = StateGraph(state_schema)
        graph_builder.add_node("prepare", self._prepare_for_loop)
        graph_builder.add_node("llm", self._llm)
        graph_builder.add_node("tools", ToolNode(
            tools=chat_model_client.tools,
            messages_key="br_rapp_sdk_buffer",
        ))
        graph_builder.add_node("cleanup", self._cleanup_after_loop)

        graph_builder.add_edge(START, "prepare")
        graph_builder.add_edge("prepare", "llm")
        graph_builder.add_conditional_edges("llm", _tools_or_cleanup)
        graph_builder.add_edge("tools", "llm")
        graph_builder.add_edge("cleanup", END)
        super().__init__(
            graph_builder=graph_builder,
            use_checkpoint=False,
            logger_name=f"react_loop.{loop_name}"
        )

    @override
    async def astream(
        self,
        generator: AsyncGenerator,
        config: RunnableConfig,
    ) -> AsyncIterable[AgentTaskResult]:
        """Streams the ReAct loop for each AgentState instance from the input generator.
        It expects the input generator to yield exactly one AgentState instance;
        if multiple instances are found, only the first instance is processed but the stream
        is fully consumed.

        Args:
            generator (AsyncGenerator): An async generator yielding AgentState instances.
            config (RunnableConfig): The runnable configuration.

        Yields:
            AgentState: The updated AgentState after each step in the loop.
        """
        instance_found = False
        async for item in generator:
            if instance_found:
                self._log("Warning: Multiple instances found in input generator. Only the first will be processed.", "warning")
            else:
                instance_found = True
                async for sub_item in self._astream_instance(item, config):
                    continue
                yield sub_item

    async def _astream_instance(
        self,
        state: Type[AgentState],
        config: RunnableConfig,
    ) -> AsyncIterable[Type[AgentState]]:
        """Streams the ReAct loop for a single AgentState instance.

        Args:
            state (Type[AgentState]): The initial state for the loop.
            config (RunnableConfig): The runnable configuration.

        Yields:
            Type[AgentState]: The updated state after each step in the loop.

        Raises:
            ValueError: If the input_key or output_key is not found in the state,
                or if the input_key does not point to a string or HumanMessage,
                or if the messages_key (if provided) does not point to a List[BaseMessage].
        """
        state_dict = state.model_dump()
        if self.input_key not in state_dict:
            raise ValueError(f"Input key '{self.input_key}' not found in state.")
        if self.output_key not in state_dict:
            raise ValueError(f"Output key '{self.output_key}' not found in state.")
        if self.messages_key and self.messages_key not in state_dict:
            raise ValueError(f"Messages key '{self.messages_key}' not found in state.")

        input = state_dict[self.input_key]
        if not isinstance(input, str) and not isinstance(input, HumanMessage):
            raise ValueError(f"Key '{self.input_key}' must point to a string or HumanMessage. Found {type(input)} instead.")
        # TODO: also check if all messages are BaseMessage instances
        messages = state_dict[self.messages_key] if self.messages_key else []
        if not isinstance(messages, List):
            raise ValueError(f"Key '{self.messages_key}' must point to a List[BaseMessage]. Found {type(messages)} instead.")
        for msg in messages:
            try:
                BaseMessage.model_validate(msg)
            except ValidationError as e:
                raise ValueError(f"Key '{self.messages_key}' must point to a List[BaseMessage]. Found item of type {type(msg)} instead.")

        stream = self._graph.astream(state, config)
        async for item in stream:
            state_item = self.parent_state_schema.model_validate(item)
            yield state_item
    
    def _prepare_for_loop(
        self,
        state: Type[AgentState],
    ) -> Type[AgentState]:
        """Prepares the state for entering the ReAct loop.
        Initializes the conversation history and buffer, and updates the status if a status_key is provided.
        The buffer is used to hold AI/Tool Messages between iterations of the loop.
        """
        self._log(
            f"Node `{self.loop_name}.prepare_for_loop`: invoked",
            "debug",
        )
        if self.messages_key:
            state.br_rapp_sdk_extra[self._internal_messages_key] = getattr(state, self.messages_key)
        else:
            state.br_rapp_sdk_extra[self._internal_messages_key] = []
        state.br_rapp_sdk_buffer = []
        if self.status_key:
            state = state.model_copy(update={
                self.status_key: "Calling LLM..."
            })
        self._log(
            f"Node `{self.loop_name}.prepare_for_loop`: prepared",
            "debug",
        )
        return state
    
    async def _llm(
        self,
        state: Type[AgentState],
    ) -> AsyncIterable[Type[AgentState]]:
        """Invokes the chat model client with the current input and conversation history.
        If the buffer is non-empty, it is used as input instead of the input_key from the state and
        then cleared.
        If the chat model produces tool calls, they are added to the buffer for processing in the ToolNode.
        If a status_key is provided, the status is updated to reflect the current operation.
        """
        self._log(
            f"Node `{self.loop_name}.llm`: invoked",
            "debug",
        )
        tool_messages = state.br_rapp_sdk_buffer
        state.br_rapp_sdk_buffer = []
        if self.status_key:
            state = state.model_copy(update={
                self.status_key: "Calling LLM...",
            })
            yield state
        try:
            # If there are tool messages, use them as input; otherwise, use the input key from state
            input = (
                tool_messages
                or (HumanMessage(state_input) if isinstance((state_input := getattr(state, self.input_key)), str) else state_input)
            )
            response = self.chat_model_client.invoke(
                input=input,
                history=state.br_rapp_sdk_extra[self._internal_messages_key],
            )
        except Exception as e:
            raise RuntimeError(f"Error invoking chat model client: {e}") from e
        if response.tool_calls:
            state.br_rapp_sdk_buffer = [response]
            if self.status_key:
                state = state.model_copy(update={
                    self.status_key: "Running tools...",
                })
        else:
            state = state.model_copy(update={self.output_key: response.content})  
        self._log(
            f"Node `{self.loop_name}.llm`: completed",
            "debug",
        )
        yield state
    
    def _cleanup_after_loop(
        self,
        state: Type[AgentState],
    ) -> Type[AgentState]:
        """Cleans up the state after exiting the ReAct loop.
        Restores the conversation history from the internal key to the messages_key in the state
        and removes the internal key from the `br_rapp_sdk_extra` dictionary in the state.
        """
        self._log(
            f"Node `{self.loop_name}.cleanup`: invoked",
            "debug",
        )
        state = state.model_copy(update={
            self.messages_key: state.br_rapp_sdk_extra[self._internal_messages_key]
        })
        if self._internal_messages_key in state.br_rapp_sdk_extra:
            del state.br_rapp_sdk_extra[self._internal_messages_key]
        self._log(
            f"Node `{self.loop_name}.cleanup`: completed",
            "debug",
        )
        return state

    def as_runnable(
        self
    ) -> RunnableGenerator:
        """Returns a RunnableGenerator for the ReActLoop, wrapping the `astream` method.
        Allows the ReActLoop to be used as a node (subgraph) in a larger graph.
        """
        return RunnableGenerator(self.astream, name=self.loop_name)
