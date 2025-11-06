# Template System Troubleshooting Guide

## Common Issues and Solutions

### Template Creation Issues

#### Issue: Template Not Found
```
Error: Template 'my-template' not found in registry
```

**Possible Causes:**
- Template name is misspelled
- Template is not registered in the system
- Template directory is missing or incorrectly structured

**Solutions:**
1. **Check available templates:**
   ```bash
   zenive create --list-templates
   ```

2. **Verify template name spelling:**
   ```bash
   # Correct names
   zenive create my-project -t fastapi-minimal
   zenive create my-project -t fastapi-moderate
   zenive create my-project -t fastapi-industry
   ```

3. **Check template directory exists:**
   ```bash
   ls zen/templates/
   # Should show: fastapi-minimal, fastapi-moderate, fastapi-industry
   ```

4. **Validate template structure:**
   ```bash
   zenive validate -t template-name
   ```

#### Issue: Directory Already Exists
```
Error: Directory 'my-project' already exists
```

**Solutions:**
1. **Use a different project name:**
   ```bash
   zenive create my-project-v2 -t fastapi-minimal
   ```

2. **Remove existing directory:**
   ```bash
   rm -rf my-project
   zenive create my-project -t fastapi-minimal
   ```

3. **Use force overwrite (if supported):**
   ```bash
   zenive create my-project -t fastapi-minimal --force
   ```

#### Issue: Permission Denied
```
Error: Permission denied when creating files
```

**Solutions:**
1. **Check directory permissions:**
   ```bash
   ls -la
   # Ensure you have write permissions in current directory
   ```

2. **Change to writable directory:**
   ```bash
   cd ~/projects
   zenive create my-project -t fastapi-minimal
   ```

3. **Fix permissions:**
   ```bash
   chmod 755 .
   ```

### Dependency Installation Issues

#### Issue: Dependency Installation Failed
```
Warning: Failed to install dependencies
Error: Could not install packages due to an EnvironmentError
```

**Solutions:**
1. **Check Python version:**
   ```bash
   python --version
   # Ensure Python 3.8+ is installed
   ```

2. **Update pip:**
   ```bash
   python -m pip install --upgrade pip
   ```

3. **Install dependencies manually:**
   ```bash
   cd my-project
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

4. **Check for conflicting packages:**
   ```bash
   pip check
   ```

5. **Use different Python version:**
   ```bash
   python3.9 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

#### Issue: Virtual Environment Creation Failed
```
Error: Failed to create virtual environment
```

**Solutions:**
1. **Install venv module:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-venv
   
   # CentOS/RHEL
   sudo yum install python3-venv
   
   # macOS (if using system Python)
   # Usually included, try updating Python
   ```

2. **Use alternative virtual environment tools:**
   ```bash
   # Using virtualenv
   pip install virtualenv
   virtualenv venv
   
   # Using conda
   conda create -n my-project python=3.9
   conda activate my-project
   ```

3. **Skip virtual environment creation:**
   ```bash
   zenive create my-project -t fastapi-minimal --no-venv
   ```

### Template Validation Issues

#### Issue: Template Validation Failed
```
Error: Template validation failed with errors
```

**Solutions:**
1. **Run detailed validation:**
   ```bash
   zenive validate -t template-name
   ```

2. **Check template.json syntax:**
   ```bash
   # Validate JSON syntax
   python -m json.tool zen/templates/template-name/template.json
   ```

3. **Verify file paths:**
   ```bash
   # Check that all files referenced in template.json exist
   ls zen/templates/template-name/
   ```

4. **Fix common validation errors:**
   - Ensure all required fields are present in template.json
   - Check that file paths are relative and don't contain '..'
   - Verify dependency format (package>=version)
   - Ensure template variables are properly defined

#### Issue: Template Inheritance Error
```
Error: Template inheritance resolution failed
```

**Solutions:**
1. **Check parent template exists:**
   ```bash
   zenive validate -t parent-template-name
   ```

2. **Verify inheritance chain:**
   ```bash
   # Check template.json for 'extends' field
   grep -n "extends" zen/templates/template-name/template.json
   ```

3. **Avoid circular inheritance:**
   - Template A extends Template B
   - Template B should not extend Template A

### Runtime Issues

#### Issue: Application Won't Start
```
Error: ModuleNotFoundError: No module named 'fastapi'
```

**Solutions:**
1. **Activate virtual environment:**
   ```bash
   cd my-project
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. **Install missing dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Check Python path:**
   ```bash
   which python
   pip list | grep fastapi
   ```

