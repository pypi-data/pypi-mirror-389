"""
Backend Project Generator
"""
import os
import shutil
from pathlib import Path
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader
import yaml

class Generator:
    """Backend project generator"""
    
    def __init__(self, project_name: str, framework: str = "fastapi", features: Optional[List[str]] = None):
        self.project_name = project_name
        self.framework = framework.lower()
        self.features = features or []
        self.project_path = Path(project_name)
        self.backend_path = self.project_path / "backend"
        
        # Setup Jinja2 environment
        self.template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
    
    def generate(self):
        """Generate the backend project"""
        # Create project directory structure
        self._create_directories()
        
        # Generate framework-specific files
        self._generate_framework_files()
        
        # Generate common files
        self._generate_common_files()
        
        # Generate feature-specific files
        self._generate_feature_files()
        
        # Generate configuration files
        self._generate_config_files()
    
    def _create_directories(self):
        """Create project directory structure"""
        directories = [
            self.project_path,
            self.backend_path,
            self.backend_path / "src",
            self.backend_path / "src" / "api",
            self.backend_path / "src" / "models",
            self.backend_path / "src" / "services",
            self.backend_path / "src" / "utils",
            self.backend_path / "src" / "config",
            self.backend_path / "tests",
            self.backend_path / "tests" / "unit",
            self.backend_path / "tests" / "integration",
        ]
        
        # Add feature-specific directories
        if "kubernetes" in self.features:
            directories.append(self.backend_path / "k8s")
            
        if "terraform" in self.features:
            directories.append(self.backend_path / "terraform")
            
        if "monitoring" in self.features:
            directories.append(self.backend_path / "monitoring")
            
        # Create all directories
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _generate_framework_files(self):
        """Generate framework-specific files"""
        framework_templates = {
            "fastapi": {
                "main.py": "fastapi/main.py.j2",
                "requirements.txt": "fastapi/requirements.txt.j2",
                "src/api/routes/__init__.py": "fastapi/routes/__init__.py.j2",
                "src/api/routes/books.py": "fastapi/routes/books.py.j2",
                "src/models/__init__.py": "fastapi/models/__init__.py.j2",
                "src/models/book.py": "fastapi/models/book.py.j2",
            },
            "django": {
                "manage.py": "django/manage.py.j2",
                "requirements.txt": "django/requirements.txt.j2",
            },
            "flask": {
                "app.py": "flask/app.py.j2",
                "requirements.txt": "flask/requirements.txt.j2",
            }
        }
        
        templates = framework_templates.get(self.framework, framework_templates["fastapi"])
        
        for output_path, template_name in templates.items():
            if self.template_dir.exists() and (self.template_dir / template_name).exists():
                # Use template if available
                template = self.env.get_template(template_name)
                content = template.render(project_name=self.project_name, features=self.features)
            else:
                # Use default content if template not found
                content = self._get_default_content(output_path)
            
            file_path = self.backend_path / output_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
    
    def _generate_common_files(self):
        """Generate common files for all projects"""
        common_files = {
            "README.md": self._generate_readme(),
            ".gitignore": self._generate_gitignore(),
            "Dockerfile": self._generate_dockerfile(),
            "docker-compose.yml": self._generate_docker_compose(),
        }
        
        for filename, content in common_files.items():
            file_path = self.backend_path / filename
            file_path.write_text(content)
    
    def _generate_feature_files(self):
        """Generate feature-specific files"""
        if "kubernetes" in self.features:
            self._generate_kubernetes_files()
            
        if "monitoring" in self.features:
            self._generate_monitoring_files()
    
    def _generate_config_files(self):
        """Generate configuration files"""
        config_content = {
            "config.yaml": f"""
project:
  name: {self.project_name}
  framework: {self.framework}
  version: 1.0.0

server:
  host: 0.0.0.0
  port: 3000
  debug: true

database:
  url: sqlite:///./{self.project_name}.db
  pool_size: 10
  max_overflow: 20

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
""",
            ".env.example": f"""
# Server
HOST=0.0.0.0
PORT=3000
DEBUG=True

# Database
DATABASE_URL=sqlite:///./{self.project_name}.db

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET=your-jwt-secret-change-in-production
"""
        }
        
        config_dir = self.backend_path / "src" / "config"
        config_dir.mkdir(exist_ok=True)
        
        for filename, content in config_content.items():
            file_path = config_dir / filename
            file_path.write_text(content.strip())
    
    def _generate_kubernetes_files(self):
        """Generate Kubernetes configuration files"""
        k8s_dir = self.backend_path / "k8s"
        k8s_dir.mkdir(exist_ok=True)
        
        k8s_files = {
            "deployment.yaml": f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {self.project_name}
  labels:
    app: {self.project_name}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {self.project_name}
  template:
    metadata:
      labels:
        app: {self.project_name}
    spec:
      containers:
      - name: {self.project_name}
        image: {self.project_name}:latest
        ports:
        - containerPort: 3000
        envFrom:
        - configMapRef:
            name: {self.project_name}-config
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
""",
            "service.yaml": f"""
apiVersion: v1
kind: Service
metadata:
  name: {self.project_name}-service
spec:
  selector:
    app: {self.project_name}
  ports:
    - protocol: TCP
      port: 80
      targetPort: 3000
  type: LoadBalancer
""",
            "configmap.yaml": f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {self.project_name}-config
data:
  PORT: "3000"
  DEBUG: "true"
"""
        }
        
        for filename, content in k8s_files.items():
            file_path = k8s_dir / filename
            file_path.write_text(content.strip())
    
    def _generate_monitoring_files(self):
        """Generate monitoring configuration files"""
        monitoring_dir = self.backend_path / "monitoring"
        monitoring_dir.mkdir(exist_ok=True)
        
        prometheus_config = """
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['localhost:3000']
"""
        
        file_path = monitoring_dir / "prometheus.yml"
        file_path.write_text(prometheus_config.strip())
    
    def _generate_readme(self) -> str:
        """Generate README.md content"""
        return f"""# {self.project_name}

Backend project generated with [Backend Clone](https://github.com/backend-clone/backend-clone) v1.5.0

## 🚀 Quick Start

```bash
cd {self.project_name}/backend
pip install -r requirements.txt
python main.py
```

## 📁 Project Structure

```
{self.project_name}/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   ├── utils/
│   │   └── config/
│   ├── tests/
│   ├── requirements.txt
│   └── main.py
└── README.md
```

## 🛠️ Features

- Framework: {self.framework}
- Features: {', '.join(self.features) if self.features else 'None'}

## 📦 Requirements

- Python 3.8+
- See `requirements.txt` for dependencies

## 🧪 Testing

```bash
pytest tests/
```

## 🐳 Docker

```bash
docker build -t {self.project_name} .
docker run -p 3000:3000 {self.project_name}
```
"""
    
    def _generate_gitignore(self) -> str:
        """Generate .gitignore content"""
        return """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Django stuff:
*.log
local_settings.py
db.sqlite3

# Flask stuff:
instance/
.webassets-cache

# FastAPI stuff:
*.db

# PyInstaller
*.manifest
*.spec

# dotenv
.env

# Virtual environment
venv/
ENV/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Docker
.dockerignore
"""
    
    def _generate_dockerfile(self) -> str:
        """Generate Dockerfile content"""
        return """
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 3000

CMD ["python", "main.py"]
"""
    
    def _generate_docker_compose(self) -> str:
        """Generate docker-compose.yml content"""
        return f"""
version: '3.8'

services:
  {self.project_name}:
    build: .
    ports:
      - "3000:3000"
    environment:
      - PORT=3000
      - DEBUG=True
    volumes:
      - .:/app
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB={self.project_name}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
"""
    
    def _get_default_content(self, filename: str) -> str:
        """Get default content for a file"""
        default_contents = {
            "main.py": f"""
from fastapi import FastAPI

app = FastAPI(title="{self.project_name}")

@app.get("/")
def read_root():
    return {{"message": "Welcome to {self.project_name}!"}}

@app.get("/health")
def health_check():
    return {{"status": "healthy"}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
""",
            "requirements.txt": """
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0
""",
            "README.md": self._generate_readme(),
        }
        
        return default_contents.get(filename, f"# {filename}\n\nGenerated by Backend Clone")