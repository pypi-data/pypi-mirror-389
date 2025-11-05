# Zenive Template System User Guide

## Overview

The Zenive template system allows you to quickly create new projects with predefined templates, similar to `npx create-next-app` or `create-react-app`. It provides three FastAPI templates of increasing complexity and is designed to be extensible for future templates.

## Quick Start

### Creating a New Project

```bash
# Interactive template selection
zenive create my-api

# Use specific template
zenive create my-api -t fastapi-minimal

# List available templates
zenive create --list-templates

# Get template information
zenive create --template-info fastapi-moderate
```

### Available Templates

| Template | Complexity | Description | Use Case |
|----------|------------|-------------|----------|
| `fastapi-minimal` | Minimal | Basic FastAPI app with simple structure | Learning, prototypes, simple APIs |
| `fastapi-moderate` | Moderate | Auth, database, API versioning, Docker | Production apps, small teams |
| `fastapi-industry` | Industry | Everything + monitoring, K8s, CI/CD | Enterprise, large teams, scale |

## Template Features

### FastAPI Minimal Template

**Perfect for**: Learning FastAPI, quick prototypes, simple APIs

**Includes**:
- Basic FastAPI application with example routes
- Pydantic models for request/response validation
- Environment-based configuration
- Simple error handling and logging
- Basic project structure
- Requirements.txt with minimal dependencies
- README with setup instructions

**Project Structure**:
```
my-project/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── models.py            # Pydantic models
│   └── config.py            # Configuration
├── tests/
│   ├── __init__.py
│   └── test_main.py         # Basic tests
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### FastAPI Moderate Template

**Perfect for**: Production applications, small to medium teams

**Includes everything from Minimal plus**:
- **Authentication & Authorization**: JWT tokens, user registration/login, password hashing, RBAC
- **Database Integration**: SQLAlchemy 2.0, Alembic migrations, PostgreSQL support, CRUD operations
- **API Structure**: Versioned APIs (v1), router organization, dependency injection
- **Development Tools**: Docker & Docker Compose, environment configs, basic testing
- **Middleware**: CORS, request logging, error handling

**Additional Structure**:
```
my-project/
├── app/
│   ├── api/v1/              # Versioned API routes
│   ├── core/                # Config, security, database
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── crud/                # Database operations
│   └── middleware/          # Custom middleware
├── migrations/              # Alembic migrations
├── deployment/              # Docker files
└── ...
```### Fa
stAPI Industry Template

**Perfect for**: Enterprise applications, large teams, production at scale

**Includes everything from Moderate plus**:
- **Advanced Performance**: Redis caching, rate limiting, Celery task queue, connection pooling
- **Monitoring & Observability**: Prometheus metrics, Grafana dashboards, structured logging, Sentry error tracking
- **Security**: Security headers, input sanitization, OWASP compliance, secrets management
- **DevOps & Deployment**: Kubernetes manifests, Helm charts, Terraform infrastructure, CI/CD pipelines
- **Testing & Quality**: Comprehensive test suite, load testing, code coverage, pre-commit hooks, type checking

**Additional Structure**:
```
my-project/
├── app/
│   ├── worker/              # Celery tasks
│   ├── middleware/          # Advanced middleware
│   └── utils/               # Utilities
├── deployment/
│   ├── k8s/                 # Kubernetes manifests
│   ├── terraform/           # Infrastructure as code
│   └── docker/              # Docker configurations
├── monitoring/
│   ├── grafana/             # Dashboards
│   └── prometheus/          # Metrics config
├── scripts/                 # Deployment scripts
├── docs/                    # Documentation
└── .github/workflows/       # CI/CD pipelines
```

## Using Templates

### Interactive Project Creation

When you run `zenive create my-project`, you'll be guided through:

1. **Template Selection**: Choose from available templates
2. **Project Preferences**: Configure installation options
3. **Template Customization**: Set template-specific variables
4. **Creation Summary**: Review before creation
5. **Project Setup**: Automatic file creation and dependency installation

### Template Customization Options

Templates support customization through variables:

```bash
# Example customization prompts for moderate template
Database Settings:
  Database name (my_project_db): 
  Database user (postgres): 
  Database password: [hidden]

Authentication Settings:
  JWT secret key: [auto-generated]
  Token expiration (24): 

Deployment Settings:
  Application port (8000): 
  Docker registry: 
```

### Project Preferences

Configure how your project is set up:

- **Install dependencies**: Automatically run `pip install -r requirements.txt`
- **Create virtual environment**: Set up isolated Python environment
- **Initialize git repository**: Create git repo with initial commit
- **Include development tools**: Add linting, formatting, pre-commit hooks

## Command Reference

### Create Command

```bash
zenive create [PROJECT_NAME] [OPTIONS]
```

**Options**:
- `-t, --template TEXT`: Specify template name
- `--list-templates`: Show available templates
- `--template-info TEXT`: Show detailed template information
- `--no-deps`: Skip dependency installation
- `--no-venv`: Skip virtual environment creation

**Examples**:
```bash
# Interactive creation
zenive create my-api

# Specific template
zenive create my-api -t fastapi-minimal

# Skip dependency installation
zenive create my-api -t fastapi-moderate --no-deps

