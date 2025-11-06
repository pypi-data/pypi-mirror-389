"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║               BACKEND-CLONE v2.0.0 - REVOLUTIONARY              ║
║                                                                  ║
║            The Most Advanced Backend Generator Ever             ║
║                                                                  ║
║   🚀 Zero-Config • 🤖 AI-Native • ☸️ Cloud-Native • 🔐 Secure   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

from setuptools import setup, find_packages
from pathlib import Path
import sys

# Minimum Python version check
if sys.version_info < (3, 9, 0):
    sys.exit("⛔ Python 3.9 yoki yuqori kerak!")

# README
README = (Path(__file__).parent / "README.md").read_text(encoding='utf-8')

# VERSION - Yagona manba!
VERSION = "2.0.0"

# Dependencies - Eng zamonaviy versiyalar!
INSTALL_REQUIRES = [
    # Core Framework
    "click>=8.1.7",
    "rich>=13.7.0",
    "typer>=0.9.0",  # Better than click!
    
    # UI & Prompts
    "questionary>=2.0.1",  # Better than inquirer!
    "textual>=0.47.0",  # TUI framework
    "prompt-toolkit>=3.0.43",
    
    # HTTP & API
    "httpx>=0.26.0",  # Modern async HTTP
    "aiohttp>=3.9.1",
    "websockets>=12.0",
    
    # AI - Multiple providers!
    "openai>=1.7.0",
    "anthropic>=0.8.0",
    "google-generativeai>=0.3.0",  # Gemini
    "cohere>=4.37",  # Cohere AI
    
    # Templates & Rendering
    "jinja2>=3.1.2",
    "pyyaml>=6.0.1",
    "toml>=0.10.2",
    "chevron>=0.14.0",  # Mustache templates
    
    # Git & Version Control
    "gitpython>=3.1.40",
    "pygit2>=1.14.0",  # Better performance
    
    # File Operations
    "pathspec>=0.12.1",
    "watchdog>=3.0.0",
    "aiofiles>=23.2.1",  # Async file ops
    
    # Data Validation
    "pydantic>=2.5.3",
    "pydantic-settings>=2.1.0",
    "jsonschema>=4.20.0",
    "cerberus>=1.3.5",
    
    # Configuration
    "python-dotenv>=1.0.0",
    "dynaconf>=3.2.4",  # Advanced config
    "configparser>=6.0.0",
    
    # CLI Utilities
    "tqdm>=4.66.1",
    "alive-progress>=3.1.5",
    "yaspin>=3.0.1",  # Spinners
    
    # Code Analysis
    "ast-grep>=0.14.0",
    "libcst>=1.1.0",  # Code transformation
    "parso>=0.8.3",  # Python parser
    
    # Security
    "cryptography>=41.0.7",
    "pycryptodome>=3.19.0",
    "keyring>=24.3.0",  # Secure credential storage
    
    # Database Drivers (all included!)
    "psycopg2-binary>=2.9.9",  # PostgreSQL
    "pymongo>=4.6.1",  # MongoDB
    "redis>=5.0.1",  # Redis
    "motor>=3.3.2",  # Async MongoDB
    "asyncpg>=0.29.0",  # Async PostgreSQL
    
    # Cloud SDKs
    "boto3>=1.34.23",  # AWS
    "google-cloud-storage>=2.14.0",  # GCP
    "azure-storage-blob>=12.19.0",  # Azure
    
    # Kubernetes & Docker
    "kubernetes>=28.1.0",
    "docker>=7.0.0",
    "docker-compose>=1.29.2",
    
    # Monitoring & Observability
    "prometheus-client>=0.19.0",
    "opentelemetry-api>=1.22.0",
    "opentelemetry-sdk>=1.22.0",
    
    # Testing
    "pytest>=7.4.4",
    "pytest-asyncio>=0.23.3",
    "pytest-cov>=4.1.0",
    "faker>=22.0.0",  # Test data generation
    
    # Utilities
    "tenacity>=8.2.3",  # Retry logic
    "cachetools>=5.3.2",  # Caching
    "python-slugify>=8.0.1",
    "semver>=3.0.2",
    "packaging>=23.2",
]

# Development dependencies
DEV_REQUIRES = [
    # Code Quality
    "black>=23.12.1",
    "ruff>=0.1.11",  # Super fast linter!
    "mypy>=1.8.0",
    "pylint>=3.0.3",
    "isort>=5.13.2",
    
    # Testing
    "pytest>=7.4.4",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.23.3",
    "pytest-mock>=3.12.0",
    "pytest-xdist>=3.5.0",  # Parallel testing
    "hypothesis>=6.96.1",  # Property-based testing
    
    # Security
    "bandit>=1.7.6",
    "safety>=3.0.1",
    "pip-audit>=2.6.3",
    
    # Documentation
    "sphinx>=7.2.6",
    "sphinx-rtd-theme>=2.0.0",
    "sphinx-click>=5.1.0",
    "myst-parser>=2.0.0",  # Markdown support
    
    # Build & Release
    "build>=1.0.3",
    "twine>=4.0.2",
    "bump2version>=1.0.1",
    
    # Performance
    "py-spy>=0.3.14",  # Profiler
    "memory-profiler>=0.61.0",
    "line-profiler>=4.1.1",
]

