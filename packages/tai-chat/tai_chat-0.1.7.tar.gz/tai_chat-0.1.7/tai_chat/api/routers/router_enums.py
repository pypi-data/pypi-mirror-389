from fastapi import APIRouter, Depends
from typing import List
from ..database import *
from ..resources import APIResponse

enumerations_router = APIRouter(
    prefix="/enums",
    tags=["Enumeraciones"]
)

@enumerations_router.get("/message-role", tags=["Enumeraciones"], response_model=APIResponse[List[str]])
async def get_message_role_enumeration(
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[List[str]]:
    """
    Obtiene los valores de la enumeración message_role.
    """
    values = api.message_role.find_many()
    
    return APIResponse.success(
        data=values,
        message="Enumeración message_role obtenida exitosamente"
    )

