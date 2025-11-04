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

chat_router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

@chat_router.get("", 
    response_model=APIResponse[List[ChatRead]],
    response_description="Lista de registros de chat obtenido exitosamente",
    operation_id="chat_find_many",
    summary="Busca varios registros en la tabla chat",
    responses={
        200: {
            "description": "Lista de registros de chat obtenido exitosamente",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/APIResponse_List_ChatRead__"
                    }
                }
            },
            "links": {
                "self": {
                    "operationId": "chat_find_many",
                    "description": "Enlace a la consulta actual con los mismos filtros",
                    "parameters": {
                        "title": "$request.query.title",
                        "username": "$request.query.username",
                        "created_at": "$request.query.created_at",
                        "updated_at": "$request.query.updated_at",
                        "is_active": "$request.query.is_active",
                        "limit": "$request.query.limit",
                        "offset": "$request.query.offset",
                        "order_by": "$request.query.order_by",
                        "order": "$request.query.order",
                        "includes": "$request.query.includes"
                    }
                },
                "item": {
                    "operationId": "chat_find",
                    "description": "Enlace para acceder a un elemento específico",
                    "parameters": {
                        "id": "$response.body#/data/**/id",
                        "includes": "$request.query.includes"
                    }
                },
                "create": {
                    "operationId": "chat_create",
                    "description": "Enlace para crear un nuevo Chat"
                },
                "count": {
                    "operationId": "chat_count",
                    "description": "Enlace para obtener el conteo total con los mismos filtros",
                    "parameters": {
                        "title": "$request.query.title",
                        "username": "$request.query.username",
                        "created_at": "$request.query.created_at",
                        "updated_at": "$request.query.updated_at",
                        "is_active": "$request.query.is_active",
                    }
                },
            "messages": {
            "operationId": "mensaje_find_many",
                    "description": "Enlace a los Mensajes relacionados",
                    "parameters": {
                        "id": "$response.body#/data/**/chat_id",
                        "includes": "$request.query.includes"
                    }
            },
            "usuario": {
            "operationId": "usuario_find",
                    "description": "Enlace al Usuario relacionado",
                    "parameters": {
                        "username": "$response.body#/data/**/username",
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
async def chat_find_many(
    limit: Optional[int] = Query(None, description="Número de registros a retornar. Valores positivos toman los n primeros registros, valores negativos toman los n últimos registros (requiere order_by)", gt=0),
    order_by: List[str] = Query(None, description="Lista de nombres de columnas para ordenar los resultados.⚠️ **IMPORTANTE**: los nombres de columnas deben existir, si no serán omitidas. Requerido cuando limit es negativo"),
    order: Optional[Literal["ASC", "DESC"]] = Query("ASC", description="Dirección de ordenamiento: 'ASC' para ascendente (por defecto), 'DESC' para descendente. Solo aplica si order_by está definido", regex="^(ASC|DESC)$"),
    offset: Optional[int] = Query(None, description="Número de registros a omitir desde el inicio. Útil para paginación. Debe ser un valor no negativo", ge=0),
    title: Optional[str] = Query(None, description='Filtrar por title. ⚠️ **IMPORTANTE**: utiliza "%title%" para hacer consultas ILIKE. Título de la conversación', min_length=1, max_length=255),
    username: Optional[str] = Query(None, description="Filtrar por username (clave foránea)"),
    min_created_at: Optional[datetime] = Query(None, description="Fecha y hora mínima para created_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_created_at: Optional[datetime] = Query(None, description="Fecha y hora máxima para created_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    min_updated_at: Optional[datetime] = Query(None, description="Fecha y hora mínima para updated_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_updated_at: Optional[datetime] = Query(None, description="Fecha y hora máxima para updated_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    is_active: Optional[bool] = Query(None, description="Filtrar por is_active (verdadero/falso). Estado activo del chat"),
    includes: List[str] = Query(None, description="Lista de relaciones a incluir en la respuesta para obtener datos relacionados. Especifica los nombres de las relaciones que deseas expandir"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[List[ChatRead]]:
    """
    ## Resumen
    Obtiene una lista de `chats` con filtros opcionales y soporte para paginación.
    
    Este endpoint permite realizar búsquedas flexibles aplicando filtros opcionales
    por cualquiera de los campos disponibles, con soporte completo para paginación
    mediante los parámetros limit y offset.

    ## Resultado
    En `APIResponse.data`, retorna un listado de objetos donde cada uno representa un registro de la tabla `chat` que incluye todos sus atributos

    ## Datos
    Para cada registro en `data` se incluye:
    - **id** (int): UUID del chat
    - **title** (str): Título de la conversación
    - **username** (str): ID del usuario propietario del chat
    - **created_at** (datetime): Fecha de creación del chat
    - **updated_at** (datetime): Fecha de última actualización
    - **is_active** (bool): Estado activo del chat
    
    ## Parámetros de Filtrado
    
    Todos los parámetros de filtrado son opcionales y se pueden combinar:
    - **title**: Filtrar por title. ⚠️ **IMPORTANTE**: utiliza "%title%" para hacer consultas ILIKE.
    - **username**: Filtrar por username
    - **min_created_at**: Filtrar por valor mínimo de created_at (incluído el valor del filtro)
    - **max_created_at**: Filtrar por valor máximo de created_at (incluído el valor del filtro)
    - **min_updated_at**: Filtrar por valor mínimo de updated_at (incluído el valor del filtro)
    - **max_updated_at**: Filtrar por valor máximo de updated_at (incluído el valor del filtro)
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

    ### Relaciones disponibles
    - **messages**: lista de Mensaje relacionados (one-to-many)

        - **descripción**: Tabla que almacena los mensajes individuales de cada chat
    - **usuario**: Usuario relacionado (many-to-one)

        - **descripción**: Tabla que almacena información de los usuarios del chatbot
    
    ### Ejemplos básicos:
    #### Solo datos básicos
    `chat = GET /chat`
    
    #### Incluir messages
    `chat = GET /chat?includes=messages`
    
    #### Incluir usuario
    `chat = GET /chat?includes=usuario`
    
    #### Múltiples relaciones en una sola consulta
    `chat = GET /chat?includes=messages&includes=usuario`
    
    #### Relaciones anidadas
    Puedes incluir los datos de messages y además incluir sus propias relaciones  
    `chat = GET /chat?includes=messages.{nested_relation}`  
    Puedes incluir los datos de usuario y además incluir sus propias relaciones  
    `chat = GET /chat?includes=usuario.{nested_relation}`  
    """
    result = await api.chat.find_many(
        limit=limit,
        offset=offset,
        order_by=order_by,
        order=order,
        title=title,
        username=username,
        min_created_at=min_created_at,
        max_created_at=max_created_at,
        min_updated_at=min_updated_at,
        max_updated_at=max_updated_at,
        is_active=is_active,
        includes=includes
    )
    
    # Obtener el total para metadatos de paginación si es necesario
    total = None
    if limit is not None or offset is not None:
        try:
            total = await api.chat.count(
                title=title,
                username=username,
                min_created_at=min_created_at,
                max_created_at=max_created_at,
                min_updated_at=min_updated_at,
                max_updated_at=max_updated_at,
                is_active=is_active,
            )
        except Exception as e:
            logger.warning(f"No se pudo obtener el total de registros: {str(e)}")
    
    return PaginatedResponse.success_paginated(
        data=result,
        total=total,
        limit=limit,
        offset=offset,
        message=f"Chats obtenidos exitosamente"
    )

@chat_router.get("/{id:int}", 
    response_model=APIResponse[ChatRead],
    response_description="Registro único de chat obtenido exitosamente",
    operation_id="chat_find",
    summary="Busca un registro en la tabla chat",
    responses={
        200: {
            "description": "Registro único de chat obtenido exitosamente",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/APIResponse_ChatRead_"
                    }
                }
            },
            "links": {
                "self": {
                    "operationId": "chat_find",
                    "description": "Enlace al recurso actual",
                    "parameters": {
                        "id": "$response.body#/data/id",
                        "includes": "$request.query.includes"
                    }
                },
                "collection": {
                    "operationId": "chat_find_many",
                    "description": "Enlace a la colección de Chats"
                },
                "edit": {
                    "operationId": "chat_update",
                    "description": "Enlace para actualizar este Chat",
                    "parameters": {
                        "id": "$response.body#/data/id",
                    }
                },
                "delete": {
                    "operationId": "chat_delete",
                    "description": "Enlace para eliminar este Chat",
                    "parameters": {
                        "id": "$response.body#/data/id",
                    }
                },
            "messages": {
            "operationId": "mensaje_find_many",
                    "description": "Enlace a los Mensajes relacionados",
                    "parameters": {
                        "id": "$response.body#/data/chat_id",
                        "includes": "$request.query.includes"
                    }
            },
            "usuario": {
            "operationId": "usuario_find",
                    "description": "Enlace al Usuario relacionado",
                    "parameters": {
                        "username": "$response.body#/data/username",
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
            "description": "Chat no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "Chat no encontrado",
                        "errors": [
                            {
                                "code": "RECORD_NOT_FOUND",
                                "message": "Chat no encontrado",
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
async def chat_find(
    id: int = Path(..., description="UUID del chat", gt=0),
    includes: List[str] = Query(None, description="Lista de relaciones a incluir en la respuesta para obtener datos relacionados. Especifica los nombres de las relaciones que deseas expandir"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[ChatRead]:
    """
    ## Resumen
    Obtiene un Chat específico por su clave primaria.
    
    Este endpoint permite recuperar un registro individual de Chat
    utilizando su identificador único (clave primaria). Opcionalmente puede
    incluir datos de relaciones asociadas.

    ## Resultado
    Si la consulta es exitosa, en `APIResponse.data`, retorna un objeto que representa un registro de la tabla `chat` que incluye todos sus atributos

    Si no se encuentra el registro, devuelve un error 404 `RECORD_NOT_FOUND`.

    ## Datos
    Para cada registro en `data` se incluye:
    - **id** (int): UUID del chat
    - **title** (str): Título de la conversación
    - **username** (str): ID del usuario propietario del chat
    - **created_at** (datetime): Fecha de creación del chat
    - **updated_at** (datetime): Fecha de última actualización
    - **is_active** (bool): Estado activo del chat
    
    ## Parámetros de Identificación
    
    - **id**: id del Chat a buscar (tipo: int)
    
    ## Consulta combinada (RECOMENDADO)
    ⚠️ **IMPORTANTE**: Usa siempre el parámetro `includes` para cargar relaciones en una sola consulta y evitar múltiples llamadas al API.
    
    El parametro `includes` permite cargar relaciones asociadas a los registros.

    ### Relaciones disponibles (usar con parámetro 'includes'):
    - messages: Lista de Mensaje relacionados (one-to-many)
        Tabla que almacena los mensajes individuales de cada chat
    - usuario: Usuario relacionado (many-to-one)
        Tabla que almacena información de los usuarios del chatbot
    
    ### Uso del parámetro 'includes':
    Para cargar relaciones específicas, usa el parámetro 'includes' en la consulta:
    
    ### Ejemplos básicos:
    #### Solo datos básicos
    `chat = GET /chat/{id:int}`
    
    #### Incluir messages
    `chat = GET /chat/{id:int}?includes=messages`
    
    #### Incluir usuario
    `chat = GET /chat/{id:int}?includes=usuario`
    
    #### Múltiples relaciones en una sola consulta
    `chat = GET /chat/{id:int}?includes=messages&includes=usuario`
    
    #### Relaciones anidadas
    Puedes incluir los datos de messages y además incluir sus propias relaciones  
    `chat = GET /chat/{id:int}?includes=messages.{nested_relation}`
    Puedes incluir los datos de usuario y además incluir sus propias relaciones  
    `chat = GET /chat/{id:int}?includes=usuario.{nested_relation}`
    """
    # Validaciones básicas de entrada
    if id <= 0:
        raise ValidationException("id debe ser mayor a 0", "id")
    
    result = await api.chat.find(
        id=id,
        includes=includes
    )
    
    if result is None:
        raise RecordNotFoundException("Chat")
        
    return APIResponse.success(
        data=result,
        message="Chat obtenido exitosamente"
    )

@chat_router.get("/count", 
    response_model=APIResponse[int],
    response_description="Número de registros de chat según los filtros aplicados",
    operation_id="chat_count",
    summary="Cuenta registros en la tabla chat",
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
async def chat_count(
    title: Optional[str] = Query(None, description='Filtrar por title. ⚠️ **IMPORTANTE**: utiliza "%title%" para hacer consultas ILIKE. Título de la conversación', min_length=1, max_length=255),
    username: Optional[str] = Query(None, description="Filtrar por username (clave foránea)"),
    min_created_at: Optional[datetime] = Query(None, description="Fecha y hora mínima para created_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_created_at: Optional[datetime] = Query(None, description="Fecha y hora máxima para created_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    min_updated_at: Optional[datetime] = Query(None, description="Fecha y hora mínima para updated_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_updated_at: Optional[datetime] = Query(None, description="Fecha y hora máxima para updated_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    is_active: Optional[bool] = Query(None, description="Filtrar por is_active (verdadero/falso). Estado activo del chat"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[int]:
    """
    Cuenta el número de Chats que coinciden con los filtros.
    """
    result = await api.chat.count(
        title=title,
        username=username,
        min_created_at=min_created_at,
        max_created_at=max_created_at,
        min_updated_at=min_updated_at,
        max_updated_at=max_updated_at,
        is_active=is_active,
    )
    
    return APIResponse.success(
        data=result,
        message="Conteo realizado exitosamente"
    )

@chat_router.get("/exists", 
    response_model=APIResponse[bool],
    operation_id="chat_exists",
    summary="Verifica existencia en la tabla chat",
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
async def chat_exists(
    title: Optional[str] = Query(None, description='Filtrar por title. ⚠️ **IMPORTANTE**: utiliza "%title%" para hacer consultas ILIKE. Título de la conversación', min_length=1, max_length=255),
    username: Optional[str] = Query(None, description="Filtrar por username (clave foránea)"),
    min_created_at: Optional[datetime] = Query(None, description="Fecha y hora mínima para created_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_created_at: Optional[datetime] = Query(None, description="Fecha y hora máxima para created_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    min_updated_at: Optional[datetime] = Query(None, description="Fecha y hora mínima para updated_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_updated_at: Optional[datetime] = Query(None, description="Fecha y hora máxima para updated_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    is_active: Optional[bool] = Query(None, description="Filtrar por is_active (verdadero/falso). Estado activo del chat"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[bool]:
    """
    Verifica si existe al menos un chat que coincida con los filtros.
    """
    result = await api.chat.exists(
        title=title,
        username=username,
        min_created_at=min_created_at,
        max_created_at=max_created_at,
        min_updated_at=min_updated_at,
        max_updated_at=max_updated_at,
        is_active=is_active,
    )
    
    return APIResponse.success(
        data=result,
        message="Verificación realizada exitosamente"
    )

@chat_router.post("", 
    response_model=APIResponse[ChatRead],
    status_code=201,
    operation_id="chat_create",
    summary="Crea un registro en la tabla chat",
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
                                "field": "title",
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
async def chat_create(
    chat: ChatCreate,
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[ChatRead]:
    """
    Crea un nuevo Chat.
    """
    result = await api.chat.create(chat)
    
    return APIResponse.success(
        data=result,
        message="Chat creado exitosamente"
    )

@chat_router.patch("/{id:int}", 
    response_model=APIResponse[int],
    operation_id="chat_update",
    summary="Actualiza un registro en la tabla chat",
    responses={
        200: {
            "description": "Chat actualizado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": 1,
                        "message": "Chat actualizado exitosamente",
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
            "description": "Chat no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "Chat no encontrado",
                        "errors": [
                            {
                                "code": "RECORD_NOT_FOUND",
                                "message": "Chat no encontrado",
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
async def chat_update(
    id: int = Path(..., description="UUID del chat", gt=0),
    values: ChatUpdateValues = Body(...),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[int]:
    """
    Actualiza un Chat específico.
    """
    # Validaciones básicas de entrada
    if id <= 0:
        raise ValidationException("id debe ser mayor a 0", "id")
    
    # Verificar que el registro existe antes de actualizar
    existing = await api.chat.find(
        id=id,
    )
    
    if existing is None:
        raise RecordNotFoundException("Chat")
    
    result = await api.chat.update(
        id=id,
        updated_values=values
    )
    
    if result == 0:
        raise RecordNotFoundException("Chat")
        
    return APIResponse.success(
        data=result,
        message="Chat actualizado exitosamente"
    )

@chat_router.patch("", 
    response_model=APIResponse[int],
    operation_id="chat_update_many",
    summary="Actualiza múltiples registros en la tabla chat",
    responses={
        200: {
            "description": "Chats actualizados exitosamente",
            "content": {
                "application/json": {
                    "examples": {
                        "records_updated": {
                            "summary": "Registros actualizados",
                            "value": {
                                "status": "success",
                                "data": 5,
                                "message": "5 Chats actualizados exitosamente",
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
async def chat_update_many(
    payload: ChatUpdate,
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[int]:
    """
    Actualiza múltiples Chats.
    """
    result = await api.chat.update_many(payload)
    
    message = f"{result} Chats actualizados exitosamente" if result > 0 else "No se encontraron registros que coincidan con los criterios"
    
    return APIResponse.success(
        data=result,
        message=message
    )

@chat_router.delete("/{id:int}", 
    response_model=APIResponse[int],
    operation_id="chat_delete",
    summary="Elimina un registro en la tabla chat",
    responses={
        200: {
            "description": "Chat eliminado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": 1,
                        "message": "Chat eliminado exitosamente",
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
            "description": "Chat no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "Chat no encontrado",
                        "errors": [
                            {
                                "code": "RECORD_NOT_FOUND",
                                "message": "Chat no encontrado",
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
async def chat_delete(
    id: int = Path(..., description="UUID del chat", gt=0),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[int]:
    """
    Elimina un Chat por su primary key.
    """
    # Validaciones básicas de entrada
    if id <= 0:
        raise ValidationException("id debe ser mayor a 0", "id")
    
    # Verificar que el registro existe antes de eliminar
    existing = await api.chat.find(
        id=id,
    )
    
    if existing is None:
        raise RecordNotFoundException("Chat")
    
    result = await api.chat.delete(
        id=id,
    )
    
    if result == 0:
        raise RecordNotFoundException("Chat")
        
    return APIResponse.success(
        data=result,
        message="Chat eliminado exitosamente"
    )
