"""
TAI-CHATBOT - Dev Application
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware 
from .routers import main_router, streaming_router
from .resources import setup_exception_handlers
from .auth import auth_router, get_current_user
from .llm import llm_manager

description = """
<details>
<summary>Mostrar diagrama ER</summary>

![ER](/database/.diagram.png)

</details>
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar LLM al iniciar la app
    await llm_manager.init()
    yield
    # Cerrar recursos al apagar la app
    await llm_manager.close()

app = FastAPI(
    title="Chatbot-API",
    version="0.1.0",
    description=description,
    lifespan=lifespan,
)

# Montar carpeta estática de diagramas
app.mount("/database", StaticFiles(directory=Path(__file__).parent / "database"), name="database")

# Incluir router de autenticación
app.include_router(auth_router)

app.include_router(streaming_router)

# Incluir router de API generada
app.include_router(
    main_router, 
    dependencies=[Depends(get_current_user)]
)

# Configurar manejadores de excepciones
setup_exception_handlers(app)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar según ambiente
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)