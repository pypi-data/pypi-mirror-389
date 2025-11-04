from fastapi import APIRouter, Depends, Query
from typing import Optional, List, Literal
from tai_alphi import Alphi
from datetime import datetime

from ..database import *
from ..resources import (
    APIResponse, PaginatedResponse
)


logger = Alphi.get_logger_by_name("tai-chatbot")

user_stats_router = APIRouter(
    prefix="/user-stats",
    tags=["UserStats"]
)

@user_stats_router.get("", 
    response_model=APIResponse[List[UserStatsRead]],
    response_description="Lista de registros de user_stats obtenido exitosamente",
    operation_id="user_stats_find_many",
    summary="Busca varios registros en la tabla user_stats",
    responses={
        200: {
            "description": "Lista de registros de user_stats obtenido exitosamente",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/APIResponse_List_UserStatsRead__"
                    }
                }
            },
            "links": {
                "self": {
                    "operationId": "user_stats_find_many",
                    "description": "Enlace a la consulta actual con los mismos filtros",
                    "parameters": {
                        "username": "$request.query.username",
                        "email": "$request.query.email",
                        "total_chats": "$request.query.total_chats",
                        "active_chats": "$request.query.active_chats",
                        "total_messages": "$request.query.total_messages",
                        "created_at": "$request.query.created_at",
                        "last_activity": "$request.query.last_activity",
                        "limit": "$request.query.limit",
                        "offset": "$request.query.offset",
                        "order_by": "$request.query.order_by",
                        "order": "$request.query.order",
                        "includes": "$request.query.includes"
                    }
                },
                "item": {
                    "operationId": "user_stats_find",
                    "description": "Enlace para acceder a un elemento específico",
                    "parameters": {
                        "includes": "$request.query.includes"
                    }
                },
                "create": {
                    "operationId": "user_stats_create",
                    "description": "Enlace para crear un nuevo UserStats"
                },
                "count": {
                    "operationId": "user_stats_count",
                    "description": "Enlace para obtener el conteo total con los mismos filtros",
                    "parameters": {
                        "username": "$request.query.username",
                        "email": "$request.query.email",
                        "total_chats": "$request.query.total_chats",
                        "active_chats": "$request.query.active_chats",
                        "total_messages": "$request.query.total_messages",
                        "created_at": "$request.query.created_at",
                        "last_activity": "$request.query.last_activity",
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
async def user_stats_find_many(
    limit: Optional[int] = Query(None, description="Número de registros a retornar. Valores positivos toman los n primeros registros, valores negativos toman los n últimos registros (requiere order_by)", gt=0),
    order_by: List[str] = Query(None, description="Lista de nombres de columnas para ordenar los resultados.⚠️ **IMPORTANTE**: los nombres de columnas deben existir, si no serán omitidas. Requerido cuando limit es negativo"),
    order: Optional[Literal["ASC", "DESC"]] = Query("ASC", description="Dirección de ordenamiento: 'ASC' para ascendente (por defecto), 'DESC' para descendente. Solo aplica si order_by está definido", regex="^(ASC|DESC)$"),
    offset: Optional[int] = Query(None, description="Número de registros a omitir desde el inicio. Útil para paginación. Debe ser un valor no negativo", ge=0),
    username: Optional[str] = Query(None, description='Filtrar por username. ⚠️ **IMPORTANTE**: utiliza "%username%" para hacer consultas ILIKE. Campo username de la tabla user_stats', min_length=1, max_length=255),
    email: Optional[str] = Query(None, description='Filtrar por email. ⚠️ **IMPORTANTE**: utiliza "%email%" para hacer consultas ILIKE. Campo email de la tabla user_stats', min_length=1, max_length=255),
    total_chats: Optional[int] = Query(None, description="Filtrar por valor exacto de total_chats. Campo total_chats de la tabla user_stats"),
    min_total_chats: Optional[int] = Query(None, description="Valor mínimo para total_chats (incluido)"),
    max_total_chats: Optional[int] = Query(None, description="Valor máximo para total_chats (incluido)"),
    active_chats: Optional[int] = Query(None, description="Filtrar por valor exacto de active_chats. Campo active_chats de la tabla user_stats"),
    min_active_chats: Optional[int] = Query(None, description="Valor mínimo para active_chats (incluido)"),
    max_active_chats: Optional[int] = Query(None, description="Valor máximo para active_chats (incluido)"),
    total_messages: Optional[int] = Query(None, description="Filtrar por valor exacto de total_messages. Campo total_messages de la tabla user_stats"),
    min_total_messages: Optional[int] = Query(None, description="Valor mínimo para total_messages (incluido)"),
    max_total_messages: Optional[int] = Query(None, description="Valor máximo para total_messages (incluido)"),
    min_created_at: Optional[datetime] = Query(None, description="Fecha y hora mínima para created_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_created_at: Optional[datetime] = Query(None, description="Fecha y hora máxima para created_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    min_last_activity: Optional[datetime] = Query(None, description="Fecha y hora mínima para last_activity (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_last_activity: Optional[datetime] = Query(None, description="Fecha y hora máxima para last_activity (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    includes: List[str] = Query(None, description="Lista de relaciones a incluir en la respuesta para obtener datos relacionados. Especifica los nombres de las relaciones que deseas expandir"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[List[UserStatsRead]]:
    """
    ## Resumen
    Obtiene una lista de `user_statss` con filtros opcionales y soporte para paginación.
    
    Este endpoint permite realizar búsquedas flexibles aplicando filtros opcionales
    por cualquiera de los campos disponibles, con soporte completo para paginación
    mediante los parámetros limit y offset.

    ## Resultado
    En `APIResponse.data`, retorna un listado de objetos donde cada uno representa un registro de la tabla `user_stats` que incluye todos sus atributos

    ## Datos
    Para cada registro en `data` se incluye:
    - **username** (str): Campo username de la tabla user_stats
    - **email** (str): Campo email de la tabla user_stats
    - **total_chats** (int): Campo total_chats de la tabla user_stats
    - **active_chats** (int): Campo active_chats de la tabla user_stats
    - **total_messages** (int): Campo total_messages de la tabla user_stats
    - **created_at** (datetime): Campo created_at de la tabla user_stats
    - **last_activity** (datetime, opcional): Campo last_activity de la tabla user_stats
    
    ## Parámetros de Filtrado
    
    Todos los parámetros de filtrado son opcionales y se pueden combinar:
    - **username**: Filtrar por username. ⚠️ **IMPORTANTE**: utiliza "%username%" para hacer consultas ILIKE.
    - **email**: Filtrar por email. ⚠️ **IMPORTANTE**: utiliza "%email%" para hacer consultas ILIKE.
    - **total_chats**: Filtrar por total_chats
    - **min_total_chats**: Filtrar por fecha mínima (incluída)
    - **max_total_chats**: Filtrar por fecha máxima (incluída)
    - **active_chats**: Filtrar por active_chats
    - **min_active_chats**: Filtrar por fecha mínima (incluída)
    - **max_active_chats**: Filtrar por fecha máxima (incluída)
    - **total_messages**: Filtrar por total_messages
    - **min_total_messages**: Filtrar por fecha mínima (incluída)
    - **max_total_messages**: Filtrar por fecha máxima (incluída)
    - **min_created_at**: Filtrar por valor mínimo de created_at (incluído el valor del filtro)
    - **max_created_at**: Filtrar por valor máximo de created_at (incluído el valor del filtro)
    - **min_last_activity**: Filtrar por valor mínimo de last_activity (incluído el valor del filtro)
    - **max_last_activity**: Filtrar por valor máximo de last_activity (incluído el valor del filtro)

    
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
    result = await api.user_stats.find_many(
        limit=limit,
        offset=offset,
        order_by=order_by,
        order=order,
        username=username,
        email=email,
        total_chats=total_chats,
        min_total_chats=min_total_chats,
        max_total_chats=max_total_chats,
        active_chats=active_chats,
        min_active_chats=min_active_chats,
        max_active_chats=max_active_chats,
        total_messages=total_messages,
        min_total_messages=min_total_messages,
        max_total_messages=max_total_messages,
        min_created_at=min_created_at,
        max_created_at=max_created_at,
        min_last_activity=min_last_activity,
        max_last_activity=max_last_activity,
        includes=includes
    )
    
    # Obtener el total para metadatos de paginación si es necesario
    total = None
    if limit is not None or offset is not None:
        try:
            total = await api.user_stats.count(
                username=username,
                email=email,
                total_chats=total_chats,
                min_total_chats=min_total_chats,
                max_total_chats=max_total_chats,
                active_chats=active_chats,
                min_active_chats=min_active_chats,
                max_active_chats=max_active_chats,
                total_messages=total_messages,
                min_total_messages=min_total_messages,
                max_total_messages=max_total_messages,
                min_created_at=min_created_at,
                max_created_at=max_created_at,
                min_last_activity=min_last_activity,
                max_last_activity=max_last_activity,
            )
        except Exception as e:
            logger.warning(f"No se pudo obtener el total de registros: {str(e)}")
    
    return PaginatedResponse.success_paginated(
        data=result,
        total=total,
        limit=limit,
        offset=offset,
        message=f"UserStatss obtenidos exitosamente"
    )

