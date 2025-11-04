import subprocess
import sys
import os
import shutil
from pathlib import Path
import click

class InitCommand:

    def __init__(self, project_name: str = 'chatbot'):
        self.project_name = project_name
        self.project_root = Path(project_name)
        self.api_dir = self.project_root / 'api'
        self.app_dir = self.project_root / 'app'
        self.front_dir = self.app_dir / 'front'
    
    @property
    def project_snake_case(self) -> str:
        """Retorna el nombre del proyecto en snake_case"""
        return self.project_name.replace('-', '_')
    
    def check_poetry(self):
        """Verifica que Poetry esté instalado y disponible"""
        try:
            subprocess.run(['poetry', '--version'], check=True, capture_output=True)
            click.echo("✅ Poetry encontrado")
        except (subprocess.CalledProcessError, FileNotFoundError):
            click.echo("❌ Error: Poetry no está instalado o no está en el PATH", err=True)
            click.echo("Instala Poetry desde: https://python-poetry.org/docs/#installation")
            sys.exit(1)
    
    def check_npm(self):
        """Verifica que npm esté instalado y disponible"""
        try:
            subprocess.run(['npm', '--version'], check=True, capture_output=True)
            click.echo("✅ npm encontrado")
        except (subprocess.CalledProcessError, FileNotFoundError):
            click.echo("❌ Error: npm no está instalado o no está en el PATH", err=True)
            click.echo("Instala Node.js y npm desde: https://nodejs.org/")
            sys.exit(1)
    
    def check_directory_is_available(self):
        """Verifica que el directorio del proyecto no exista"""
        if self.project_root.exists():
            click.echo(f"❌ Error: el directorio '{self.project_name}' ya existe", err=True)
            sys.exit(1)
        click.echo(f"✅ Directorio '{self.project_name}' disponible")
    
    def create_root_directory(self):
        """Crea el directorio raíz del proyecto"""
        try:
            self.project_root.mkdir(parents=True, exist_ok=False)
            click.echo(f"✅ Directorio raíz '{self.project_name}' creado")
        except FileExistsError:
            click.echo(f"❌ Error: el directorio '{self.project_name}' ya existe", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Error al crear directorio raíz: {e}", err=True)
            sys.exit(1)
    
    def copy_frontend(self):
        """Copia la carpeta front a app/front"""
        try:
            # Obtener la ruta de la carpeta front del proyecto actual
            current_file = Path(__file__).resolve()
            tai_chat_root = current_file.parents[3]  # Navegar hasta tai_chat/
            source_front = tai_chat_root / 'front'
            
            if not source_front.exists():
                click.echo(f"❌ Error: no se encontró la carpeta front en {source_front}", err=True)
                sys.exit(1)
            
            # Crear carpeta app si no existe
            self.app_dir.mkdir(parents=True, exist_ok=True)
            
            # Copiar toda la carpeta front a app/front
            shutil.copytree(source_front, self.front_dir)
            click.echo(f"✅ Frontend copiado")
            
        except Exception as e:
            click.echo(f"❌ Error al copiar frontend: {e}", err=True)
            sys.exit(1)
    
    def check_virtualenv(self):
        """Verifica que el entorno virtual de Poetry esté activo"""
        if 'VIRTUAL_ENV' not in os.environ:
            click.echo("⚠️  Advertencia: No hay entorno virtual activo", err=True)
            click.echo("   Recomendado: crear uno con 'pyenv virtualenv <env_name>' y asignarlo con 'pyenv local <env_name>'", err=True)
            # No salir, solo advertir
    
    def create_api_project(self):
        """Crea el proyecto Poetry para la API"""
        click.echo(f"🚀 Creando proyecto API con Poetry...")
        
        try:
            # Crear proyecto con poetry new
            subprocess.run(['poetry', 'new', '--flat', '--python', '<4.0,>=3.10', 'api'], 
                        check=True, 
                        capture_output=True)
            subprocess.run(['poetry', 'install'],
                        cwd=self.project_root / 'api',
                        check=True, 
                        capture_output=True)
            
            click.echo(f"✅ Proyecto API creado en {self.api_dir}")
        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Error al crear proyecto API: {e}", err=True)
            sys.exit(1)
    
    def create_project(self):
        """Crea el proyecto base con Poetry (método legacy - se mantiene por compatibilidad)"""
        # Este método se mantiene por compatibilidad pero ahora usa create_api_project
        self.create_api_project()

    def add_dependencies(self):
        """Añade las dependencias necesarias al proyecto API"""
        click.echo("📦 Añadiendo dependencias al proyecto API...")
        
        # Dependencias básicas
        basic_dependencies = [
            'fastapi', 
            'uvicorn[standard]', 
            'asyncpg',
            'sqlalchemy', 
            'psycopg2-binary', 
            'pydantic',
            'pydantic-settings',
            'python-multipart',
            'python-jose[cryptography]',
            'passlib[bcrypt]',
            'tai-alphi',
            'langchain-openai',
            'langgraph-checkpoint-postgres'
        ]
        
        # Dependencias con versiones prerelease que requieren poetry add --allow-prereleases
        prerelease_dependencies = [
            'langchain==1.0.0a4',
            'langgraph==1.0.0a3'
        ]
        
        # Añadir dependencias básicas
        for dep in basic_dependencies:
            try:
                subprocess.run(['poetry', 'add', dep], 
                            cwd=self.api_dir,
                            check=True, 
                            capture_output=True)
                click.echo(f"   ✅ {dep} añadido")
            except subprocess.CalledProcessError as e:
                click.echo(f"   ❌ Error al añadir dependencia {dep}: {e}", err=True)
                sys.exit(1)
        
        # Añadir dependencias prerelease con flag especial
        for dep in prerelease_dependencies:
            try:
                subprocess.run(['poetry', 'add', '--allow-prereleases', dep], 
                            cwd=self.api_dir,
                            check=True, 
                            capture_output=True)
                click.echo(f"   ✅ {dep} añadido (prerelease)")
            except subprocess.CalledProcessError as e:
                click.echo(f"   ❌ Error al añadir dependencia prerelease {dep}: {e}", err=True)
                sys.exit(1)
    
    def copy_api_code(self):
        """Sobrescribe la carpeta api interna con nuestra carpeta api"""
        try:
            # Obtener la ruta de la carpeta api del proyecto actual
            current_file = Path(__file__).resolve()
            tai_chat_root = current_file.parents[2]  # Navegar hasta tai_chat/
            source_api = tai_chat_root.parent / 'api'  # api está en el nivel superior
            
            if not source_api.exists():
                click.echo(f"❌ Error: no se encontró la carpeta api en {source_api}", err=True)
                sys.exit(1)
            
            # Eliminar la carpeta api generada por poetry
            generated_api = self.api_dir / 'api'
            if generated_api.exists():
                shutil.rmtree(generated_api)
            
            # Copiar nuestra carpeta api
            shutil.copytree(source_api, generated_api)
            click.echo(f"✅ Código API copiado desde {source_api}")
            
        except Exception as e:
            click.echo(f"❌ Error al copiar código API: {e}", err=True)
            sys.exit(1)
    
    def copy_api_dockerfile(self):
        """Copia el dockerfile y archivos relacionados de la API al directorio api/"""
        try:
            # Obtener la ruta de los archivos Docker de la API
            current_file = Path(__file__).resolve()
            tai_chat_root = current_file.parents[3]  # Navegar hasta tai_chat/
            source_docker_api = tai_chat_root / 'docker' / 'api'
            
            if not source_docker_api.exists():
                click.echo(f"❌ Error: no se encontró la carpeta docker/api en {source_docker_api}", err=True)
                sys.exit(1)
            
            # Copiar dockerfile y entrypoint.sh
            dockerfile_src = source_docker_api / 'dockerfile'
            entrypoint_src = source_docker_api / 'entrypoint.sh'
            
            if dockerfile_src.exists():
                shutil.copy2(dockerfile_src, self.api_dir / 'dockerfile')
                click.echo(f"✅ Dockerfile de API copiado")
            
            if entrypoint_src.exists():
                shutil.copy2(entrypoint_src, self.api_dir / 'entrypoint.sh')
                click.echo(f"✅ Entrypoint de API copiado")
            
            # Crear archivo sshd_config básico
            sshd_config_content = """Port 			2222
ListenAddress 		0.0.0.0
LoginGraceTime 		180
X11Forwarding 		yes
Ciphers aes128-cbc,3des-cbc,aes256-cbc,aes128-ctr,aes192-ctr,aes256-ctr
MACs hmac-sha1,hmac-sha1-96
StrictModes 		yes
SyslogFacility 		DAEMON
PasswordAuthentication 	yes
PermitEmptyPasswords 	no
PermitRootLogin 	yes
Subsystem sftp internal-sftp
"""
            sshd_config_path = self.api_dir / 'sshd_config'
            sshd_config_path.write_text(sshd_config_content)
            click.echo(f"✅ Configuración SSH creada")
            
        except Exception as e:
            click.echo(f"❌ Error al copiar archivos Docker de la API: {e}", err=True)
            sys.exit(1)
    
    def install_api_dependencies(self):
        """Instala las dependencias del proyecto API"""
        try:
            click.echo("📦 Instalando dependencias de la API...")
            subprocess.run(['poetry', 'install'],
                        cwd=self.api_dir,
                        check=True, 
                        capture_output=True)
            click.echo("✅ Dependencias de la API instaladas")
        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Error al instalar dependencias de la API: {e}", err=True)
            sys.exit(1)
    
    def install_frontend_dependencies(self):
        """Instala las dependencias del frontend"""
        try:
            click.echo("📦 Instalando dependencias del frontend...")
            subprocess.run(['npm', 'install'],
                        cwd=self.front_dir,
                        check=True, 
                        capture_output=True)
            click.echo("✅ Dependencias del frontend instaladas")
        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Error al instalar dependencias del frontend: {e}", err=True)
            sys.exit(1)
    
    def copy_frontend_dockerfile(self):
        """Copia el dockerfile del frontend a la carpeta app/"""
        try:
            # Obtener la ruta de los archivos Docker del frontend
            current_file = Path(__file__).resolve()
            tai_chat_root = current_file.parents[3]  # Navegar hasta tai_chat/
            source_docker_front = tai_chat_root / 'docker' / 'front'
            
            if not source_docker_front.exists():
                click.echo(f"❌ Error: no se encontró la carpeta docker/front en {source_docker_front}", err=True)
                sys.exit(1)
            
            # Copiar dockerfile y .dockerignore
            dockerfile_src = source_docker_front / 'dockerfile'
            dockerignore_src = source_docker_front / '.dockerignore'
            entrypoint_src = source_docker_front / 'entrypoint.sh'
            
            if dockerfile_src.exists():
                shutil.copy2(dockerfile_src, self.app_dir / 'dockerfile')
                click.echo(f"✅ Dockerfile del frontend copiado")
            
            if dockerignore_src.exists():
                shutil.copy2(dockerignore_src, self.app_dir / '.dockerignore')
                click.echo(f"✅ .dockerignore del frontend copiado")
            
            if entrypoint_src.exists():
                shutil.copy2(entrypoint_src, self.app_dir / 'entrypoint.sh')
                click.echo(f"✅ Entrypoint del frontend copiado")
            
        except Exception as e:
            click.echo(f"❌ Error al copiar archivos Docker del frontend: {e}", err=True)
            sys.exit(1)
    
    def copy_docker_compose(self):
        """Copia el docker-compose.yaml a la carpeta raíz del proyecto"""
        try:
            # Obtener la ruta del archivo docker-compose.yaml
            current_file = Path(__file__).resolve()
            tai_chat_root = current_file.parents[3]  # Navegar hasta tai_chat/
            source_docker_compose = tai_chat_root / 'docker' / 'docker-compose.yaml'
            
            if not source_docker_compose.exists():
                click.echo(f"❌ Error: no se encontró el archivo docker-compose.yaml en {source_docker_compose}", err=True)
                sys.exit(1)
            
            # Copiar docker-compose.yaml
            shutil.copy2(source_docker_compose, self.project_root / 'docker-compose.yaml')
            click.echo(f"✅ docker-compose.yaml copiado")
            
        except Exception as e:
            click.echo(f"❌ Error al copiar docker-compose.yaml: {e}", err=True)
            sys.exit(1)
    
    def create_project_config(self) -> None:
        """Crea archivos de configuración del proyecto tai-chat"""
        try:
            # Crear README.md
            readme_content = f"""# {self.project_name}

## Estructura del proyecto

- `api/` - Backend FastAPI
- `app/front/` - Frontend Svelte
- `docker-compose.yaml` - Configuración de Docker

## Comandos de desarrollo
Puedes levantar ambos servicios en local o en docker

### Levantar servicios en local (DEV)

#### FULL
```bash
tai-chat dev
```

#### API
```bash
tai-chat dev api
```

#### Frontend
```bash
tai-chat dev front
```

### Levantar servicios en docker (RUN)

#### FULL
```bash
tai-chat run
```

#### API
```bash
tai-chat run api
```

#### Frontend
```bash
tai-chat run front

## Variables de entorno

```bash
cp {self.project_name}/.env.example {self.project_name}/.env
```

`.env`
```
# DEV/PROD
MAIN_DATABASE_URL=postgresql://user:password@host:5432/dbname
CHATBOT_DATABASE_URL=postgresql://user:password@host:5432/chatbotdb
CONTEXT_DATABASE_URL=postgresql://user:password@host:5432/context-chatbotdb
SECRET_KEY=superclavesecretade32caracteres
API_KEY=tu-api-key-aqui

# PROD
VITE_API_URL=https://chatbotapi.azurewebsites.com
```
"""
            
            readme_path = self.project_root / 'README.md'
            readme_path.write_text(readme_content)
            
            # Crear .env.example
            env_example_content = """
# DEV/PROD
MAIN_DATABASE_URL=postgresql://user:password@host:5432/dbname
CHATBOT_DATABASE_URL=postgresql://user:password@host:5432/chatbotdb
CONTEXT_DATABASE_URL=postgresql://user:password@host:5432/context-chatbotdb
SECRET_KEY=superclavesecretade32caracteres
API_KEY=tu-api-key-aqui

# PROD
VITE_API_URL=https://chatbotapi.azurewebsites.com
"""
            
            env_example_path = self.project_root / '.env.example'
            env_example_path.write_text(env_example_content)
            
            click.echo("✅ Archivos de configuración creados")
            
        except Exception as e:
            click.echo(f"❌ Error al crear configuración del proyecto: {e}", err=True)
            sys.exit(1)

    def msg(self):
        """Muestra el mensaje de éxito y next steps con información del proyecto"""
        click.echo()
        click.echo(f'🎉 ¡Proyecto "{self.project_name}" creado exitosamente!')
        
        # Mostrar información del proyecto
        click.echo()
        click.echo("📋 Información del proyecto:")
        click.echo(f"   Nombre: {self.project_name}")
        click.echo(f"   API: {self.api_dir}")
        click.echo(f"   Frontend: {self.front_dir}")
        
        click.echo()
        click.echo("📋 Próximos pasos:")
        click.echo("   1. Configurar variables de entorno:")
        click.echo(f"      cp {self.project_name}/.env.example {self.project_name}/.env")
        click.echo("      # Editar .env con tus configuraciones")
        click.echo()
        click.echo("   2. Iniciar el desarrollo:")
        click.echo(f"      tai-chat dev")
        click.echo()
        click.echo("   3. O usando Docker:")
        click.echo("      tai-chat run")
        click.echo()
        click.echo("🔧 URLs de desarrollo:")
        click.echo("   Frontend: http://localhost:4713")
        click.echo("   API: http://localhost:8000")
        click.echo("   API Docs: http://localhost:8000/docs")
        click.echo()
        click.echo("🔗 Documentación: https://github.com/triplealpha-innovation/tai-chat")
        
