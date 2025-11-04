from fastapi import APIRouter, Depends, Query, Path, Body
from typing import Optional, List, Literal
from tai_alphi import Alphi
from datetime import datetime

from ..database import *
from ..resources import (
    APIResponse, PaginatedResponse, RecordNotFoundException,
    ValidationException
)


logger = Alphi.get_logger_by_name("tai-chatbot")

token_usage_router = APIRouter(
    prefix="/token-usage",
    tags=["TokenUsage"]
)

@token_usage_router.get("", 
    response_model=APIResponse[List[TokenUsageRead]],
    response_description="Lista de registros de token_usage obtenido exitosamente",
    operation_id="token_usage_find_many",
    summary="Busca varios registros en la tabla token_usage",
    responses={
        200: {
            "description": "Lista de registros de token_usage obtenido exitosamente",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/APIResponse_List_TokenUsageRead__"
                    }
                }
            },
            "links": {
                "self": {
                    "operationId": "token_usage_find_many",
                    "description": "Enlace a la consulta actual con los mismos filtros",
                    "parameters": {
                        "prompt_tokens": "$request.query.prompt_tokens",
                        "completion_tokens": "$request.query.completion_tokens",
                        "total_tokens": "$request.query.total_tokens",
                        "model_name": "$request.query.model_name",
                        "provider": "$request.query.provider",
                        "cost_usd": "$request.query.cost_usd",
                        "timestamp": "$request.query.timestamp",
                        "message_id": "$request.query.message_id",
                        "limit": "$request.query.limit",
                        "offset": "$request.query.offset",
                        "order_by": "$request.query.order_by",
                        "order": "$request.query.order",
                        "includes": "$request.query.includes"
                    }
                },
                "item": {
                    "operationId": "token_usage_find",
                    "description": "Enlace para acceder a un elemento específico",
                    "parameters": {
                        "id": "$response.body#/data/**/id",
                        "includes": "$request.query.includes"
                    }
                },
                "create": {
                    "operationId": "token_usage_create",
                    "description": "Enlace para crear un nuevo TokenUsage"
                },
                "count": {
                    "operationId": "token_usage_count",
                    "description": "Enlace para obtener el conteo total con los mismos filtros",
                    "parameters": {
                        "prompt_tokens": "$request.query.prompt_tokens",
                        "completion_tokens": "$request.query.completion_tokens",
                        "total_tokens": "$request.query.total_tokens",
                        "model_name": "$request.query.model_name",
                        "provider": "$request.query.provider",
                        "cost_usd": "$request.query.cost_usd",
                        "timestamp": "$request.query.timestamp",
                        "message_id": "$request.query.message_id",
                    }
                },
            "message": {
            "operationId": "mensaje_find",
                    "description": "Enlace al Mensaje relacionado",
                    "parameters": {
                        "id": "$response.body#/data/**/message_id",
                        "includes": "$request.query.includes"
                    }
            }
            }
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
async def token_usage_find_many(
    limit: Optional[int] = Query(None, description="Número de registros a retornar. Valores positivos toman los n primeros registros, valores negativos toman los n últimos registros (requiere order_by)", gt=0),
    order_by: List[str] = Query(None, description="Lista de nombres de columnas para ordenar los resultados.⚠️ **IMPORTANTE**: los nombres de columnas deben existir, si no serán omitidas. Requerido cuando limit es negativo"),
    order: Optional[Literal["ASC", "DESC"]] = Query("ASC", description="Dirección de ordenamiento: 'ASC' para ascendente (por defecto), 'DESC' para descendente. Solo aplica si order_by está definido", regex="^(ASC|DESC)$"),
    offset: Optional[int] = Query(None, description="Número de registros a omitir desde el inicio. Útil para paginación. Debe ser un valor no negativo", ge=0),
    prompt_tokens: Optional[int] = Query(None, description="Filtrar por valor exacto de prompt_tokens. Tokens consumidos en el prompt"),
    min_prompt_tokens: Optional[int] = Query(None, description="Valor mínimo para prompt_tokens (incluido)"),
    max_prompt_tokens: Optional[int] = Query(None, description="Valor máximo para prompt_tokens (incluido)"),
    completion_tokens: Optional[int] = Query(None, description="Filtrar por valor exacto de completion_tokens. Tokens consumidos en la respuesta"),
    min_completion_tokens: Optional[int] = Query(None, description="Valor mínimo para completion_tokens (incluido)"),
    max_completion_tokens: Optional[int] = Query(None, description="Valor máximo para completion_tokens (incluido)"),
    total_tokens: Optional[int] = Query(None, description="Filtrar por valor exacto de total_tokens. Total de tokens consumidos"),
    min_total_tokens: Optional[int] = Query(None, description="Valor mínimo para total_tokens (incluido)"),
    max_total_tokens: Optional[int] = Query(None, description="Valor máximo para total_tokens (incluido)"),
    model_name: Optional[str] = Query(None, description='Filtrar por model_name. ⚠️ **IMPORTANTE**: utiliza "%model_name%" para hacer consultas ILIKE. Nombre del modelo utilizado', min_length=1, max_length=255),
    provider: Optional[str] = Query(None, description='Filtrar por provider. ⚠️ **IMPORTANTE**: utiliza "%provider%" para hacer consultas ILIKE. Proveedor del modelo (OpenAI, Anthropic, etc.)', min_length=1, max_length=255),
    min_cost_usd: Optional[float] = Query(None, description="Valor mínimo para cost_usd (incluido)"),
    max_cost_usd: Optional[float] = Query(None, description="Valor máximo para cost_usd (incluido)"),
    min_timestamp: Optional[datetime] = Query(None, description="Fecha y hora mínima para timestamp (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_timestamp: Optional[datetime] = Query(None, description="Fecha y hora máxima para timestamp (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    message_id: Optional[int] = Query(None, description="Filtrar por message_id (clave foránea)"),
    includes: List[str] = Query(None, description="Lista de relaciones a incluir en la respuesta para obtener datos relacionados. Especifica los nombres de las relaciones que deseas expandir"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[List[TokenUsageRead]]:
    """
    ## Resumen
    Obtiene una lista de `token_usages` con filtros opcionales y soporte para paginación.
    
    Este endpoint permite realizar búsquedas flexibles aplicando filtros opcionales
    por cualquiera de los campos disponibles, con soporte completo para paginación
    mediante los parámetros limit y offset.

    ## Resultado
    En `APIResponse.data`, retorna un listado de objetos donde cada uno representa un registro de la tabla `token_usage` que incluye todos sus atributos

    ## Datos
    Para cada registro en `data` se incluye:
    - **id** (int): Campo id de la tabla token_usage
    - **prompt_tokens** (int): Tokens consumidos en el prompt
    - **completion_tokens** (int): Tokens consumidos en la respuesta
    - **total_tokens** (int): Total de tokens consumidos
    - **model_name** (str): Nombre del modelo utilizado
    - **provider** (str): Proveedor del modelo (OpenAI, Anthropic, etc.)
    - **cost_usd** (float, opcional): Costo estimado en USD
    - **timestamp** (datetime): Timestamp del consumo
    - **message_id** (int): ID del mensaje asociado
    
    ## Parámetros de Filtrado
    
    Todos los parámetros de filtrado son opcionales y se pueden combinar:
    - **prompt_tokens**: Filtrar por prompt_tokens
    - **min_prompt_tokens**: Filtrar por fecha mínima (incluída)
    - **max_prompt_tokens**: Filtrar por fecha máxima (incluída)
    - **completion_tokens**: Filtrar por completion_tokens
    - **min_completion_tokens**: Filtrar por fecha mínima (incluída)
    - **max_completion_tokens**: Filtrar por fecha máxima (incluída)
    - **total_tokens**: Filtrar por total_tokens
    - **min_total_tokens**: Filtrar por fecha mínima (incluída)
    - **max_total_tokens**: Filtrar por fecha máxima (incluída)
    - **model_name**: Filtrar por model_name. ⚠️ **IMPORTANTE**: utiliza "%model_name%" para hacer consultas ILIKE.
    - **provider**: Filtrar por provider. ⚠️ **IMPORTANTE**: utiliza "%provider%" para hacer consultas ILIKE.
    - **min_cost_usd**: Filtrar por valor mínimo de cost_usd (incluído el valor del filtro)
    - **max_cost_usd**: Filtrar por valor máximo de cost_usd (incluído el valor del filtro)
    - **min_timestamp**: Filtrar por valor mínimo de timestamp (incluído el valor del filtro)
    - **max_timestamp**: Filtrar por valor máximo de timestamp (incluído el valor del filtro)
    - **message_id**: Filtrar por message_id

    
    ## Parámetros de Paginación
    
    - **limit**: Número máximo de registros a retornar. Solo admite valores positivos. Si no se especifica, retorna todos los registros que coincidan con los filtros.
    - **order_by**: Lista de nombres de columnas para ordenar los resultados.⚠️ **IMPORTANTE**: los nombres de columnas deben existir, si no serán omitidas.
    - **order**: Dirección de ordenamiento: 'ASC' para ascendente (por defecto), 'DESC' para descendente. Solo aplica si order_by está definido.
    - **offset**: Número de registros a omitir desde el inicio. Solo admite valores positivos. Si no se especifica, inicia desde el primer registro.
    
    ## Consulta combinada (recomendado para pocos registros)
    ⚠️ **IMPORTANTE**: Usa siempre el parámetro `includes` para cargar relaciones en una sola consulta y evitar múltiples llamadas al API.
    
    ⚠️ **WARNING**: Si la relación incluida tiene muchos registros relacionados, la respuesta puede ser muy grande y lenta. Mejor consultar su endpoint directamente con filtros.
    
    El parametro `includes` permite cargar relaciones asociadas a los registros.

    ### Relaciones disponibles
    - **message**: Mensaje relacionado (many-to-one)

        - **descripción**: Tabla que almacena los mensajes individuales de cada chat
    
    ### Ejemplos básicos:
    #### Solo datos básicos
    `token_usage = GET /token_usage`
    
    #### Incluir message
    `token_usage = GET /token_usage?includes=message`
    
    #### Relaciones anidadas
    Puedes incluir los datos de message y además incluir sus propias relaciones  
    `token_usage = GET /token_usage?includes=message.{nested_relation}`  
    """
    result = await api.token_usage.find_many(
        limit=limit,
        offset=offset,
        order_by=order_by,
        order=order,
        prompt_tokens=prompt_tokens,
        min_prompt_tokens=min_prompt_tokens,
        max_prompt_tokens=max_prompt_tokens,
        completion_tokens=completion_tokens,
        min_completion_tokens=min_completion_tokens,
        max_completion_tokens=max_completion_tokens,
        total_tokens=total_tokens,
        min_total_tokens=min_total_tokens,
        max_total_tokens=max_total_tokens,
        model_name=model_name,
        provider=provider,
        min_cost_usd=min_cost_usd,
        max_cost_usd=max_cost_usd,
        min_timestamp=min_timestamp,
        max_timestamp=max_timestamp,
        message_id=message_id,
        includes=includes
    )
    
    # Obtener el total para metadatos de paginación si es necesario
    total = None
    if limit is not None or offset is not None:
        try:
            total = await api.token_usage.count(
                prompt_tokens=prompt_tokens,
                min_prompt_tokens=min_prompt_tokens,
                max_prompt_tokens=max_prompt_tokens,
                completion_tokens=completion_tokens,
                min_completion_tokens=min_completion_tokens,
                max_completion_tokens=max_completion_tokens,
                total_tokens=total_tokens,
                min_total_tokens=min_total_tokens,
                max_total_tokens=max_total_tokens,
                model_name=model_name,
                provider=provider,
                min_cost_usd=min_cost_usd,
                max_cost_usd=max_cost_usd,
                min_timestamp=min_timestamp,
                max_timestamp=max_timestamp,
                message_id=message_id,
            )
        except Exception as e:
            logger.warning(f"No se pudo obtener el total de registros: {str(e)}")
    
    return PaginatedResponse.success_paginated(
        data=result,
        total=total,
        limit=limit,
        offset=offset,
        message=f"TokenUsages obtenidos exitosamente"
    )

@token_usage_router.get("/{id:int}", 
    response_model=APIResponse[TokenUsageRead],
    response_description="Registro único de token_usage obtenido exitosamente",
    operation_id="token_usage_find",
    summary="Busca un registro en la tabla token_usage",
    responses={
        200: {
            "description": "Registro único de token_usage obtenido exitosamente",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/APIResponse_TokenUsageRead_"
                    }
                }
            },
            "links": {
                "self": {
                    "operationId": "token_usage_find",
                    "description": "Enlace al recurso actual",
                    "parameters": {
                        "id": "$response.body#/data/id",
                        "includes": "$request.query.includes"
                    }
                },
                "collection": {
                    "operationId": "token_usage_find_many",
                    "description": "Enlace a la colección de TokenUsages"
                },
                "edit": {
                    "operationId": "token_usage_update",
                    "description": "Enlace para actualizar este TokenUsage",
                    "parameters": {
                        "id": "$response.body#/data/id",
                    }
                },
                "delete": {
                    "operationId": "token_usage_delete",
                    "description": "Enlace para eliminar este TokenUsage",
                    "parameters": {
                        "id": "$response.body#/data/id",
                    }
                },
            "message": {
            "operationId": "mensaje_find",
                    "description": "Enlace al Mensaje relacionado",
                    "parameters": {
                        "id": "$response.body#/data/message_id",
                        "includes": "$request.query.includes"
                    }
            }
            }
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
                                "message": "id debe ser mayor a 0",
                                "field": "id",
                                "details": None
                            }
                        ],
                        "meta": None
                    }
                }
            }
        },
        404: {
            "description": "TokenUsage no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "TokenUsage no encontrado",
                        "errors": [
                            {
                                "code": "RECORD_NOT_FOUND",
                                "message": "TokenUsage no encontrado",
                                "field": None,
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
async def token_usage_find(
    id: int = Path(..., description="Campo id de la tabla token_usage", gt=0),
    includes: List[str] = Query(None, description="Lista de relaciones a incluir en la respuesta para obtener datos relacionados. Especifica los nombres de las relaciones que deseas expandir"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[TokenUsageRead]:
    """
    ## Resumen
    Obtiene un TokenUsage específico por su clave primaria.
    
    Este endpoint permite recuperar un registro individual de TokenUsage
    utilizando su identificador único (clave primaria). Opcionalmente puede
    incluir datos de relaciones asociadas.

    ## Resultado
    Si la consulta es exitosa, en `APIResponse.data`, retorna un objeto que representa un registro de la tabla `token_usage` que incluye todos sus atributos

    Si no se encuentra el registro, devuelve un error 404 `RECORD_NOT_FOUND`.

    ## Datos
    Para cada registro en `data` se incluye:
    - **id** (int): Campo id de la tabla token_usage
    - **prompt_tokens** (int): Tokens consumidos en el prompt
    - **completion_tokens** (int): Tokens consumidos en la respuesta
    - **total_tokens** (int): Total de tokens consumidos
    - **model_name** (str): Nombre del modelo utilizado
    - **provider** (str): Proveedor del modelo (OpenAI, Anthropic, etc.)
    - **cost_usd** (float, opcional): Costo estimado en USD
    - **timestamp** (datetime): Timestamp del consumo
    - **message_id** (int): ID del mensaje asociado
    
    ## Parámetros de Identificación
    
    - **id**: id del TokenUsage a buscar (tipo: int)
    
    ## Consulta combinada (RECOMENDADO)
    ⚠️ **IMPORTANTE**: Usa siempre el parámetro `includes` para cargar relaciones en una sola consulta y evitar múltiples llamadas al API.
    
    El parametro `includes` permite cargar relaciones asociadas a los registros.

    ### Relaciones disponibles (usar con parámetro 'includes'):
    - message: Mensaje relacionado (many-to-one)
        Tabla que almacena los mensajes individuales de cada chat
    
    ### Uso del parámetro 'includes':
    Para cargar relaciones específicas, usa el parámetro 'includes' en la consulta:
    
    ### Ejemplos básicos:
    #### Solo datos básicos
    `token_usage = GET /token_usage/{id:int}`
    
    #### Incluir message
    `token_usage = GET /token_usage/{id:int}?includes=message`
    
    #### Relaciones anidadas
    Puedes incluir los datos de message y además incluir sus propias relaciones  
    `token_usage = GET /token_usage/{id:int}?includes=message.{nested_relation}`
    """
    # Validaciones básicas de entrada
    if id <= 0:
        raise ValidationException("id debe ser mayor a 0", "id")
    
    result = await api.token_usage.find(
        id=id,
        includes=includes
    )
    
    if result is None:
        raise RecordNotFoundException("TokenUsage")
        
    return APIResponse.success(
        data=result,
        message="TokenUsage obtenido exitosamente"
    )

@token_usage_router.get("/count", 
    response_model=APIResponse[int],
    response_description="Número de registros de token_usage según los filtros aplicados",
    operation_id="token_usage_count",
    summary="Cuenta registros en la tabla token_usage",
    responses={
        200: {
            "description": "Conteo realizado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": 42,
                        "message": "Conteo realizado exitosamente",
                        "errors": None,
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
async def token_usage_count(
    prompt_tokens: Optional[int] = Query(None, description="Filtrar por valor exacto de prompt_tokens. Tokens consumidos en el prompt"),
    min_prompt_tokens: Optional[int] = Query(None, description="Valor mínimo para prompt_tokens (incluido)"),
    max_prompt_tokens: Optional[int] = Query(None, description="Valor máximo para prompt_tokens (incluido)"),
    completion_tokens: Optional[int] = Query(None, description="Filtrar por valor exacto de completion_tokens. Tokens consumidos en la respuesta"),
    min_completion_tokens: Optional[int] = Query(None, description="Valor mínimo para completion_tokens (incluido)"),
    max_completion_tokens: Optional[int] = Query(None, description="Valor máximo para completion_tokens (incluido)"),
    total_tokens: Optional[int] = Query(None, description="Filtrar por valor exacto de total_tokens. Total de tokens consumidos"),
    min_total_tokens: Optional[int] = Query(None, description="Valor mínimo para total_tokens (incluido)"),
    max_total_tokens: Optional[int] = Query(None, description="Valor máximo para total_tokens (incluido)"),
    model_name: Optional[str] = Query(None, description='Filtrar por model_name. ⚠️ **IMPORTANTE**: utiliza "%model_name%" para hacer consultas ILIKE. Nombre del modelo utilizado', min_length=1, max_length=255),
    provider: Optional[str] = Query(None, description='Filtrar por provider. ⚠️ **IMPORTANTE**: utiliza "%provider%" para hacer consultas ILIKE. Proveedor del modelo (OpenAI, Anthropic, etc.)', min_length=1, max_length=255),
    min_cost_usd: Optional[float] = Query(None, description="Valor mínimo para cost_usd (incluido)"),
    max_cost_usd: Optional[float] = Query(None, description="Valor máximo para cost_usd (incluido)"),
    min_timestamp: Optional[datetime] = Query(None, description="Fecha y hora mínima para timestamp (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_timestamp: Optional[datetime] = Query(None, description="Fecha y hora máxima para timestamp (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    message_id: Optional[int] = Query(None, description="Filtrar por message_id (clave foránea)"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[int]:
    """
    Cuenta el número de TokenUsages que coinciden con los filtros.
    """
    result = await api.token_usage.count(
        prompt_tokens=prompt_tokens,
        min_prompt_tokens=min_prompt_tokens,
        max_prompt_tokens=max_prompt_tokens,
        completion_tokens=completion_tokens,
        min_completion_tokens=min_completion_tokens,
        max_completion_tokens=max_completion_tokens,
        total_tokens=total_tokens,
        min_total_tokens=min_total_tokens,
        max_total_tokens=max_total_tokens,
        model_name=model_name,
        provider=provider,
        min_cost_usd=min_cost_usd,
        max_cost_usd=max_cost_usd,
        min_timestamp=min_timestamp,
        max_timestamp=max_timestamp,
        message_id=message_id,
    )
    
    return APIResponse.success(
        data=result,
        message="Conteo realizado exitosamente"
    )

@token_usage_router.get("/exists", 
    response_model=APIResponse[bool],
    operation_id="token_usage_exists",
    summary="Verifica existencia en la tabla token_usage",
    responses={
        200: {
            "description": "Verificación realizada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": True,
                        "message": "Verificación realizada exitosamente",
                        "errors": None,
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
async def token_usage_exists(
    prompt_tokens: Optional[int] = Query(None, description="Filtrar por valor exacto de prompt_tokens. Tokens consumidos en el prompt"),
    min_prompt_tokens: Optional[int] = Query(None, description="Valor mínimo para prompt_tokens (incluido)"),
    max_prompt_tokens: Optional[int] = Query(None, description="Valor máximo para prompt_tokens (incluido)"),
    completion_tokens: Optional[int] = Query(None, description="Filtrar por valor exacto de completion_tokens. Tokens consumidos en la respuesta"),
    min_completion_tokens: Optional[int] = Query(None, description="Valor mínimo para completion_tokens (incluido)"),
    max_completion_tokens: Optional[int] = Query(None, description="Valor máximo para completion_tokens (incluido)"),
    total_tokens: Optional[int] = Query(None, description="Filtrar por valor exacto de total_tokens. Total de tokens consumidos"),
    min_total_tokens: Optional[int] = Query(None, description="Valor mínimo para total_tokens (incluido)"),
    max_total_tokens: Optional[int] = Query(None, description="Valor máximo para total_tokens (incluido)"),
    model_name: Optional[str] = Query(None, description='Filtrar por model_name. ⚠️ **IMPORTANTE**: utiliza "%model_name%" para hacer consultas ILIKE. Nombre del modelo utilizado', min_length=1, max_length=255),
    provider: Optional[str] = Query(None, description='Filtrar por provider. ⚠️ **IMPORTANTE**: utiliza "%provider%" para hacer consultas ILIKE. Proveedor del modelo (OpenAI, Anthropic, etc.)', min_length=1, max_length=255),
    min_cost_usd: Optional[float] = Query(None, description="Valor mínimo para cost_usd (incluido)"),
    max_cost_usd: Optional[float] = Query(None, description="Valor máximo para cost_usd (incluido)"),
    min_timestamp: Optional[datetime] = Query(None, description="Fecha y hora mínima para timestamp (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_timestamp: Optional[datetime] = Query(None, description="Fecha y hora máxima para timestamp (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    message_id: Optional[int] = Query(None, description="Filtrar por message_id (clave foránea)"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[bool]:
    """
    Verifica si existe al menos un token_usage que coincida con los filtros.
    """
    result = await api.token_usage.exists(
        prompt_tokens=prompt_tokens,
        min_prompt_tokens=min_prompt_tokens,
        max_prompt_tokens=max_prompt_tokens,
        completion_tokens=completion_tokens,
        min_completion_tokens=min_completion_tokens,
        max_completion_tokens=max_completion_tokens,
        total_tokens=total_tokens,
        min_total_tokens=min_total_tokens,
        max_total_tokens=max_total_tokens,
        model_name=model_name,
        provider=provider,
        min_cost_usd=min_cost_usd,
        max_cost_usd=max_cost_usd,
        min_timestamp=min_timestamp,
        max_timestamp=max_timestamp,
        message_id=message_id,
    )
    
    return APIResponse.success(
        data=result,
        message="Verificación realizada exitosamente"
    )

@token_usage_router.post("", 
    response_model=APIResponse[TokenUsageRead],
    status_code=201,
    operation_id="token_usage_create",
    summary="Crea un registro en la tabla token_usage",
    responses={
        422: {
            "description": "Error de validación en los datos de entrada",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "Error de validación",
                        "errors": [
                            {
                                "code": "VALIDATION_ERROR",
                                "message": "El campo es requerido",
                                "field": "prompt_tokens",
                                "details": None
                            }
                        ],
                        "meta": None
                    }
                }
            }
        },
        409: {
            "description": "Registro duplicado",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "El registro ya existe",
                        "errors": [
                            {
                                "code": "DUPLICATE_RECORD",
                                "message": "El registro ya existe",
                                "field": None,
                                "details": None
                            }
                        ],
                        "meta": None
                    }
                }
            }
        },
        422: {
            "description": "Violación de clave foránea",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "Violación de clave foránea",
                        "errors": [
                            {
                                "code": "FOREIGN_KEY_VIOLATION",
                                "message": "La referencia especificada no existe",
                                "field": None,
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
async def token_usage_create(
    token_usage: TokenUsageCreate,
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[TokenUsageRead]:
    """
    Crea un nuevo TokenUsage.
    """
    result = await api.token_usage.create(token_usage)
    
    return APIResponse.success(
        data=result,
        message="TokenUsage creado exitosamente"
    )

@token_usage_router.patch("/{id:int}", 
    response_model=APIResponse[int],
    operation_id="token_usage_update",
    summary="Actualiza un registro en la tabla token_usage",
    responses={
        200: {
            "description": "TokenUsage actualizado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": 1,
                        "message": "TokenUsage actualizado exitosamente",
                        "errors": None,
                        "meta": None
                    }
                }
            }
        },
        422: {
            "description": "Error de validación en parámetros o datos",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "Error de validación",
                        "errors": [
                            {
                                "code": "VALIDATION_ERROR",
                                "message": "id debe ser mayor a 0",
                                "field": "id",
                                "details": None
                            }
                        ],
                        "meta": None
                    }
                }
            }
        },
        404: {
            "description": "TokenUsage no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "TokenUsage no encontrado",
                        "errors": [
                            {
                                "code": "RECORD_NOT_FOUND",
                                "message": "TokenUsage no encontrado",
                                "field": None,
                                "details": None
                            }
                        ],
                        "meta": None
                    }
                }
            }
        },
        422: {
            "description": "Violación de clave foránea",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "Violación de clave foránea",
                        "errors": [
                            {
                                "code": "FOREIGN_KEY_VIOLATION",
                                "message": "La referencia especificada no existe",
                                "field": None,
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
async def token_usage_update(
    id: int = Path(..., description="Campo id de la tabla token_usage", gt=0),
    values: TokenUsageUpdateValues = Body(...),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[int]:
    """
    Actualiza un TokenUsage específico.
    """
    # Validaciones básicas de entrada
    if id <= 0:
        raise ValidationException("id debe ser mayor a 0", "id")
    
    # Verificar que el registro existe antes de actualizar
    existing = await api.token_usage.find(
        id=id,
    )
    
    if existing is None:
        raise RecordNotFoundException("TokenUsage")
    
    result = await api.token_usage.update(
        id=id,
        updated_values=values
    )
    
    if result == 0:
        raise RecordNotFoundException("TokenUsage")
        
    return APIResponse.success(
        data=result,
        message="TokenUsage actualizado exitosamente"
    )

@token_usage_router.patch("", 
    response_model=APIResponse[int],
    operation_id="token_usage_update_many",
    summary="Actualiza múltiples registros en la tabla token_usage",
    responses={
        200: {
            "description": "TokenUsages actualizados exitosamente",
            "content": {
                "application/json": {
                    "examples": {
                        "records_updated": {
                            "summary": "Registros actualizados",
                            "value": {
                                "status": "success",
                                "data": 5,
                                "message": "5 TokenUsages actualizados exitosamente",
                                "errors": None,
                                "meta": None
                            }
                        },
                        "no_records_found": {
                            "summary": "No se encontraron registros",
                            "value": {
                                "status": "success",
                                "data": 0,
                                "message": "No se encontraron registros que coincidan con los criterios",
                                "errors": None,
                                "meta": None
                            }
                        }
                    }
                }
            }
        },
        422: {
            "description": "Error de validación en los datos",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "Error de validación",
                        "errors": [
                            {
                                "code": "VALIDATION_ERROR",
                                "message": "Los criterios de búsqueda son requeridos",
                                "field": "filters",
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
async def token_usage_update_many(
    payload: TokenUsageUpdate,
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[int]:
    """
    Actualiza múltiples TokenUsages.
    """
    result = await api.token_usage.update_many(payload)
    
    message = f"{result} TokenUsages actualizados exitosamente" if result > 0 else "No se encontraron registros que coincidan con los criterios"
    
    return APIResponse.success(
        data=result,
        message=message
    )

@token_usage_router.delete("/{id:int}", 
    response_model=APIResponse[int],
    operation_id="token_usage_delete",
    summary="Elimina un registro en la tabla token_usage",
    responses={
        200: {
            "description": "TokenUsage eliminado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": 1,
                        "message": "TokenUsage eliminado exitosamente",
                        "errors": None,
                        "meta": None
                    }
                }
            }
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
                                "message": "id debe ser mayor a 0",
                                "field": "id",
                                "details": None
                            }
                        ],
                        "meta": None
                    }
                }
            }
        },
        404: {
            "description": "TokenUsage no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "TokenUsage no encontrado",
                        "errors": [
                            {
                                "code": "RECORD_NOT_FOUND",
                                "message": "TokenUsage no encontrado",
                                "field": None,
                                "details": None
                            }
                        ],
                        "meta": None
                    }
                }
            }
        },
        422: {
            "description": "Violación de clave foránea",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "Violación de clave foránea",
                        "errors": [
                            {
                                "code": "FOREIGN_KEY_VIOLATION",
                                "message": "No se puede eliminar el registro porque está siendo referenciado",
                                "field": None,
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
async def token_usage_delete(
    id: int = Path(..., description="Campo id de la tabla token_usage", gt=0),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[int]:
    """
    Elimina un TokenUsage por su primary key.
    """
    # Validaciones básicas de entrada
    if id <= 0:
        raise ValidationException("id debe ser mayor a 0", "id")
    
    # Verificar que el registro existe antes de eliminar
    existing = await api.token_usage.find(
        id=id,
    )
    
    if existing is None:
        raise RecordNotFoundException("TokenUsage")
    
    result = await api.token_usage.delete(
        id=id,
    )
    
    if result == 0:
        raise RecordNotFoundException("TokenUsage")
        
    return APIResponse.success(
        data=result,
        message="TokenUsage eliminado exitosamente"
    )
