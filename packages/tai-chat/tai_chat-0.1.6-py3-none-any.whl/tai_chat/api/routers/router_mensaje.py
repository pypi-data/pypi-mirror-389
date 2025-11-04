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

mensaje_router = APIRouter(
    prefix="/mensaje",
    tags=["Mensaje"]
)

@mensaje_router.get("", 
    response_model=APIResponse[List[MensajeRead]],
    response_description="Lista de registros de mensaje obtenido exitosamente",
    operation_id="mensaje_find_many",
    summary="Busca varios registros en la tabla mensaje",
    responses={
        200: {
            "description": "Lista de registros de mensaje obtenido exitosamente",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/APIResponse_List_MensajeRead__"
                    }
                }
            },
            "links": {
                "self": {
                    "operationId": "mensaje_find_many",
                    "description": "Enlace a la consulta actual con los mismos filtros",
                    "parameters": {
                        "content": "$request.query.content",
                        "role": "$request.query.role",
                        "timestamp": "$request.query.timestamp",
                        "chat_id": "$request.query.chat_id",
                        "limit": "$request.query.limit",
                        "offset": "$request.query.offset",
                        "order_by": "$request.query.order_by",
                        "order": "$request.query.order",
                        "includes": "$request.query.includes"
                    }
                },
                "item": {
                    "operationId": "mensaje_find",
                    "description": "Enlace para acceder a un elemento específico",
                    "parameters": {
                        "id": "$response.body#/data/**/id",
                        "includes": "$request.query.includes"
                    }
                },
                "create": {
                    "operationId": "mensaje_create",
                    "description": "Enlace para crear un nuevo Mensaje"
                },
                "count": {
                    "operationId": "mensaje_count",
                    "description": "Enlace para obtener el conteo total con los mismos filtros",
                    "parameters": {
                        "content": "$request.query.content",
                        "role": "$request.query.role",
                        "timestamp": "$request.query.timestamp",
                        "chat_id": "$request.query.chat_id",
                    }
                },
            "token_usage": {
            "operationId": "tokenusage_find_many",
                    "description": "Enlace a los TokenUsages relacionados",
                    "parameters": {
                        "id": "$response.body#/data/**/message_id",
                        "includes": "$request.query.includes"
                    }
            },
            "chat": {
            "operationId": "chat_find",
                    "description": "Enlace al Chat relacionado",
                    "parameters": {
                        "id": "$response.body#/data/**/chat_id",
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
async def mensaje_find_many(
    limit: Optional[int] = Query(None, description="Número de registros a retornar. Valores positivos toman los n primeros registros, valores negativos toman los n últimos registros (requiere order_by)", gt=0),
    order_by: List[str] = Query(None, description="Lista de nombres de columnas para ordenar los resultados.⚠️ **IMPORTANTE**: los nombres de columnas deben existir, si no serán omitidas. Requerido cuando limit es negativo"),
    order: Optional[Literal["ASC", "DESC"]] = Query("ASC", description="Dirección de ordenamiento: 'ASC' para ascendente (por defecto), 'DESC' para descendente. Solo aplica si order_by está definido", regex="^(ASC|DESC)$"),
    offset: Optional[int] = Query(None, description="Número de registros a omitir desde el inicio. Útil para paginación. Debe ser un valor no negativo", ge=0),
    content: Optional[str] = Query(None, description='Filtrar por content. ⚠️ **IMPORTANTE**: utiliza "%content%" para hacer consultas ILIKE. Contenido del mensaje', min_length=1, max_length=255),
    role: Optional[str] = Query(None, description='Filtrar por role. ⚠️ **IMPORTANTE**: utiliza "%role%" para hacer consultas ILIKE. Rol del mensaje (user, assistant, system)', min_length=1, max_length=255),
    min_timestamp: Optional[datetime] = Query(None, description="Fecha y hora mínima para timestamp (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_timestamp: Optional[datetime] = Query(None, description="Fecha y hora máxima para timestamp (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    chat_id: Optional[int] = Query(None, description="Filtrar por chat_id (clave foránea)"),
    includes: List[str] = Query(None, description="Lista de relaciones a incluir en la respuesta para obtener datos relacionados. Especifica los nombres de las relaciones que deseas expandir"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[List[MensajeRead]]:
    """
    ## Resumen
    Obtiene una lista de `mensajes` con filtros opcionales y soporte para paginación.
    
    Este endpoint permite realizar búsquedas flexibles aplicando filtros opcionales
    por cualquiera de los campos disponibles, con soporte completo para paginación
    mediante los parámetros limit y offset.

    ## Resultado
    En `APIResponse.data`, retorna un listado de objetos donde cada uno representa un registro de la tabla `mensaje` que incluye todos sus atributos

    ## Datos
    Para cada registro en `data` se incluye:
    - **id** (int): UUID del mensaje
    - **content** (str): Contenido del mensaje
    - **role** (str): Rol del mensaje (user, assistant, system)
    - **timestamp** (datetime): Timestamp del mensaje
    - **chat_id** (int): ID del chat al que pertenece el mensaje
    
    ## Parámetros de Filtrado
    
    Todos los parámetros de filtrado son opcionales y se pueden combinar:
    - **content**: Filtrar por content. ⚠️ **IMPORTANTE**: utiliza "%content%" para hacer consultas ILIKE.
    - **role**: Filtrar por role. ⚠️ **IMPORTANTE**: utiliza "%role%" para hacer consultas ILIKE.
    - **min_timestamp**: Filtrar por valor mínimo de timestamp (incluído el valor del filtro)
    - **max_timestamp**: Filtrar por valor máximo de timestamp (incluído el valor del filtro)
    - **chat_id**: Filtrar por chat_id

    
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
    - **token_usage**: lista de TokenUsage relacionados (one-to-many)

        - **descripción**: Tabla que almacena el consumo de tokens para métricas y facturación
    - **chat**: Chat relacionado (many-to-one)

        - **descripción**: Tabla que almacena las conversaciones del chatbot
    
    ### Ejemplos básicos:
    #### Solo datos básicos
    `mensaje = GET /mensaje`
    
    #### Incluir token_usage
    `mensaje = GET /mensaje?includes=token_usage`
    
    #### Incluir chat
    `mensaje = GET /mensaje?includes=chat`
    
    #### Múltiples relaciones en una sola consulta
    `mensaje = GET /mensaje?includes=token_usage&includes=chat`
    
    #### Relaciones anidadas
    Puedes incluir los datos de token_usage y además incluir sus propias relaciones  
    `mensaje = GET /mensaje?includes=token_usage.{nested_relation}`  
    Puedes incluir los datos de chat y además incluir sus propias relaciones  
    `mensaje = GET /mensaje?includes=chat.{nested_relation}`  
    """
    result = await api.mensaje.find_many(
        limit=limit,
        offset=offset,
        order_by=order_by,
        order=order,
        content=content,
        role=role,
        min_timestamp=min_timestamp,
        max_timestamp=max_timestamp,
        chat_id=chat_id,
        includes=includes
    )
    
    # Obtener el total para metadatos de paginación si es necesario
    total = None
    if limit is not None or offset is not None:
        try:
            total = await api.mensaje.count(
                content=content,
                role=role,
                min_timestamp=min_timestamp,
                max_timestamp=max_timestamp,
                chat_id=chat_id,
            )
        except Exception as e:
            logger.warning(f"No se pudo obtener el total de registros: {str(e)}")
    
    return PaginatedResponse.success_paginated(
        data=result,
        total=total,
        limit=limit,
        offset=offset,
        message=f"Mensajes obtenidos exitosamente"
    )

@mensaje_router.get("/{id:int}", 
    response_model=APIResponse[MensajeRead],
    response_description="Registro único de mensaje obtenido exitosamente",
    operation_id="mensaje_find",
    summary="Busca un registro en la tabla mensaje",
    responses={
        200: {
            "description": "Registro único de mensaje obtenido exitosamente",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/APIResponse_MensajeRead_"
                    }
                }
            },
            "links": {
                "self": {
                    "operationId": "mensaje_find",
                    "description": "Enlace al recurso actual",
                    "parameters": {
                        "id": "$response.body#/data/id",
                        "includes": "$request.query.includes"
                    }
                },
                "collection": {
                    "operationId": "mensaje_find_many",
                    "description": "Enlace a la colección de Mensajes"
                },
                "edit": {
                    "operationId": "mensaje_update",
                    "description": "Enlace para actualizar este Mensaje",
                    "parameters": {
                        "id": "$response.body#/data/id",
                    }
                },
                "delete": {
                    "operationId": "mensaje_delete",
                    "description": "Enlace para eliminar este Mensaje",
                    "parameters": {
                        "id": "$response.body#/data/id",
                    }
                },
            "token_usage": {
            "operationId": "tokenusage_find_many",
                    "description": "Enlace a los TokenUsages relacionados",
                    "parameters": {
                        "id": "$response.body#/data/message_id",
                        "includes": "$request.query.includes"
                    }
            },
            "chat": {
            "operationId": "chat_find",
                    "description": "Enlace al Chat relacionado",
                    "parameters": {
                        "id": "$response.body#/data/chat_id",
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
            "description": "Mensaje no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "Mensaje no encontrado",
                        "errors": [
                            {
                                "code": "RECORD_NOT_FOUND",
                                "message": "Mensaje no encontrado",
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
async def mensaje_find(
    id: int = Path(..., description="UUID del mensaje", gt=0),
    includes: List[str] = Query(None, description="Lista de relaciones a incluir en la respuesta para obtener datos relacionados. Especifica los nombres de las relaciones que deseas expandir"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[MensajeRead]:
    """
    ## Resumen
    Obtiene un Mensaje específico por su clave primaria.
    
    Este endpoint permite recuperar un registro individual de Mensaje
    utilizando su identificador único (clave primaria). Opcionalmente puede
    incluir datos de relaciones asociadas.

    ## Resultado
    Si la consulta es exitosa, en `APIResponse.data`, retorna un objeto que representa un registro de la tabla `mensaje` que incluye todos sus atributos

    Si no se encuentra el registro, devuelve un error 404 `RECORD_NOT_FOUND`.

    ## Datos
    Para cada registro en `data` se incluye:
    - **id** (int): UUID del mensaje
    - **content** (str): Contenido del mensaje
    - **role** (str): Rol del mensaje (user, assistant, system)
    - **timestamp** (datetime): Timestamp del mensaje
    - **chat_id** (int): ID del chat al que pertenece el mensaje
    
    ## Parámetros de Identificación
    
    - **id**: id del Mensaje a buscar (tipo: int)
    
    ## Consulta combinada (RECOMENDADO)
    ⚠️ **IMPORTANTE**: Usa siempre el parámetro `includes` para cargar relaciones en una sola consulta y evitar múltiples llamadas al API.
    
    El parametro `includes` permite cargar relaciones asociadas a los registros.

    ### Relaciones disponibles (usar con parámetro 'includes'):
    - token_usage: Lista de TokenUsage relacionados (one-to-many)
        Tabla que almacena el consumo de tokens para métricas y facturación
    - chat: Chat relacionado (many-to-one)
        Tabla que almacena las conversaciones del chatbot
    
    ### Uso del parámetro 'includes':
    Para cargar relaciones específicas, usa el parámetro 'includes' en la consulta:
    
    ### Ejemplos básicos:
    #### Solo datos básicos
    `mensaje = GET /mensaje/{id:int}`
    
    #### Incluir token_usage
    `mensaje = GET /mensaje/{id:int}?includes=token_usage`
    
    #### Incluir chat
    `mensaje = GET /mensaje/{id:int}?includes=chat`
    
    #### Múltiples relaciones en una sola consulta
    `mensaje = GET /mensaje/{id:int}?includes=token_usage&includes=chat`
    
    #### Relaciones anidadas
    Puedes incluir los datos de token_usage y además incluir sus propias relaciones  
    `mensaje = GET /mensaje/{id:int}?includes=token_usage.{nested_relation}`
    Puedes incluir los datos de chat y además incluir sus propias relaciones  
    `mensaje = GET /mensaje/{id:int}?includes=chat.{nested_relation}`
    """
    # Validaciones básicas de entrada
    if id <= 0:
        raise ValidationException("id debe ser mayor a 0", "id")
    
    result = await api.mensaje.find(
        id=id,
        includes=includes
    )
    
    if result is None:
        raise RecordNotFoundException("Mensaje")
        
    return APIResponse.success(
        data=result,
        message="Mensaje obtenido exitosamente"
    )

@mensaje_router.get("/count", 
    response_model=APIResponse[int],
    response_description="Número de registros de mensaje según los filtros aplicados",
    operation_id="mensaje_count",
    summary="Cuenta registros en la tabla mensaje",
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
async def mensaje_count(
    content: Optional[str] = Query(None, description='Filtrar por content. ⚠️ **IMPORTANTE**: utiliza "%content%" para hacer consultas ILIKE. Contenido del mensaje', min_length=1, max_length=255),
    role: Optional[str] = Query(None, description='Filtrar por role. ⚠️ **IMPORTANTE**: utiliza "%role%" para hacer consultas ILIKE. Rol del mensaje (user, assistant, system)', min_length=1, max_length=255),
    min_timestamp: Optional[datetime] = Query(None, description="Fecha y hora mínima para timestamp (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_timestamp: Optional[datetime] = Query(None, description="Fecha y hora máxima para timestamp (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    chat_id: Optional[int] = Query(None, description="Filtrar por chat_id (clave foránea)"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[int]:
    """
    Cuenta el número de Mensajes que coinciden con los filtros.
    """
    result = await api.mensaje.count(
        content=content,
        role=role,
        min_timestamp=min_timestamp,
        max_timestamp=max_timestamp,
        chat_id=chat_id,
    )
    
    return APIResponse.success(
        data=result,
        message="Conteo realizado exitosamente"
    )

@mensaje_router.get("/exists", 
    response_model=APIResponse[bool],
    operation_id="mensaje_exists",
    summary="Verifica existencia en la tabla mensaje",
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
async def mensaje_exists(
    content: Optional[str] = Query(None, description='Filtrar por content. ⚠️ **IMPORTANTE**: utiliza "%content%" para hacer consultas ILIKE. Contenido del mensaje', min_length=1, max_length=255),
    role: Optional[str] = Query(None, description='Filtrar por role. ⚠️ **IMPORTANTE**: utiliza "%role%" para hacer consultas ILIKE. Rol del mensaje (user, assistant, system)', min_length=1, max_length=255),
    min_timestamp: Optional[datetime] = Query(None, description="Fecha y hora mínima para timestamp (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_timestamp: Optional[datetime] = Query(None, description="Fecha y hora máxima para timestamp (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    chat_id: Optional[int] = Query(None, description="Filtrar por chat_id (clave foránea)"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[bool]:
    """
    Verifica si existe al menos un mensaje que coincida con los filtros.
    """
    result = await api.mensaje.exists(
        content=content,
        role=role,
        min_timestamp=min_timestamp,
        max_timestamp=max_timestamp,
        chat_id=chat_id,
    )
    
    return APIResponse.success(
        data=result,
        message="Verificación realizada exitosamente"
    )

@mensaje_router.post("", 
    response_model=APIResponse[MensajeRead],
    status_code=201,
    operation_id="mensaje_create",
    summary="Crea un registro en la tabla mensaje",
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
                                "field": "content",
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
async def mensaje_create(
    mensaje: MensajeCreate,
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[MensajeRead]:
    """
    Crea un nuevo Mensaje.
    """
    result = await api.mensaje.create(mensaje)
    
    return APIResponse.success(
        data=result,
        message="Mensaje creado exitosamente"
    )

@mensaje_router.patch("/{id:int}", 
    response_model=APIResponse[int],
    operation_id="mensaje_update",
    summary="Actualiza un registro en la tabla mensaje",
    responses={
        200: {
            "description": "Mensaje actualizado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": 1,
                        "message": "Mensaje actualizado exitosamente",
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
            "description": "Mensaje no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "Mensaje no encontrado",
                        "errors": [
                            {
                                "code": "RECORD_NOT_FOUND",
                                "message": "Mensaje no encontrado",
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
async def mensaje_update(
    id: int = Path(..., description="UUID del mensaje", gt=0),
    values: MensajeUpdateValues = Body(...),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[int]:
    """
    Actualiza un Mensaje específico.
    """
    # Validaciones básicas de entrada
    if id <= 0:
        raise ValidationException("id debe ser mayor a 0", "id")
    
    # Verificar que el registro existe antes de actualizar
    existing = await api.mensaje.find(
        id=id,
    )
    
    if existing is None:
        raise RecordNotFoundException("Mensaje")
    
    result = await api.mensaje.update(
        id=id,
        updated_values=values
    )
    
    if result == 0:
        raise RecordNotFoundException("Mensaje")
        
    return APIResponse.success(
        data=result,
        message="Mensaje actualizado exitosamente"
    )

@mensaje_router.patch("", 
    response_model=APIResponse[int],
    operation_id="mensaje_update_many",
    summary="Actualiza múltiples registros en la tabla mensaje",
    responses={
        200: {
            "description": "Mensajes actualizados exitosamente",
            "content": {
                "application/json": {
                    "examples": {
                        "records_updated": {
                            "summary": "Registros actualizados",
                            "value": {
                                "status": "success",
                                "data": 5,
                                "message": "5 Mensajes actualizados exitosamente",
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
async def mensaje_update_many(
    payload: MensajeUpdate,
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[int]:
    """
    Actualiza múltiples Mensajes.
    """
    result = await api.mensaje.update_many(payload)
    
    message = f"{result} Mensajes actualizados exitosamente" if result > 0 else "No se encontraron registros que coincidan con los criterios"
    
    return APIResponse.success(
        data=result,
        message=message
    )

@mensaje_router.delete("/{id:int}", 
    response_model=APIResponse[int],
    operation_id="mensaje_delete",
    summary="Elimina un registro en la tabla mensaje",
    responses={
        200: {
            "description": "Mensaje eliminado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": 1,
                        "message": "Mensaje eliminado exitosamente",
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
            "description": "Mensaje no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "Mensaje no encontrado",
                        "errors": [
                            {
                                "code": "RECORD_NOT_FOUND",
                                "message": "Mensaje no encontrado",
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
async def mensaje_delete(
    id: int = Path(..., description="UUID del mensaje", gt=0),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[int]:
    """
    Elimina un Mensaje por su primary key.
    """
    # Validaciones básicas de entrada
    if id <= 0:
        raise ValidationException("id debe ser mayor a 0", "id")
    
    # Verificar que el registro existe antes de eliminar
    existing = await api.mensaje.find(
        id=id,
    )
    
    if existing is None:
        raise RecordNotFoundException("Mensaje")
    
    result = await api.mensaje.delete(
        id=id,
    )
    
    if result == 0:
        raise RecordNotFoundException("Mensaje")
        
    return APIResponse.success(
        data=result,
        message="Mensaje eliminado exitosamente"
    )
