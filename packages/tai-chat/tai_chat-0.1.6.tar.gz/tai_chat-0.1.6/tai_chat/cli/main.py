import click
from .commands import (
    init,
    pushdb,
    add_user
)

@click.group()
def cli():
    """CLI para tai-chat: descubre tus datos con LLMs."""
    pass

cli.add_command(init)
cli.add_command(pushdb)
cli.add_command(add_user)
# cli.add_command(deploy)

if __name__ == '__main__':
    cli()