# List all templates
zenive create --list-templates

# Get template details
zenive create --template-info fastapi-industry
```

### Validate Command

```bash
zenive validate [OPTIONS]
```

**Options**:
- `-t, --template TEXT`: Validate specific template
- `-a, --all`: Validate all templates
- `--test`: Run comprehensive tests
- `--fix`: Attempt to fix validation issues

**Examples**:
```bash
# Validate all templates
zenive validate --all

# Validate specific template
zenive validate -t fastapi-minimal

# Run comprehensive tests
zenive validate --all --test
```

## Working with Created Projects

### Getting Started

After creating a project:

1. **Navigate to project directory**:
   ```bash
   cd my-project
   ```

2. **Activate virtual environment** (if created):
   ```bash
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies** (if not auto-installed):
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the API**:
   - Application: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

### Development Workflow

#### For Minimal Template

```bash
# Run development server
uvicorn app.main:app --reload

# Run tests
pytest

# Add new routes in app/main.py
# Add models in app/models.py
# Update config in app/config.py
```

#### For Moderate Template

```bash
# Run with Docker Compose
docker-compose up -d

# Run database migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Add new table"

# Run tests
pytest

# Access services:
# - API: http://localhost:8000
# - Database: localhost:5432
# - Redis: localhost:6379
```

#### For Industry Template

```bash
# Local development
docker-compose up -d

# Production deployment
kubectl apply -f deployment/k8s/

# Infrastructure setup
cd deployment/terraform
terraform init
terraform plan
terraform apply

# Monitoring
# - Grafana: http://localhost:3000
# - Prometheus: http://localhost:9090
```

## Project Configuration

Created projects include a `.zen/config.yaml` file that tracks:

```yaml
name: my-project
version: 1.0.0
description: Project created from fastapi-moderate template
project:
  name: my-project
  created_from_template: fastapi-moderate
  template_version: 1.0.0
  template_variables:
    project_name: my-project
    database_name: my_project_db
    # ... other variables
  created_at: 2024-01-15T10:30:00
template:
  name: fastapi-moderate
  version: 1.0.0
  complexity: moderate
  category: web
  extends: fastapi-minimal
components: {}  # For future component installations
structure:
  models: app/models
  schemas: app/schemas
  api: app/api
  # ... other paths
```

This configuration:
- Tracks the template used to create the project
- Stores template variables for reference
- Maintains project structure mapping
- Enables future component installations
- Provides project metadata

## Troubleshooting

### Common Issues

#### Template Not Found
```bash
Error: Template 'my-template' not found
```
**Solution**: Use `zenive create --list-templates` to see available templates.

#### Directory Already Exists
```bash
Error: Directory 'my-project' already exists
```
**Solution**: Use a different name or remove the existing directory.

#### Dependency Installation Failed
```bash
Warning: Failed to install dependencies
```
**Solution**: 
1. Activate virtual environment: `source venv/bin/activate`
2. Install manually: `pip install -r requirements.txt`
3. Check Python version compatibility

#### Permission Errors
```bash
Error: Permission denied when creating files
```
**Solution**: 
1. Check directory permissions
2. Run with appropriate user permissions
3. Ensure target directory is writable

### Getting Help

1. **Check command help**:
   ```bash
   zenive create --help
   zenive validate --help
   ```

2. **Validate templates**:
   ```bash
   zenive validate --all
   ```

3. **Check project configuration**:
   ```bash
   cat .zen/config.yaml
   ```

4. **View template details**:
   ```bash
   zenive create --template-info fastapi-moderate
   ```

## Best Practices

### Choosing the Right Template

- **Use Minimal** for:
  - Learning FastAPI
  - Quick prototypes
  - Simple APIs with few endpoints
  - Personal projects

- **Use Moderate** for:
  - Production applications
  - APIs requiring authentication
  - Database-backed applications
  - Small to medium teams

- **Use Industry** for:
  - Enterprise applications
  - High-scale production systems
  - Applications requiring monitoring
  - Large development teams
  - Complex deployment requirements

### Project Organization

1. **Follow template structure**: Don't reorganize the generated structure unnecessarily
2. **Use provided patterns**: Leverage the CRUD, schema, and router patterns
3. **Extend gradually**: Start with a simpler template and add complexity as needed
4. **Document changes**: Update README.md with your specific setup instructions

### Development Tips

1. **Environment Variables**: Always use `.env` files for configuration
2. **Database Migrations**: Use Alembic for all database schema changes
3. **Testing**: Write tests as you develop, don't leave it for later
4. **Docker**: Use Docker Compose for consistent development environments
5. **Documentation**: Keep API documentation up to date using FastAPI's automatic docs

## Next Steps

After creating your project:

1. **Customize for your needs**: Modify the generated code to fit your requirements
2. **Add components**: Use `zenive add` to install additional components
3. **Set up CI/CD**: Configure continuous integration and deployment
4. **Monitor and scale**: Implement monitoring and scaling strategies
5. **Contribute back**: Share useful patterns and improvements with the community

For more advanced topics, see:
- [Template Development Guide](TEMPLATE_DEVELOPMENT.md)
- [API Documentation](API_REFERENCE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)