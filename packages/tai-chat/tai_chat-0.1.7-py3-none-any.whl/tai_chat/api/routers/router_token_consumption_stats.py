from fastapi import APIRouter, Depends, Query
from typing import Optional, List, Literal
from tai_alphi import Alphi
from datetime import datetime

from ..database import *
from ..resources import (
    APIResponse, PaginatedResponse
)


logger = Alphi.get_logger_by_name("tai-chatbot")

token_consumption_stats_router = APIRouter(
    prefix="/token-consumption-stats",
    tags=["TokenConsumptionStats"]
)

@token_consumption_stats_router.get("", 
    response_model=APIResponse[List[TokenConsumptionStatsRead]],
    response_description="Lista de registros de token_consumption_stats obtenido exitosamente",
    operation_id="token_consumption_stats_find_many",
    summary="Busca varios registros en la tabla token_consumption_stats",
    responses={
        200: {
            "description": "Lista de registros de token_consumption_stats obtenido exitosamente",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/APIResponse_List_TokenConsumptionStatsRead__"
                    }
                }
            },
            "links": {
                "self": {
                    "operationId": "token_consumption_stats_find_many",
                    "description": "Enlace a la consulta actual con los mismos filtros",
                    "parameters": {
                        "username": "$request.query.username",
                        "date": "$request.query.date",
                        "total_prompt_tokens": "$request.query.total_prompt_tokens",
                        "total_completion_tokens": "$request.query.total_completion_tokens",
                        "total_tokens": "$request.query.total_tokens",
                        "total_cost_usd": "$request.query.total_cost_usd",
                        "chat_count": "$request.query.chat_count",
                        "most_used_model": "$request.query.most_used_model",
                        "most_used_provider": "$request.query.most_used_provider",
                        "limit": "$request.query.limit",
                        "offset": "$request.query.offset",
                        "order_by": "$request.query.order_by",
                        "order": "$request.query.order",
                        "includes": "$request.query.includes"
                    }
                },
                "item": {
                    "operationId": "token_consumption_stats_find",
                    "description": "Enlace para acceder a un elemento específico",
                    "parameters": {
                        "includes": "$request.query.includes"
                    }
                },
                "create": {
                    "operationId": "token_consumption_stats_create",
                    "description": "Enlace para crear un nuevo TokenConsumptionStats"
                },
                "count": {
                    "operationId": "token_consumption_stats_count",
                    "description": "Enlace para obtener el conteo total con los mismos filtros",
                    "parameters": {
                        "username": "$request.query.username",
                        "date": "$request.query.date",
                        "total_prompt_tokens": "$request.query.total_prompt_tokens",
                        "total_completion_tokens": "$request.query.total_completion_tokens",
                        "total_tokens": "$request.query.total_tokens",
                        "total_cost_usd": "$request.query.total_cost_usd",
                        "chat_count": "$request.query.chat_count",
                        "most_used_model": "$request.query.most_used_model",
                        "most_used_provider": "$request.query.most_used_provider",
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
async def token_consumption_stats_find_many(
    limit: Optional[int] = Query(None, description="Número de registros a retornar. Valores positivos toman los n primeros registros, valores negativos toman los n últimos registros (requiere order_by)", gt=0),
    order_by: List[str] = Query(None, description="Lista de nombres de columnas para ordenar los resultados.⚠️ **IMPORTANTE**: los nombres de columnas deben existir, si no serán omitidas. Requerido cuando limit es negativo"),
    order: Optional[Literal["ASC", "DESC"]] = Query("ASC", description="Dirección de ordenamiento: 'ASC' para ascendente (por defecto), 'DESC' para descendente. Solo aplica si order_by está definido", regex="^(ASC|DESC)$"),
    offset: Optional[int] = Query(None, description="Número de registros a omitir desde el inicio. Útil para paginación. Debe ser un valor no negativo", ge=0),
    username: Optional[str] = Query(None, description='Filtrar por username. ⚠️ **IMPORTANTE**: utiliza "%username%" para hacer consultas ILIKE. Campo username de la tabla token_consumption_stats', min_length=1, max_length=255),
    min_date: Optional[datetime] = Query(None, description="Fecha y hora mínima para date (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_date: Optional[datetime] = Query(None, description="Fecha y hora máxima para date (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    total_prompt_tokens: Optional[int] = Query(None, description="Filtrar por valor exacto de total_prompt_tokens. Campo total_prompt_tokens de la tabla token_consumption_stats"),
    min_total_prompt_tokens: Optional[int] = Query(None, description="Valor mínimo para total_prompt_tokens (incluido)"),
    max_total_prompt_tokens: Optional[int] = Query(None, description="Valor máximo para total_prompt_tokens (incluido)"),
    total_completion_tokens: Optional[int] = Query(None, description="Filtrar por valor exacto de total_completion_tokens. Campo total_completion_tokens de la tabla token_consumption_stats"),
    min_total_completion_tokens: Optional[int] = Query(None, description="Valor mínimo para total_completion_tokens (incluido)"),
    max_total_completion_tokens: Optional[int] = Query(None, description="Valor máximo para total_completion_tokens (incluido)"),
    total_tokens: Optional[int] = Query(None, description="Filtrar por valor exacto de total_tokens. Campo total_tokens de la tabla token_consumption_stats"),
    min_total_tokens: Optional[int] = Query(None, description="Valor mínimo para total_tokens (incluido)"),
    max_total_tokens: Optional[int] = Query(None, description="Valor máximo para total_tokens (incluido)"),
    min_total_cost_usd: Optional[float] = Query(None, description="Valor mínimo para total_cost_usd (incluido)"),
    max_total_cost_usd: Optional[float] = Query(None, description="Valor máximo para total_cost_usd (incluido)"),
    chat_count: Optional[int] = Query(None, description="Filtrar por valor exacto de chat_count. Campo chat_count de la tabla token_consumption_stats"),
    min_chat_count: Optional[int] = Query(None, description="Valor mínimo para chat_count (incluido)"),
    max_chat_count: Optional[int] = Query(None, description="Valor máximo para chat_count (incluido)"),
    most_used_model: Optional[str] = Query(None, description='Filtrar por most_used_model. ⚠️ **IMPORTANTE**: utiliza "%most_used_model%" para hacer consultas ILIKE. Campo most_used_model de la tabla token_consumption_stats', min_length=1, max_length=255),
    most_used_provider: Optional[str] = Query(None, description='Filtrar por most_used_provider. ⚠️ **IMPORTANTE**: utiliza "%most_used_provider%" para hacer consultas ILIKE. Campo most_used_provider de la tabla token_consumption_stats', min_length=1, max_length=255),
    includes: List[str] = Query(None, description="Lista de relaciones a incluir en la respuesta para obtener datos relacionados. Especifica los nombres de las relaciones que deseas expandir"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[List[TokenConsumptionStatsRead]]:
    """
    ## Resumen
    Obtiene una lista de `token_consumption_statss` con filtros opcionales y soporte para paginación.
    
    Este endpoint permite realizar búsquedas flexibles aplicando filtros opcionales
    por cualquiera de los campos disponibles, con soporte completo para paginación
    mediante los parámetros limit y offset.

    ## Resultado
    En `APIResponse.data`, retorna un listado de objetos donde cada uno representa un registro de la tabla `token_consumption_stats` que incluye todos sus atributos

    ## Datos
    Para cada registro en `data` se incluye:
    - **username** (str): Campo username de la tabla token_consumption_stats
    - **date** (datetime): Campo date de la tabla token_consumption_stats
    - **total_prompt_tokens** (int): Campo total_prompt_tokens de la tabla token_consumption_stats
    - **total_completion_tokens** (int): Campo total_completion_tokens de la tabla token_consumption_stats
    - **total_tokens** (int): Campo total_tokens de la tabla token_consumption_stats
    - **total_cost_usd** (float, opcional): Campo total_cost_usd de la tabla token_consumption_stats
    - **chat_count** (int): Campo chat_count de la tabla token_consumption_stats
    - **most_used_model** (str): Campo most_used_model de la tabla token_consumption_stats
    - **most_used_provider** (str): Campo most_used_provider de la tabla token_consumption_stats
    
    ## Parámetros de Filtrado
    
    Todos los parámetros de filtrado son opcionales y se pueden combinar:
    - **username**: Filtrar por username. ⚠️ **IMPORTANTE**: utiliza "%username%" para hacer consultas ILIKE.
    - **min_date**: Filtrar por valor mínimo de date (incluído el valor del filtro)
    - **max_date**: Filtrar por valor máximo de date (incluído el valor del filtro)
    - **total_prompt_tokens**: Filtrar por total_prompt_tokens
    - **min_total_prompt_tokens**: Filtrar por fecha mínima (incluída)
    - **max_total_prompt_tokens**: Filtrar por fecha máxima (incluída)
    - **total_completion_tokens**: Filtrar por total_completion_tokens
    - **min_total_completion_tokens**: Filtrar por fecha mínima (incluída)
    - **max_total_completion_tokens**: Filtrar por fecha máxima (incluída)
    - **total_tokens**: Filtrar por total_tokens
    - **min_total_tokens**: Filtrar por fecha mínima (incluída)
    - **max_total_tokens**: Filtrar por fecha máxima (incluída)
    - **min_total_cost_usd**: Filtrar por valor mínimo de total_cost_usd (incluído el valor del filtro)
    - **max_total_cost_usd**: Filtrar por valor máximo de total_cost_usd (incluído el valor del filtro)
    - **chat_count**: Filtrar por chat_count
    - **min_chat_count**: Filtrar por fecha mínima (incluída)
    - **max_chat_count**: Filtrar por fecha máxima (incluída)
    - **most_used_model**: Filtrar por most_used_model. ⚠️ **IMPORTANTE**: utiliza "%most_used_model%" para hacer consultas ILIKE.
    - **most_used_provider**: Filtrar por most_used_provider. ⚠️ **IMPORTANTE**: utiliza "%most_used_provider%" para hacer consultas ILIKE.

    
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
    result = await api.token_consumption_stats.find_many(
        limit=limit,
        offset=offset,
        order_by=order_by,
        order=order,
        username=username,
        min_date=min_date,
        max_date=max_date,
        total_prompt_tokens=total_prompt_tokens,
        min_total_prompt_tokens=min_total_prompt_tokens,
        max_total_prompt_tokens=max_total_prompt_tokens,
        total_completion_tokens=total_completion_tokens,
        min_total_completion_tokens=min_total_completion_tokens,
        max_total_completion_tokens=max_total_completion_tokens,
        total_tokens=total_tokens,
        min_total_tokens=min_total_tokens,
        max_total_tokens=max_total_tokens,
        min_total_cost_usd=min_total_cost_usd,
        max_total_cost_usd=max_total_cost_usd,
        chat_count=chat_count,
        min_chat_count=min_chat_count,
        max_chat_count=max_chat_count,
        most_used_model=most_used_model,
        most_used_provider=most_used_provider,
        includes=includes
    )
    
    # Obtener el total para metadatos de paginación si es necesario
    total = None
    if limit is not None or offset is not None:
        try:
            total = await api.token_consumption_stats.count(
                username=username,
                min_date=min_date,
                max_date=max_date,
                total_prompt_tokens=total_prompt_tokens,
                min_total_prompt_tokens=min_total_prompt_tokens,
                max_total_prompt_tokens=max_total_prompt_tokens,
                total_completion_tokens=total_completion_tokens,
                min_total_completion_tokens=min_total_completion_tokens,
                max_total_completion_tokens=max_total_completion_tokens,
                total_tokens=total_tokens,
                min_total_tokens=min_total_tokens,
                max_total_tokens=max_total_tokens,
                min_total_cost_usd=min_total_cost_usd,
                max_total_cost_usd=max_total_cost_usd,
                chat_count=chat_count,
                min_chat_count=min_chat_count,
                max_chat_count=max_chat_count,
                most_used_model=most_used_model,
                most_used_provider=most_used_provider,
            )
        except Exception as e:
            logger.warning(f"No se pudo obtener el total de registros: {str(e)}")
    
    return PaginatedResponse.success_paginated(
        data=result,
        total=total,
        limit=limit,
        offset=offset,
        message=f"TokenConsumptionStatss obtenidos exitosamente"
    )

