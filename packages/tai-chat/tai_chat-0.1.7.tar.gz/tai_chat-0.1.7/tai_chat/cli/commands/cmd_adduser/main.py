import click
from .chatbot.crud.syn import chatbot_api, UsuarioCreate

@click.command()
def add_user():
    """Añade un nuevo usuario al sistema"""
    
    # Solicitar username al usuario
    username = click.prompt('Ingrese el nombre de usuario', type=str)
    
    # Solicitar password al usuario (oculto por seguridad)
    password = click.prompt('Ingrese la contraseña', type=str, hide_input=True, confirmation_prompt=True)

    # Comprobar si existe el usuario
    existing_user = chatbot_api.usuario.find(username)

    if existing_user:
        click.echo(f"❌ El usuario '{username}' ya existe.", err=True)
        return
    
    chatbot_api.usuario.create(
        UsuarioCreate(
            username=username,
            password=password
        )
    )
