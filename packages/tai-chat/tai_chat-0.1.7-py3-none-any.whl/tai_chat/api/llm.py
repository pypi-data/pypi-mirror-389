"""
LLM
"""
from tai_alphi import Alphi
from langchain.chat_models import BaseChatModel
from langchain_openai.chat_models import ChatOpenAI, AzureChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage, AIMessageChunk, AIMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver, AsyncConnectionPool

from .config import LLMConfig
from .types import WebsocketMessageType
from .websockets import connection_manager
from .utils import add_message
from .tools import tools

logger = Alphi.get_logger_by_name("tai-chatbot")

class LLM:

    def __init__(self, prompt: str = None):
        self.config = LLMConfig.load()
        self.prompt = SystemMessage(content=prompt or '\n'.join(self.config.prompt))
        self._model: BaseChatModel  = None
        self._pool: AsyncConnectionPool | None = None
    
    @property
    def pool(self) -> AsyncConnectionPool:
        """Obtener pool de conexiones a BD"""
        if self._pool is None:
            self._pool = AsyncConnectionPool(conninfo=self.config.context_database_url, open=False)
        
        return self._pool

    async def init(self):
        """Inicializar pool y checkpointer (llamar al arrancar la app)"""
        await self.pool.open()
        async with self.pool.connection() as conn:
            await conn.set_autocommit(True)
            await AsyncPostgresSaver(conn).setup()

    async def close(self):
        """Cerrar recursos (llamar al apagar la app)"""
        if self._pool:
            await self._pool.close()
            self._pool = None

    @property
    def model(self) -> BaseChatModel:
        """Obtener modelo de chat configurado"""
        if self._model is None:
            if self.config.provider == "openai":
                self._model = ChatOpenAI(
                    model_name=self.config.model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    openai_api_key=self.config.api_key,
                    streaming=True
                )
            elif self.config.provider == "azure-openai":
                self._model = AzureChatOpenAI(
                    azure_deployment=self.config.model,
                    azure_endpoint=self.config.endpoint,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    openai_api_key=self.config.api_key,
                    streaming=True,
                    api_version="2024-10-21"
                )
        
        return self._model
    
    async def delete_context(self, thread_id: str):
        """Eliminar contexto guardado (si aplica)"""
        async with self.pool.connection() as conn:
            checkpointer = AsyncPostgresSaver(conn)
            await checkpointer.adelete_thread(thread_id=thread_id)
    
    async def streaming_response(self, msg: HumanMessage, chat_id: int):
        """
        Procesar respuesta del LLM en streaming (función background)
        
        Args:
            chat_id: ID del chat
        """
        try:
            logger.info(f"[{self.config.provider}] Iniciando streaming para chat {chat_id}")

            async with self.pool.connection() as conn:
                checkpointer = AsyncPostgresSaver(conn) # Usar este checkpointer en el agente

                # 2. Crear agente
                agent = create_agent(
                    model=self.model,
                    tools=tools,
                    prompt=self.prompt,
                    checkpointer=checkpointer,
                )
            
                # 3. Notificar inicio de respuesta del asistente
                await connection_manager.send_to_chat(
                    chat_id, {"type": WebsocketMessageType.ASSISTANT_RESPONSE_START.value}
                )
            
                # 4. Generar respuesta streaming
                full_response = AIMessageChunk(content="")
                config = {'configurable': {'thread_id': chat_id}}

                async for token, meta in agent.astream({"messages": [msg]}, config=config, stream_mode="messages"):

                    token: AIMessageChunk  # type hint

                    if token.type == WebsocketMessageType.AICHUNK.value and token.content:
                        # Enviar chunk via WebSocket
                        await connection_manager.send_to_chat(chat_id, token.model_dump())

                        full_response += token

                # 5. Guardar respuesta completa en BD
                await add_message(chat_id=chat_id, msg=AIMessage(content=full_response.content))

                # 6. Notificar finalización
                await connection_manager.send_to_chat(
                    chat_id,
                    {
                        "type": WebsocketMessageType.ASSISTANT_RESPONSE_COMPLETE.value,
                        "data": {
                            "id": full_response.id,
                            "content": full_response.content
                        }
                    }
                )
                
                logger.info(f"[{self.config.provider}] Streaming completado para chat {chat_id}")
            
        except Exception as e:
            logger.error(f"[{self.config.provider}] Error en streaming para chat {chat_id}: {e}")
            
            # Notificar error via WebSocket
            await connection_manager.send_to_chat(
                chat_id,
                {
                    "type": WebsocketMessageType.ASSISTANT_RESPONSE_ERROR.value,
                    "data": {
                        "error": str(e),
                        "status": "error"
                    }
                }
            )

llm_manager = LLM()