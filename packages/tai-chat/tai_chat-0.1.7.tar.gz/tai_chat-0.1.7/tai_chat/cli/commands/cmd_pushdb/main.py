import sys
import click
import subprocess
from pathlib import Path
from tai_sql import pm
from tai_sql.cli.commands.cmd_deploy import push
from tai_sql.core.provider import Provider
from tai_sql.drivers import drivers
from sqlalchemy import create_engine, text

@click.command()
def pushdb():
    """Crea/empuja las bases de datos a un servidor remoto"""

    try:

        provider = Provider.from_environment('CONTEXT_DATABASE_URL')

        engine = create_engine(provider.url)

        driver = drivers.get_or_raise(provider.drivername)

        exists_query = driver.database_exists_query()


        with engine.connect() as conn:
            result = conn.execute(text(exists_query), {"db_name": provider.database})
            exists = result.fetchone() is not None
            if exists:
                click.echo(f"ℹ️  La base de datos '{provider.database}' ya existe")
            else:
                create_statement = driver.create_database_statement(provider.database)
                conn = conn.execution_options(isolation_level="AUTOCOMMIT")
                conn.execute(text(create_statement))
                click.echo(f"✅ Base de datos '{provider.database}' creada exitosamente")
            
            click.echo()

        database_dir = pm.find_project_root(Path(__file__).parent.parent.parent.parent)

        config = pm.load_config(database_dir)

        subprocess.run(['poetry', 'install'],
            cwd=database_dir,
            check=True, 
            capture_output=True)

        pm.set_current_schema(config.default_schema)

        push.callback(schema=None, force=True, dry_run=False, verbose=False, no_generate=False)

    except Exception as e:
        click.echo(f"❌ Error al inicializar el proyecto: {str(e)}", err=True)
        sys.exit(1)