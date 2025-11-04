"""
Custom ER Diagram generator for tai-chat project.
"""
import os
from tai_sql.generators import ERDiagramGenerator


class CustomERDiagramGenerator(ERDiagramGenerator):
    """
    Custom ER Diagram generator that extends the base ERDiagramGenerator.
    """
    def generate(self) -> str:
        """
        Genera el diagrama ER.
        
        Returns:
            str: Ruta del archivo generado
        """

        # Verificar dependencias
        self.check_dependencies()
        
        # Analizar modelos y crear entidades
        self.load_entities()
        
        # Detectar relaciones
        if self.include_relationships:
            self.load_relationships()
        
        # Crear diagrama Graphviz
        dot = self.create_diagram()
        
        # Renderizar
        output_path = os.path.join(self.config.output_dir, f'.diagram')
        dot.render(output_path, format=self.format, cleanup=True)
        
        final_path = f"{output_path}.{self.format}"
        
        return final_path