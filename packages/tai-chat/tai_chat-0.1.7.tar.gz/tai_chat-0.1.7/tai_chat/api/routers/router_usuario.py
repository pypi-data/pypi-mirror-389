from fastapi import APIRouter, Depends, Query, Path, Body
from typing import Optional, List, Literal
from tai_alphi import Alphi
from datetime import datetime

from ..database import *
from ..resources import (
    APIResponse, PaginatedResponse, RecordNotFoundException
)


logger = Alphi.get_logger_by_name("tai-chatbot")

usuario_router = APIRouter(
    prefix="/usuario",
    tags=["Usuario"]
)

@usuario_router.get("", 
    response_model=APIResponse[List[UsuarioRead]],
    response_description="Lista de registros de usuario obtenido exitosamente",
    operation_id="usuario_find_many",
    summary="Busca varios registros en la tabla usuario",
    responses={
        200: {
            "description": "Lista de registros de usuario obtenido exitosamente",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/APIResponse_List_UsuarioRead__"
                    }
                }
            },
            "links": {
                "self": {
                    "operationId": "usuario_find_many",
                    "description": "Enlace a la consulta actual con los mismos filtros",
                    "parameters": {
                        "username": "$request.query.username",
                        "email": "$request.query.email",
                        "avatar": "$request.query.avatar",
                        "session_id": "$request.query.session_id",
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
                    "operationId": "usuario_find",
                    "description": "Enlace para acceder a un elemento específico",
                    "parameters": {
                        "username": "$response.body#/data/**/username",
                        "includes": "$request.query.includes"
                    }
                },
                "create": {
                    "operationId": "usuario_create",
                    "description": "Enlace para crear un nuevo Usuario"
                },
                "count": {
                    "operationId": "usuario_count",
                    "description": "Enlace para obtener el conteo total con los mismos filtros",
                    "parameters": {
                        "username": "$request.query.username",
                        "email": "$request.query.email",
                        "avatar": "$request.query.avatar",
                        "session_id": "$request.query.session_id",
                        "created_at": "$request.query.created_at",
                        "updated_at": "$request.query.updated_at",
                        "is_active": "$request.query.is_active",
                    }
                },
            "chats": {
            "operationId": "chat_find_many",
                    "description": "Enlace a los Chats relacionados",
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
async def usuario_find_many(
    limit: Optional[int] = Query(None, description="Número de registros a retornar. Valores positivos toman los n primeros registros, valores negativos toman los n últimos registros (requiere order_by)", gt=0),
    order_by: List[str] = Query(None, description="Lista de nombres de columnas para ordenar los resultados.⚠️ **IMPORTANTE**: los nombres de columnas deben existir, si no serán omitidas. Requerido cuando limit es negativo"),
    order: Optional[Literal["ASC", "DESC"]] = Query("ASC", description="Dirección de ordenamiento: 'ASC' para ascendente (por defecto), 'DESC' para descendente. Solo aplica si order_by está definido", regex="^(ASC|DESC)$"),
    offset: Optional[int] = Query(None, description="Número de registros a omitir desde el inicio. Útil para paginación. Debe ser un valor no negativo", ge=0),
    username: Optional[str] = Query(None, description="Filtrar por username (clave primaria)"),
    email: Optional[str] = Query(None, description='Filtrar por email. ⚠️ **IMPORTANTE**: utiliza "%email%" para hacer consultas ILIKE. Correo electrónico del usuario', min_length=1, max_length=255),
    avatar: Optional[str] = Query(None, description='Filtrar por avatar. ⚠️ **IMPORTANTE**: utiliza "%avatar%" para hacer consultas ILIKE. URL del avatar del usuario', min_length=1, max_length=255),
    session_id: Optional[str] = Query(None, description='Filtrar por session_id. ⚠️ **IMPORTANTE**: utiliza "%session_id%" para hacer consultas ILIKE. ID de la sesión activa del usuario', min_length=1, max_length=255),
    min_created_at: Optional[datetime] = Query(None, description="Fecha y hora mínima para created_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_created_at: Optional[datetime] = Query(None, description="Fecha y hora máxima para created_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    min_updated_at: Optional[datetime] = Query(None, description="Fecha y hora mínima para updated_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_updated_at: Optional[datetime] = Query(None, description="Fecha y hora máxima para updated_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    is_active: Optional[bool] = Query(None, description="Filtrar por is_active (verdadero/falso). Estado activo del usuario"),
    includes: List[str] = Query(None, description="Lista de relaciones a incluir en la respuesta para obtener datos relacionados. Especifica los nombres de las relaciones que deseas expandir"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[List[UsuarioRead]]:
    """
    ## Resumen
    Obtiene una lista de `usuarios` con filtros opcionales y soporte para paginación.
    
    Este endpoint permite realizar búsquedas flexibles aplicando filtros opcionales
    por cualquiera de los campos disponibles, con soporte completo para paginación
    mediante los parámetros limit y offset.

    ## Resultado
    En `APIResponse.data`, retorna un listado de objetos donde cada uno representa un registro de la tabla `usuario` que incluye todos sus atributos

    ## Datos
    Para cada registro en `data` se incluye:
    - **username** (str): Nombre de usuario único
    - **password** (str): Contraseña encriptada
    - **email** (str, opcional): Correo electrónico del usuario
    - **avatar** (str, opcional): URL del avatar del usuario
    - **session_id** (str, opcional): ID de la sesión activa del usuario
    - **created_at** (datetime): Fecha de creación del usuario
    - **updated_at** (datetime): Fecha de última actualización
    - **is_active** (bool): Estado activo del usuario
    
    ## Parámetros de Filtrado
    
    Todos los parámetros de filtrado son opcionales y se pueden combinar:
    - **username**: Filtrar por username
    - **email**: Filtrar por email. ⚠️ **IMPORTANTE**: utiliza "%email%" para hacer consultas ILIKE.
    - **avatar**: Filtrar por avatar. ⚠️ **IMPORTANTE**: utiliza "%avatar%" para hacer consultas ILIKE.
    - **session_id**: Filtrar por session_id. ⚠️ **IMPORTANTE**: utiliza "%session_id%" para hacer consultas ILIKE.
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
    - **chats**: lista de Chat relacionados (one-to-many)

        - **descripción**: Tabla que almacena las conversaciones del chatbot
    
    ### Ejemplos básicos:
    #### Solo datos básicos
    `usuario = GET /usuario`
    
    #### Incluir chats
    `usuario = GET /usuario?includes=chats`
    
    #### Relaciones anidadas
    Puedes incluir los datos de chats y además incluir sus propias relaciones  
    `usuario = GET /usuario?includes=chats.{nested_relation}`  
    """
    result = await api.usuario.find_many(
        limit=limit,
        offset=offset,
        order_by=order_by,
        order=order,
        username=username,
        email=email,
        avatar=avatar,
        session_id=session_id,
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
            total = await api.usuario.count(
                username=username,
                email=email,
                avatar=avatar,
                session_id=session_id,
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
        message=f"Usuarios obtenidos exitosamente"
    )

@usuario_router.get("/{username:str}", 
    response_model=APIResponse[UsuarioRead],
    response_description="Registro único de usuario obtenido exitosamente",
    operation_id="usuario_find",
    summary="Busca un registro en la tabla usuario",
    responses={
        200: {
            "description": "Registro único de usuario obtenido exitosamente",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/APIResponse_UsuarioRead_"
                    }
                }
            },
            "links": {
                "self": {
                    "operationId": "usuario_find",
                    "description": "Enlace al recurso actual",
                    "parameters": {
                        "username": "$response.body#/data/username",
                        "includes": "$request.query.includes"
                    }
                },
                "collection": {
                    "operationId": "usuario_find_many",
                    "description": "Enlace a la colección de Usuarios"
                },
                "edit": {
                    "operationId": "usuario_update",
                    "description": "Enlace para actualizar este Usuario",
                    "parameters": {
                        "username": "$response.body#/data/username",
                    }
                },
                "delete": {
                    "operationId": "usuario_delete",
                    "description": "Enlace para eliminar este Usuario",
                    "parameters": {
                        "username": "$response.body#/data/username",
                    }
                },
            "chats": {
            "operationId": "chat_find_many",
                    "description": "Enlace a los Chats relacionados",
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
                                "message": "username debe ser mayor a 0",
                                "field": "username",
                                "details": None
                            }
                        ],
                        "meta": None
                    }
                }
            }
        },
        404: {
            "description": "Usuario no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "Usuario no encontrado",
                        "errors": [
                            {
                                "code": "RECORD_NOT_FOUND",
                                "message": "Usuario no encontrado",
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
async def usuario_find(
    username: str = Path(..., description="Nombre de usuario único"),
    includes: List[str] = Query(None, description="Lista de relaciones a incluir en la respuesta para obtener datos relacionados. Especifica los nombres de las relaciones que deseas expandir"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[UsuarioRead]:
    """
    ## Resumen
    Obtiene un Usuario específico por su clave primaria.
    
    Este endpoint permite recuperar un registro individual de Usuario
    utilizando su identificador único (clave primaria). Opcionalmente puede
    incluir datos de relaciones asociadas.

    ## Resultado
    Si la consulta es exitosa, en `APIResponse.data`, retorna un objeto que representa un registro de la tabla `usuario` que incluye todos sus atributos

    Si no se encuentra el registro, devuelve un error 404 `RECORD_NOT_FOUND`.

    ## Datos
    Para cada registro en `data` se incluye:
    - **username** (str): Nombre de usuario único
    - **password** (str): Contraseña encriptada
    - **email** (str, opcional): Correo electrónico del usuario
    - **avatar** (str, opcional): URL del avatar del usuario
    - **session_id** (str, opcional): ID de la sesión activa del usuario
    - **created_at** (datetime): Fecha de creación del usuario
    - **updated_at** (datetime): Fecha de última actualización
    - **is_active** (bool): Estado activo del usuario
    
    ## Parámetros de Identificación
    
    - **username**: username del Usuario a buscar (tipo: str)
    
    ## Consulta combinada (RECOMENDADO)
    ⚠️ **IMPORTANTE**: Usa siempre el parámetro `includes` para cargar relaciones en una sola consulta y evitar múltiples llamadas al API.
    
    El parametro `includes` permite cargar relaciones asociadas a los registros.

    ### Relaciones disponibles (usar con parámetro 'includes'):
    - chats: Lista de Chat relacionados (one-to-many)
        Tabla que almacena las conversaciones del chatbot
    
    ### Uso del parámetro 'includes':
    Para cargar relaciones específicas, usa el parámetro 'includes' en la consulta:
    
    ### Ejemplos básicos:
    #### Solo datos básicos
    `usuario = GET /usuario/{username:str}`
    
    #### Incluir chats
    `usuario = GET /usuario/{username:str}?includes=chats`
    
    #### Relaciones anidadas
    Puedes incluir los datos de chats y además incluir sus propias relaciones  
    `usuario = GET /usuario/{username:str}?includes=chats.{nested_relation}`
    """
    # Validaciones básicas de entrada
    
    result = await api.usuario.find(
        username=username,
        includes=includes
    )
    
    if result is None:
        raise RecordNotFoundException("Usuario")
        
    return APIResponse.success(
        data=result,
        message="Usuario obtenido exitosamente"
    )

@usuario_router.get("/count", 
    response_model=APIResponse[int],
    response_description="Número de registros de usuario según los filtros aplicados",
    operation_id="usuario_count",
    summary="Cuenta registros en la tabla usuario",
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
async def usuario_count(
    username: Optional[str] = Query(None, description="Filtrar por username (clave primaria)"),
    email: Optional[str] = Query(None, description='Filtrar por email. ⚠️ **IMPORTANTE**: utiliza "%email%" para hacer consultas ILIKE. Correo electrónico del usuario', min_length=1, max_length=255),
    avatar: Optional[str] = Query(None, description='Filtrar por avatar. ⚠️ **IMPORTANTE**: utiliza "%avatar%" para hacer consultas ILIKE. URL del avatar del usuario', min_length=1, max_length=255),
    session_id: Optional[str] = Query(None, description='Filtrar por session_id. ⚠️ **IMPORTANTE**: utiliza "%session_id%" para hacer consultas ILIKE. ID de la sesión activa del usuario', min_length=1, max_length=255),
    min_created_at: Optional[datetime] = Query(None, description="Fecha y hora mínima para created_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_created_at: Optional[datetime] = Query(None, description="Fecha y hora máxima para created_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    min_updated_at: Optional[datetime] = Query(None, description="Fecha y hora mínima para updated_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_updated_at: Optional[datetime] = Query(None, description="Fecha y hora máxima para updated_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    is_active: Optional[bool] = Query(None, description="Filtrar por is_active (verdadero/falso). Estado activo del usuario"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[int]:
    """
    Cuenta el número de Usuarios que coinciden con los filtros.
    """
    result = await api.usuario.count(
        username=username,
        email=email,
        avatar=avatar,
        session_id=session_id,
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

@usuario_router.get("/exists", 
    response_model=APIResponse[bool],
    operation_id="usuario_exists",
    summary="Verifica existencia en la tabla usuario",
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
async def usuario_exists(
    username: Optional[str] = Query(None, description="Filtrar por username (clave primaria)"),
    email: Optional[str] = Query(None, description='Filtrar por email. ⚠️ **IMPORTANTE**: utiliza "%email%" para hacer consultas ILIKE. Correo electrónico del usuario', min_length=1, max_length=255),
    avatar: Optional[str] = Query(None, description='Filtrar por avatar. ⚠️ **IMPORTANTE**: utiliza "%avatar%" para hacer consultas ILIKE. URL del avatar del usuario', min_length=1, max_length=255),
    session_id: Optional[str] = Query(None, description='Filtrar por session_id. ⚠️ **IMPORTANTE**: utiliza "%session_id%" para hacer consultas ILIKE. ID de la sesión activa del usuario', min_length=1, max_length=255),
    min_created_at: Optional[datetime] = Query(None, description="Fecha y hora mínima para created_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_created_at: Optional[datetime] = Query(None, description="Fecha y hora máxima para created_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    min_updated_at: Optional[datetime] = Query(None, description="Fecha y hora mínima para updated_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    max_updated_at: Optional[datetime] = Query(None, description="Fecha y hora máxima para updated_at (incluida, formato: YYYY-MM-DDTHH:MM:SS)"),
    is_active: Optional[bool] = Query(None, description="Filtrar por is_active (verdadero/falso). Estado activo del usuario"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[bool]:
    """
    Verifica si existe al menos un usuario que coincida con los filtros.
    """
    result = await api.usuario.exists(
        username=username,
        email=email,
        avatar=avatar,
        session_id=session_id,
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

@usuario_router.post("", 
    response_model=APIResponse[UsuarioRead],
    status_code=201,
    operation_id="usuario_create",
    summary="Crea un registro en la tabla usuario",
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
                                "field": "password",
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
async def usuario_create(
    usuario: UsuarioCreate,
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[UsuarioRead]:
    """
    Crea un nuevo Usuario.
    """
    result = await api.usuario.create(usuario)
    
    return APIResponse.success(
        data=result,
        message="Usuario creado exitosamente"
    )

@usuario_router.patch("/{username:str}", 
    response_model=APIResponse[int],
    operation_id="usuario_update",
    summary="Actualiza un registro en la tabla usuario",
    responses={
        200: {
            "description": "Usuario actualizado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": 1,
                        "message": "Usuario actualizado exitosamente",
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
                                "message": "username debe ser mayor a 0",
                                "field": "username",
                                "details": None
                            }
                        ],
                        "meta": None
                    }
                }
            }
        },
        404: {
            "description": "Usuario no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "Usuario no encontrado",
                        "errors": [
                            {
                                "code": "RECORD_NOT_FOUND",
                                "message": "Usuario no encontrado",
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
async def usuario_update(
    username: str = Path(..., description="Nombre de usuario único"),
    values: UsuarioUpdateValues = Body(...),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[int]:
    """
    Actualiza un Usuario específico.
    """
    # Validaciones básicas de entrada
    
    # Verificar que el registro existe antes de actualizar
    existing = await api.usuario.find(
        username=username,
    )
    
    if existing is None:
        raise RecordNotFoundException("Usuario")
    
    result = await api.usuario.update(
        username=username,
        updated_values=values
    )
    
    if result == 0:
        raise RecordNotFoundException("Usuario")
        
    return APIResponse.success(
        data=result,
        message="Usuario actualizado exitosamente"
    )

@usuario_router.patch("", 
    response_model=APIResponse[int],
    operation_id="usuario_update_many",
    summary="Actualiza múltiples registros en la tabla usuario",
    responses={
        200: {
            "description": "Usuarios actualizados exitosamente",
            "content": {
                "application/json": {
                    "examples": {
                        "records_updated": {
                            "summary": "Registros actualizados",
                            "value": {
                                "status": "success",
                                "data": 5,
                                "message": "5 Usuarios actualizados exitosamente",
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
async def usuario_update_many(
    payload: UsuarioUpdate,
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[int]:
    """
    Actualiza múltiples Usuarios.
    """
    result = await api.usuario.update_many(payload)
    
    message = f"{result} Usuarios actualizados exitosamente" if result > 0 else "No se encontraron registros que coincidan con los criterios"
    
    return APIResponse.success(
        data=result,
        message=message
    )

@usuario_router.delete("/{username:str}", 
    response_model=APIResponse[int],
    operation_id="usuario_delete",
    summary="Elimina un registro en la tabla usuario",
    responses={
        200: {
            "description": "Usuario eliminado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": 1,
                        "message": "Usuario eliminado exitosamente",
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
                                "message": "username debe ser mayor a 0",
                                "field": "username",
                                "details": None
                            }
                        ],
                        "meta": None
                    }
                }
            }
        },
        404: {
            "description": "Usuario no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "data": None,
                        "message": "Usuario no encontrado",
                        "errors": [
                            {
                                "code": "RECORD_NOT_FOUND",
                                "message": "Usuario no encontrado",
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
async def usuario_delete(
    username: str = Path(..., description="Nombre de usuario único"),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> APIResponse[int]:
    """
    Elimina un Usuario por su primary key.
    """
    # Validaciones básicas de entrada
    
    # Verificar que el registro existe antes de eliminar
    existing = await api.usuario.find(
        username=username,
    )
    
    if existing is None:
        raise RecordNotFoundException("Usuario")
    
    result = await api.usuario.delete(
        username=username,
    )
    
    if result == 0:
        raise RecordNotFoundException("Usuario")
        
    return APIResponse.success(
        data=result,
        message="Usuario eliminado exitosamente"
    )
