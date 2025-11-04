import sys
import click
from .model import InitCommand

@click.command()
@click.option('--name', '-n', default='chatbot', help='Nombre del proyecto a crear (por defecto: chatbot)')
def init(name: str):
    """Inicializa un nuevo proyecto tai-chat"""
    command = InitCommand(project_name=name)
    try:
        # Verificaciones previas
        command.check_poetry()
        command.check_npm()
        command.check_directory_is_available()
        command.check_virtualenv()
        
        # Creación del proyecto
        command.create_root_directory()
        command.copy_frontend()
        command.create_api_project()
        command.add_dependencies()
        command.copy_api_code()
        
        # Copiar archivos Docker
        command.copy_api_dockerfile()
        command.copy_frontend_dockerfile()
        command.copy_docker_compose()
        
        # Instalar dependencias
        command.install_api_dependencies()
        command.install_frontend_dependencies()
        command.create_project_config()
        
        # Mensaje final
        command.msg()
        
    except Exception as e:
        click.echo(f"❌ Error al inicializar el proyecto: {str(e)}", err=True)
        sys.exit(1)