"""
Custom model generators for tai-chat.
"""
import os
from pathlib import Path
from tai_sql import pm
from tai_sql.generators import ModelsGenerator


class CustomModelsGenerator(ModelsGenerator):
    """
    Custom model generator that extends the base ModelsGenerator.
    """

    def generate(self) -> str:
        """
        Genera un único archivo con todos los modelos SQLAlchemy.
        
        Returns:
            Ruta al archivo generado
        """

        self.validate_encryption_setup()

        # Preparar datos para la plantilla
        models_data = []
        
        # Analizar cada modelo y recopilar información
        for model in self.models:
            model_info = model.info()
            models_data.append(model_info)
        
        # Cargar la plantilla
        template = self.jinja_env.get_template('__init__.py.jinja2')
        
        # Renderizar la plantilla
        code = template.render(
            imports=self.imports,
            models=models_data,
            is_postgres=pm.db.provider.drivername == 'postgresql',
            schema_name=pm.db.schema_name,
            secret_key_name=pm.db.secret_key_name,
            has_encrypted_columns=self.has_encrypted_columns
        )
        
        # Escribir el archivo generado
        path = os.path.join(Path(self.config.output_dir), 'models.py')

        with open(path, 'w') as f:
            f.write(code)
        
        return self.file_path
