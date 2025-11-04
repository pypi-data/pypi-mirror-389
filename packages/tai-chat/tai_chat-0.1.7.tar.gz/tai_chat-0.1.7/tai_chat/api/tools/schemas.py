from typing import Optional, List, Literal, Dict
from pydantic import BaseModel, Field


# Añade modelos de pydantic para los esquemas de las herramientas aquí
# Por ejemplo:

class SumaParams(BaseModel):
    a: float = Field(..., description="Primer número a sumar")
    b: float = Field(..., description="Segundo número a sumar")
