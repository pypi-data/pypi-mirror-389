from fastapi import APIRouter
from .router_usuario import usuario_router
from .router_chat import chat_router
from .router_mensaje import mensaje_router
from .router_token_usage import token_usage_router
from .router_user_stats import user_stats_router
from .router_token_consumption_stats import token_consumption_stats_router
from .router_chat_activity import chat_activity_router
from .router_enums import enumerations_router
from .router_stream import streaming_router

main_router = APIRouter()

main_router.include_router(usuario_router)
main_router.include_router(chat_router)
main_router.include_router(mensaje_router)
main_router.include_router(token_usage_router)
main_router.include_router(user_stats_router)
main_router.include_router(token_consumption_stats_router)
main_router.include_router(chat_activity_router)
main_router.include_router(enumerations_router)

__all__ = [
    "main_router",
    "streaming_router"
]
