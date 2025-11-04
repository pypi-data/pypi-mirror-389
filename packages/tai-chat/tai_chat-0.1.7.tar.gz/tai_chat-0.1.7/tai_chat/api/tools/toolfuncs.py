from langchain_core.tools import tool
from typing import Optional, List, Literal

from .schemas import *

# Añade aquí las herramientas que quieras exponer
# Por ejemplo:

@tool(args_schema=SumaParams)
async def suma(a: float, b: float) -> float:
    """
    Sumar dos números
    """
    return a + b

# Considera utilizar tai-sql para crear herramientas que interactúen con tu base de datos