#### Issue: Import Errors
```
ImportError: cannot import name 'FastAPI' from 'fastapi'
```

**Solutions:**
1. **Check FastAPI installation:**
   ```bash
   pip show fastapi
   ```

2. **Reinstall FastAPI:**
   ```bash
   pip uninstall fastapi
   pip install fastapi>=0.104.0
   ```

3. **Check for version conflicts:**
   ```bash
   pip check
   ```

#### Issue: Database Connection Failed
```
Error: could not connect to server: Connection refused
```

**Solutions:**
1. **Start database service:**
   ```bash
   # PostgreSQL
   sudo systemctl start postgresql
   
   # Docker Compose
   docker-compose up -d db
   ```

2. **Check database configuration:**
   ```bash
   # Verify .env file
   cat .env
   # Check DATABASE_URL is correct
   ```

3. **Use SQLite for development:**
   ```bash
   # In .env file
   DATABASE_URL=sqlite:///./app.db
   ```

### Docker Issues

#### Issue: Docker Build Failed
```
Error: failed to solve with frontend dockerfile.v0
```

**Solutions:**
1. **Check Docker is running:**
   ```bash
   docker --version
   docker info
   ```

2. **Build with verbose output:**
   ```bash
   docker build --no-cache -t my-project .
   ```

3. **Check Dockerfile syntax:**
   ```bash
   # Verify Dockerfile exists and is valid
   cat Dockerfile
   ```

4. **Update base image:**
   ```dockerfile
   # Use specific Python version
   FROM python:3.9-slim
   ```

#### Issue: Docker Compose Failed
```
Error: Service 'web' failed to build
```

**Solutions:**
1. **Check docker-compose.yml:**
   ```bash
   docker-compose config
   ```

2. **Build services individually:**
   ```bash
   docker-compose build web
   docker-compose build db
   ```

3. **Check port conflicts:**
   ```bash
   # Find processes using port 8000
   lsof -i :8000
   # Kill conflicting processes or change port
   ```

### Configuration Issues

#### Issue: Environment Variables Not Loaded
```
Error: KeyError: 'DATABASE_URL'
```

**Solutions:**
1. **Check .env file exists:**
   ```bash
   ls -la .env*
   # Should show .env and .env.example
   ```

2. **Copy from example:**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

3. **Verify environment loading:**
   ```python
   # In Python
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print(os.getenv('DATABASE_URL'))
   ```

4. **Check file permissions:**
   ```bash
   chmod 644 .env
   ```

### Performance Issues

#### Issue: Slow Template Creation
```
Template creation is taking a very long time
```

**Solutions:**
1. **Skip dependency installation:**
   ```bash
   zenive create my-project -t template-name --no-deps
   # Install dependencies later manually
   ```

2. **Use faster mirror:**
   ```bash
   pip install -r requirements.txt -i https://pypi.douban.com/simple/
   ```

3. **Check network connectivity:**
   ```bash
   ping pypi.org
   ```

4. **Use cached wheels:**
   ```bash
   pip install --cache-dir ~/.pip/cache -r requirements.txt
   ```

#### Issue: Large Template Size
```
Template download/creation is very slow due to size
```

**Solutions:**
1. **Use minimal template first:**
   ```bash
   zenive create my-project -t fastapi-minimal
   # Add complexity later
   ```

2. **Check available disk space:**
   ```bash
   df -h
   ```

3. **Clean up old projects:**
   ```bash
   rm -rf old-project-*
   ```

## Debugging Techniques

### Enable Debug Logging

```bash
# Set environment variable
export ZEN_LOG_LEVEL=DEBUG
zenive create my-project -t fastapi-minimal

# Or use verbose flag
zenive create my-project -t fastapi-minimal --verbose
```

### Validate Before Creating

```bash
# Always validate templates before use
zenive validate --all

# Validate specific template
zenive validate -t fastapi-minimal --test
```

### Check System Requirements

```bash
# Python version
python --version

# Pip version
pip --version

# Available space
df -h

# Memory usage
free -h

# Network connectivity
ping github.com
```

### Inspect Generated Projects

```bash
# Check project structure
tree my-project

# Verify files were created correctly
ls -la my-project/

# Check configuration
cat my-project/.zen/config.yaml

# Test application
cd my-project
python -m app.main
```

## Error Code Reference

### Template System Error Codes

