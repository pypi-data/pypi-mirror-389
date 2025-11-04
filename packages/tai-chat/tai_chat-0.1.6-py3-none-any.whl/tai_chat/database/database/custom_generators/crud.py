"""
Custom CRUD generator for tai-chat project.
"""
from tai_sql.generators.crud import AsyncCRUDGenerator


class CustomAsyncCRUDGenerator(AsyncCRUDGenerator):
    """
    Custom CRUD generator that extends the base CRUDGenerator.
    """
    
    def __init__(self, output_dir = None, models_import_path = ".models", max_depth = 5, logger_name = 'tai-sql'):
        super().__init__(output_dir, models_import_path, max_depth, logger_name)


