from fastapi import APIRouter, Depends, Query
from typing import Optional, List, Literal
from tai_alphi import Alphi
from datetime import datetime

from ..database import *
from ..resources import (
    APIResponse, PaginatedResponse
)

logger = Alphi.get_logger_by_name("tai-chatbot")

chat_activity_router = APIRouter(
    prefix="/chat-activity",
    tags=["ChatActivity"]
)

@chat_activity_router.get("", 
    response_model=APIResponse[List[ChatActivityRead]],
    response_description="Lista de registros de chat_activity obtenido exitosamente",
    operation_id="chat_activity_find_many",
    summary="Busca varios registros en la tabla chat_activity",
    responses={
        200: {
            "description": "Lista de registros de chat_activity obtenido exitosamente",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/APIResponse_List_ChatActivityRead__"
                    }
                }
            },
            "links": {
                "self": {
                    "operationId": "chat_activity_find_many",
                    "description": "Enlace a la consulta actual con los mismos filtros",
                    "parameters": {
                        "chat_id": "$request.query.chat_id",
                        "chat_title": "$request.query.chat_title",
                        "username": "$request.query.username",
                        "message_count": "$request.query.message_count",
                        "last_message_timestamp": "$request.query.last_message_timestamp",
                        "total_tokens_consumed": "$request.query.total_tokens_consumed",
                        "is_active": "$request.query.is_active",
                        "limit": "$request.query.limit",
                        "offset": "$request.query.offset",
                        "order_by": "$request.query.order_by",
                        "order": "$request.query.order",
                        "includes": "$request.query.includes"
                    }
                },
                "item": {
                    "operationId": "chat_activity_find",
                    "description": "Enlace para acceder a un elemento específico",
                    "parameters": {
                        "includes": "$request.query.includes"
                    }
                },
                "create": {
                    "operationId": "chat_activity_create",
                    "description": "Enlace para crear un nuevo ChatActivity"
                },
                "count": {
                    "operationId": "chat_activity_count",
                    "description": "Enlace para obtener el conteo total con los mismos filtros",
                    "parameters": {
                        "chat_id": "$request.query.chat_id",
                        "chat_title": "$request.query.chat_title",
                        "username": "$request.query.username",
                        "message_count": "$request.query.message_count",
                        "last_message_timestamp": "$request.query.last_message_timestamp",
                        "total_tokens_consumed": "$request.query.total_tokens_consumed",
                        "is_active": "$request.query.is_active",
                    }
                }}
        },
        422: {
            "description": "Error de validación en parámetros",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "Error de validación",
                        "errors": [
                            {
                                "code": "VALIDATION_ERROR",
                                "message": "El límite no puede ser negativo",
                                "field": "limit",
                                "details": None
                            }
                        ],
                        "meta": None
                    }
                }
            }
        },
        500: {
            "description": "Error interno del servidor",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "Error interno del servidor",
                        "errors": [
                            {
                                "code": "DATABASE_ERROR",
                                "message": "Error en la base de datos",
                                "field": None,
                                "details": None
                            }
                        ],
                        "meta": None
                    }
                }
            }
        }
    }
)
async def chat_activity_find_many(
    limit: Optional[int] = Query(None, description="Número de registros a retornar. Valores positivos toman los n primeros registros, valores negativos toman los n últimos registros (requiere order_by)", gt=0),
    order_by: List[str] = Query(None, description="Lista de nombres de columnas para ordenar los resultados.⚠️ **IMPORTANTE**: los nombres de columnas deben existir, si no serán omitidas. Requerido cuando limit es negativo"),
    order: Optional[Literal["ASC", "DESC"]] = Query("ASC", description="Dirección de ordenamiento: 'ASC' para ascendente (por defecto), 'DESC' para descendente. Solo aplica si order_by está definido", regex="^(ASC|DESC)$"),
    offset: Optional[int] = Query(None, description="Número de registros a omitir desde el inicio. Útil para paginación. Debe ser un valor no negativo", ge=0),
    chat_id: Optional[str] = Query(None, description='Filtrar por chat_id. ⚠️ **IMPORTANTE**: utiliza "%chat_id%" para hacer consultas ILIKE. Campo chat_id de la tabla chat_activity', min_length=1, max_length=255),
    chat_title: Optional[str] = Query(None, description='Filtrar por chat_title. ⚠️ **IMPORTANTE**: utiliza "%chat_title%" para hacer consultas ILIKE. Campo chat_title de la tabla chat_activity', min_length=1, max_length=255),
    username: Optional[str] = Query(None, description='Filtrar por username. ⚠️ **IMPORTANTE**: utiliza "%username%" para hacer consultas ILIKE. Campo username de la tabla chat_activity', min_length=1, max_length=255),
    message_count: Optional[int] = Query(None, description="Filtrar por valor exacto de message_count. Campo message_count de la tabla chat_activity"),
    min_message_count: Optional[int] = Query(None, description="Valor mínimo para message_count (incluido)"),
    max_message_count: Optional[int] = Query(None, description="Valor máximo para message_count (incluido)"),
    min_last_message_timestamp: Optional[datetime] = Query(None, description="Fecha y hora mínima para last_message_timestamp (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_last_message_timestamp: Optional[datetime] = Query(None, description="Fecha y hora máxima para last_message_timestamp (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    total_tokens_consumed: Optional[int] = Query(None, description="Filtrar por valor exacto de total_tokens_consumed. Campo total_tokens_consumed de la tabla chat_activity"),
    min_total_tokens_consumed: Optional[int] = Query(None, description="Valor mínimo para total_tokens_consumed (incluido)"),
    max_total_tokens_consumed: Optional[int] = Query(None, description="Valor máximo para total_tokens_consumed (incluido)"),
    is_active: Optional[bool] = Query(None, description="Filtrar por is_active (verdadero/falso). Campo is_active de la tabla chat_activity"),
    includes: List[str] = Query(None, description="Lista de relaciones a incluir en la respuesta para obtener datos relacionados. Especifica los nombres de las relaciones que deseas expandir"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[List[ChatActivityRead]]:
    """
    ## Resumen
    Obtiene una lista de `chat_activitys` con filtros opcionales y soporte para paginación.
    
    Este endpoint permite realizar búsquedas flexibles aplicando filtros opcionales
    por cualquiera de los campos disponibles, con soporte completo para paginación
    mediante los parámetros limit y offset.

    ## Resultado
    En `APIResponse.data`, retorna un listado de objetos donde cada uno representa un registro de la tabla `chat_activity` que incluye todos sus atributos

    ## Datos
    Para cada registro en `data` se incluye:
    - **chat_id** (str): Campo chat_id de la tabla chat_activity
    - **chat_title** (str): Campo chat_title de la tabla chat_activity
    - **username** (str): Campo username de la tabla chat_activity
    - **message_count** (int): Campo message_count de la tabla chat_activity
    - **last_message_timestamp** (datetime): Campo last_message_timestamp de la tabla chat_activity
    - **total_tokens_consumed** (int): Campo total_tokens_consumed de la tabla chat_activity
    - **is_active** (bool): Campo is_active de la tabla chat_activity
    
    ## Parámetros de Filtrado
    
    Todos los parámetros de filtrado son opcionales y se pueden combinar:
    - **chat_id**: Filtrar por chat_id. ⚠️ **IMPORTANTE**: utiliza "%chat_id%" para hacer consultas ILIKE.
    - **chat_title**: Filtrar por chat_title. ⚠️ **IMPORTANTE**: utiliza "%chat_title%" para hacer consultas ILIKE.
    - **username**: Filtrar por username. ⚠️ **IMPORTANTE**: utiliza "%username%" para hacer consultas ILIKE.
    - **message_count**: Filtrar por message_count
    - **min_message_count**: Filtrar por fecha mínima (incluída)
    - **max_message_count**: Filtrar por fecha máxima (incluída)
    - **min_last_message_timestamp**: Filtrar por valor mínimo de last_message_timestamp (incluído el valor del filtro)
    - **max_last_message_timestamp**: Filtrar por valor máximo de last_message_timestamp (incluído el valor del filtro)
    - **total_tokens_consumed**: Filtrar por total_tokens_consumed
    - **min_total_tokens_consumed**: Filtrar por fecha mínima (incluída)
    - **max_total_tokens_consumed**: Filtrar por fecha máxima (incluída)
    - **is_active**: Filtrar por is_active (verdadero/falso)

    
    ## Parámetros de Paginación
    
    - **limit**: Número máximo de registros a retornar. Solo admite valores positivos. Si no se especifica, retorna todos los registros que coincidan con los filtros.
    - **order_by**: Lista de nombres de columnas para ordenar los resultados.⚠️ **IMPORTANTE**: los nombres de columnas deben existir, si no serán omitidas.
    - **order**: Dirección de ordenamiento: 'ASC' para ascendente (por defecto), 'DESC' para descendente. Solo aplica si order_by está definido.
    - **offset**: Número de registros a omitir desde el inicio. Solo admite valores positivos. Si no se especifica, inicia desde el primer registro.
    
    ## Consulta combinada (recomendado para pocos registros)
    ⚠️ **IMPORTANTE**: Usa siempre el parámetro `includes` para cargar relaciones en una sola consulta y evitar múltiples llamadas al API.
    
    ⚠️ **WARNING**: Si la relación incluida tiene muchos registros relacionados, la respuesta puede ser muy grande y lenta. Mejor consultar su endpoint directamente con filtros.
    
    El parametro `includes` permite cargar relaciones asociadas a los registros.
    """
    result = await api.chat_activity.find_many(
        limit=limit,
        offset=offset,
        order_by=order_by,
        order=order,
        chat_id=chat_id,
        chat_title=chat_title,
        username=username,
        message_count=message_count,
        min_message_count=min_message_count,
        max_message_count=max_message_count,
        min_last_message_timestamp=min_last_message_timestamp,
        max_last_message_timestamp=max_last_message_timestamp,
        total_tokens_consumed=total_tokens_consumed,
        min_total_tokens_consumed=min_total_tokens_consumed,
        max_total_tokens_consumed=max_total_tokens_consumed,
        is_active=is_active,
        includes=includes
    )
    
    # Obtener el total para metadatos de paginación si es necesario
    total = None
    if limit is not None or offset is not None:
        try:
            total = await api.chat_activity.count(
                chat_id=chat_id,
                chat_title=chat_title,
                username=username,
                message_count=message_count,
                min_message_count=min_message_count,
                max_message_count=max_message_count,
                min_last_message_timestamp=min_last_message_timestamp,
                max_last_message_timestamp=max_last_message_timestamp,
                total_tokens_consumed=total_tokens_consumed,
                min_total_tokens_consumed=min_total_tokens_consumed,
                max_total_tokens_consumed=max_total_tokens_consumed,
                is_active=is_active,
            )
        except Exception as e:
            logger.warning(f"No se pudo obtener el total de registros: {str(e)}")
    
    return PaginatedResponse.success_paginated(
        data=result,
        total=total,
        limit=limit,
        offset=offset,
        message=f"ChatActivitys obtenidos exitosamente"
    )

