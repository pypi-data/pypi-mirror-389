from .toolfuncs import *

#Añadir aquí las herramientas que quieras exponer
tools = [
    suma
] 

# Alternativamente, puedes importar todas las herramientas automáticamente
# Pero es menos eficiente y más propenso a errores

# # UNCOMMENT TO USE AUTOMATIC IMPORT OF TOOLS
# from . import toolfuncs
# from langchain_core.tools.structured import BaseTool

# tools = [
#     getattr(toolfuncs, name) 
#     for name in dir(toolfuncs) 
#     if isinstance(getattr(toolfuncs, name), BaseTool)
# ]
