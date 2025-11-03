import asyncio
import uuid
import httpx
import uvicorn
from ..common import create_logger
from ._executor import MinimalAgentExecutor
from .graph import AgentGraph
from a2a.client import ClientConfig, ClientFactory
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, Message, TextPart
from mcp.server import FastMCP
from starlette.applications import Starlette
from threading import Thread
from typing import Optional

_logger = create_logger(__name__, "debug")

class AgentApplication:
    """Agent Application based on `Starlette`.

    Attributes:
        agent_card (AgentCard): The agent card containing metadata about the agent.
        agent_graph (AgentGraph): The agent graph that defines the agent's behavior and capabilities.
    
    Example:
    ```python
        import httpx
        import json
        import uvicorn
        from a2a.types import AgentCard
        from br_rapp_sdk.agents import AgentApplication

        with open('./agent.json', 'r') as file:
            agent_data = json.load(file)
            agent_card = AgentCard.model_validate(agent_data)
            logger.info(f'Agent Card loaded: {agent_card}')
        
        url = httpx.URL(agent_card.url)
        graph = MyAgentGraph()
        agent = AgentApplication(
            agent_card=agent_card,
            agent_graph=graph,
        )

        uvicorn.run(agent.build(), host=url.host, port=url.port)
    ```
    """

    def __init__(
        self,
        agent_card: AgentCard,
        agent_graph: AgentGraph,
        a2a_port: int = 9900,
        mcp_port: int = 9800,
    ):
        """
        Initialize the AgentApplication with an agent card and agent graph.
        Args:
            agent_card (AgentCard): The agent card.
            agent_graph (AgentGraph): The agent graph implementing the agent's logic.
        """
        self._agent_executor = MinimalAgentExecutor(agent_graph)
        self.agent_card = agent_card

        self._httpx_client = httpx.AsyncClient()
        self._request_handler = DefaultRequestHandler(
            agent_executor=self._agent_executor,
            task_store=InMemoryTaskStore(),
        )
        self._a2a_server = A2AStarletteApplication(
            agent_card=self.agent_card,
            http_handler=self._request_handler
        )
        self.a2a_port = a2a_port
        self.mcp_port = mcp_port

        self._mcw_wrap_a2a_client_factory = ClientFactory(
            config=ClientConfig(
                streaming=False,
                httpx_client=httpx.AsyncClient(timeout=180),
            ),
        )

    @property
    def agent_graph(self) -> AgentGraph:
        """Get the agent graph."""
        return self._agent_executor.agent_graph
    
    def _build_a2a_application(self) -> Starlette:
        """Build the A2A Starlette application.
        
        Returns:
            Starlette: The built Starlette application.
        """
        return self._a2a_server.build()

    def _build_mcp_application(self) -> FastMCP:
        mcp = FastMCP(
            name=self.agent_card.name,
            host="0.0.0.0",
            port=self.mcp_port,
        )

        @mcp.tool(
            name=f"get_{self.agent_card.name.lower().replace(' ', '_')}_card",
        )
        def get_agent_card() -> str:
            """
            Get the Agent Card as a JSON string, i.e. a description of the Agent and its capabilities.

            Returns:
                str: The agent card in JSON format.
            """
            return self.agent_card.model_dump_json()

        @mcp.tool(
            name=f"call_{self.agent_card.name.lower().replace(' ', '_')}",
        )
        def call_agent(
            query: str,
            context_id: Optional[str] = None,
            message_id: str = "1",
        ) -> str:
            """
            Call the Agent with a query and return the response.

            Args:
                query (str): The input query for the Agent.
                context_id (Optional[str]): The context ID for the conversation. Defaults to None.
                    If None, a random context ID will be generated calling `uuid.uuid4()`.
                message_id (str): The message ID in the conversation. Defaults to "1".

            Returns:
                str: The Agent's response.
            """
            async def get_response_from_stream() -> str:
                client = self._mcw_wrap_a2a_client_factory.create(card=self.agent_card)
                message = Message(
                    context_id=context_id or str(uuid.uuid4()),
                    message_id=message_id,
                    role="user",
                    parts=[TextPart(text=query)]
                )
                stream = client.send_message(message)
                item = await anext(stream)

                response = None
                if isinstance(item, Message):
                    if item.parts and item.parts[0].root.kind == "text":
                        response = item.parts[0].root.text
                    else:
                        _logger.warning("Received Message with non-text part; ignoring.")
                else:
                    task = item[0]
                    if task.artifacts:
                        artifact = task.artifacts[0]
                        if artifact.parts and artifact.parts[0].root.kind == "text":
                            response = artifact.parts[0].root.text
                        else:
                            _logger.warning("Received Artifact with non-text part; ignoring.")

                if response is None:
                    response = "No valid response received."
                    _logger.warning("No valid response was obtained from the agent stream.")
                return response

            try:
                result = {}
                def runner(coro):
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result["value"] = loop.run_until_complete(coro)
                    except Exception as e:
                        result["error"] = e
                    finally:
                        pending = asyncio.all_tasks(loop)
                        for task in pending:
                            task.cancel()
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        loop.close()

                t = Thread(
                    target=runner,
                    args=(get_response_from_stream(),),
                )
                t.start()
                t.join()

                if "error" in result:
                    raise result["error"]
                response = result["value"]
            except Exception as e:
                _logger.error(f"Error while getting response from Agent: {e}")
                response = f"An error occurred while processing your request: {e}"
            return response

        return mcp

    def run(
        self,
        expose_mcp: bool = False,
    ) -> None:
        """Run the agent application.

        Args:
            expose_mcp (bool, optional): Whether to expose the MCP protocol. Defaults to False.
                **This parameter isn't fully supported yet and may lead to unexpected behavior
                when set to True.**
            
        Raises:
            ValueError: If no protocols are specified to be exposed.
        """
        a2a_app = self._build_a2a_application()
        mcp_app = self._build_mcp_application()

        a2a_server_config = uvicorn.Config(
            app=a2a_app,
            host="0.0.0.0",
            port=self.a2a_port,
            reload=False,
        )
        a2a_server = uvicorn.Server(config=a2a_server_config)

        t_a2a = Thread(target=lambda: a2a_server.run())
        t_mcp = Thread(target=lambda: asyncio.run(mcp_app.run_streamable_http_async()))

        t_a2a.start()
        if expose_mcp:
            t_mcp.start()
            t_mcp.join()        
        t_a2a.join()