| Code | Error | Description | Solution |
|------|-------|-------------|----------|
| T001 | Template not found | Template name doesn't exist | Check available templates |
| T002 | Invalid template format | template.json is malformed | Validate JSON syntax |
| T003 | Missing template files | Referenced files don't exist | Check file paths |
| T004 | Inheritance error | Parent template issues | Verify parent template |
| T005 | Variable substitution failed | Template variable error | Check variable definitions |
| T006 | Dependency conflict | Package version conflicts | Resolve dependency versions |
| T007 | Permission denied | File system permissions | Check directory permissions |
| T008 | Network error | Cannot download resources | Check network connectivity |

### Project Creation Error Codes

| Code | Error | Description | Solution |
|------|-------|-------------|----------|
| P001 | Invalid project name | Name format is invalid | Use alphanumeric names with hyphens |
| P002 | Directory exists | Target directory not empty | Use different name or remove directory |
| P003 | Dependency installation failed | pip install failed | Check Python environment |
| P004 | Virtual environment creation failed | venv creation failed | Install python3-venv package |
| P005 | File creation failed | Cannot write files | Check permissions and disk space |
| P006 | Configuration error | Invalid configuration | Check .env and config files |

## Getting Additional Help

### Community Resources

1. **GitHub Issues**: Report bugs and request features
   - https://github.com/TheRaj71/Zenive/issues

2. **Documentation**: Comprehensive guides and references
   - [Template System Guide](TEMPLATE_SYSTEM_GUIDE.md)
   - [Template Development Guide](TEMPLATE_DEVELOPMENT.md)
   - [API Reference](API_REFERENCE.md)

3. **Examples**: Working examples and tutorials
   - Check `examples/` directory in repository
   - Review existing templates in `zen/templates/`

### Diagnostic Information

When reporting issues, include:

1. **System Information:**
   ```bash
   python --version
   pip --version
   zenive --version
   uname -a  # Linux/Mac
   ```

2. **Error Details:**
   ```bash
   # Full error message
   # Command that caused the error
   # Expected vs actual behavior
   ```

3. **Environment:**
   ```bash
   # Virtual environment status
   # Installed packages: pip list
   # Environment variables (sanitized)
   ```

4. **Template Information:**
   ```bash
   zenive validate -t template-name
   # Template validation output
   ```

### Self-Diagnosis Checklist

Before seeking help, try:

- [ ] Check template name spelling
- [ ] Validate template with `zenive validate`
- [ ] Verify Python version (3.8+)
- [ ] Check available disk space
- [ ] Test with minimal template first
- [ ] Review error messages carefully
- [ ] Check file permissions
- [ ] Verify network connectivity
- [ ] Try creating in different directory
- [ ] Check for conflicting processes/ports

### Advanced Debugging

#### Template Registry Inspection

```python
from zen.core.template_registry import TemplateRegistry

registry = TemplateRegistry()
templates = registry.list_templates()

print("Available templates:")
for template in templates:
    print(f"  {template.name} v{template.version}")
    
# Check specific template
try:
    template = registry.get_template("fastapi-minimal")
    print(f"Template loaded: {template.name}")
    
    # Check inheritance
    resolved = registry.resolve_inheritance(template)
    print(f"Files after resolution: {len(resolved.files)}")
    
except Exception as e:
    print(f"Error loading template: {e}")
```

#### Project Creation Debugging

```python
from zen.core.project_initializer import ProjectInitializer
from zen.core.template_registry import TemplateRegistry

registry = TemplateRegistry()
initializer = ProjectInitializer(registry)

# Test project name validation
issues = initializer.validate_project_name("my-project")
if issues:
    print("Name validation issues:")
    for issue in issues:
        print(f"  - {issue}")

# Test directory availability
available = initializer.check_project_directory_availability("my-project")
print(f"Directory available: {available}")

# Test project creation (dry run)
try:
    result = initializer.create_project(
        project_name="test-project",
        template_name="fastapi-minimal",
        dry_run=True  # If supported
    )
    print(f"Dry run result: {result.success}")
except Exception as e:
    print(f"Creation test failed: {e}")
```

#### File System Debugging

```bash
# Check template directory structure
find zen/templates/ -name "*.json" -exec echo "=== {} ===" \; -exec cat {} \;

# Check file permissions
ls -la zen/templates/*/

# Check for symbolic links or special files
find zen/templates/ -type l -o -type p -o -type s

# Verify file encodings
file zen/templates/*/template.json
```

This troubleshooting guide should help resolve most common issues with the template system. For persistent problems, don't hesitate to seek help from the community or maintainers.