# All features
ALL_REQUIRES = INSTALL_REQUIRES + DEV_REQUIRES + [
    # Extra frameworks
    "uvicorn>=0.25.0",
    "gunicorn>=21.2.0",
    "hypercorn>=0.16.0",
    
    # Extra databases
    "sqlalchemy>=2.0.25",
    "alembic>=1.13.1",
    "tortoise-orm>=0.20.0",
    
    # Message Queues
    "celery>=5.3.6",
    "kombu>=5.3.5",
    "pika>=1.3.2",  # RabbitMQ
    "kafka-python>=2.0.2",
    
    # Search
    "elasticsearch>=8.11.1",
    "opensearch-py>=2.4.2",
    
    # ML/AI extras
    "langchain>=0.1.0",
    "llama-index>=0.9.42",
    "sentence-transformers>=2.2.2",
    
    # GraphQL
    "strawberry-graphql>=0.217.1",
    "graphene>=3.3",
    
    # gRPC
    "grpcio>=1.60.0",
    "grpcio-tools>=1.60.0",
]

setup(
    name="backend-clone",
    version=VERSION,
    author="Backend Clone Team",
    author_email="team@backend-clone.dev",
    description="🚀 The Most Advanced Backend Generator - v2.0.0 Revolutionary Update",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/backend-clone/backend-clone",
    project_urls={
        "Documentation": "https://docs.backend-clone.dev",
        "Source": "https://github.com/backend-clone/backend-clone",
        "Changelog": "https://github.com/backend-clone/backend-clone/blob/main/CHANGELOG.md",
        "Issues": "https://github.com/backend-clone/backend-clone/issues",
        "Discussions": "https://github.com/backend-clone/backend-clone/discussions",
        "Discord": "https://discord.gg/backend-clone",
        "Twitter": "https://twitter.com/backend_clone",
    },
    packages=find_packages(exclude=["tests*", "docs*", "examples*"]),
    classifiers=[
        # Development Status
        "Development Status :: 6 - Mature",
        
        # Audience
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
        
        # Topics
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: System :: Systems Administration",
        
        # License
        "License :: OSI Approved :: MIT License",
        
        # Python Versions
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        
        # OS
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        
        # Environment
        "Environment :: Console",
        "Environment :: Web Environment",
        
        # Framework
        "Framework :: AsyncIO",
        "Framework :: FastAPI",
        "Framework :: Django",
        "Framework :: Flask",
        
        # Natural Language
        "Natural Language :: English",
        "Natural Language :: Russian",
        "Natural Language :: Uzbek",
        
        # Typing
        "Typing :: Typed",
    ],
    keywords=[
        # Core
        "backend", "generator", "template", "scaffold", "boilerplate",
        "cli", "tool", "automation", "code-generation",
        
        # Frameworks
        "fastapi", "django", "flask", "express", "nestjs",
        "gin", "fiber", "actix", "rocket", "rails", "phoenix",
        
        # Technologies
        "rest-api", "graphql", "grpc", "websocket",
        "microservices", "serverless", "cloud-native",
        
        # DevOps
        "docker", "kubernetes", "terraform", "helm",
        "cicd", "deployment", "infrastructure",
        
        # AI
        "ai", "gpt", "claude", "gemini", "llm",
        "code-assistant", "ai-powered",
        
        # Cloud
        "aws", "gcp", "azure", "cloud",
        "vercel", "railway", "render", "fly-io",
        
        # Database
        "postgresql", "mongodb", "redis", "elasticsearch",
        "database", "orm", "prisma", "sqlalchemy",
        
        # Features
        "authentication", "authorization", "jwt", "oauth",
        "monitoring", "logging", "tracing", "security",
    ],
    python_requires=">=3.9",
    install_requires=INSTALL_REQUIRES,
    extras_require={
        "dev": DEV_REQUIRES,
        "all": ALL_REQUIRES,
        "ai": ["openai>=1.7.0", "anthropic>=0.8.0", "langchain>=0.1.0"],
        "cloud": ["boto3>=1.34.23", "google-cloud-storage>=2.14.0"],
        "k8s": ["kubernetes>=28.1.0", "docker>=7.0.0"],
        "ml": ["sentence-transformers>=2.2.2", "llama-index>=0.9.42"],
    },
    entry_points={
        "console_scripts": [
            "backend-clone=backend_clone.cli:app",
            "bc=backend_clone.cli:app",
            "backend=backend_clone.cli:app",
        ],
    },
    include_package_data=True,
    package_data={
        "backend_clone": [
            "templates/**/*",
            "templates/**/**/*",
            "templates/**/**/**/*",
            "schemas/*.json",
            "schemas/*.yaml",
            "config/*.toml",
            "config/*.yaml",
            "assets/*",
            "i18n/*.json",  # Internationalization
        ],
    },
    zip_safe=False,
    platforms=["any"],
    
    # Metadata v2.1
    options={
        "bdist_wheel": {
            "universal": False,
            "python-tag": "py39.py310.py311.py312",
        }
    },
)