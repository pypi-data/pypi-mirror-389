# GitHub Actions Python Component

A comprehensive suite of pre-configured GitHub Actions workflow templates for Python development projects. This component provides battle-tested, production-ready workflows that follow industry best practices and can be easily customized for your specific needs.

## Overview

This component provides ready-to-use GitHub Actions workflows that cover common Python development scenarios including:

- **Continuous Integration**: Basic and matrix testing across multiple Python versions (3.8-3.12) and operating systems (Ubuntu, Windows, macOS)
- **Code Quality**: Automated formatting with Black, import sorting with isort, linting with flake8/pylint, and type checking with mypy
- **Security**: Vulnerability scanning with bandit and safety, plus CodeQL integration for advanced security analysis
- **Publishing**: Automated package publishing to PyPI and TestPyPI with secure token-based authentication
- **Documentation**: Automated documentation building and deployment for both Sphinx and MkDocs to GitHub Pages
- **Dependency Management**: Automated dependency updates with Dependabot and security monitoring
- **Performance**: Performance benchmarking and regression detection with pytest-benchmark

## Features

✅ **Zero Configuration**: Works out of the box with sensible defaults  
✅ **Highly Customizable**: Extensive configuration options and inline documentation  
✅ **Security First**: Built-in security scanning and secure publishing workflows  
✅ **Multi-Platform**: Supports Ubuntu, Windows, and macOS runners  
✅ **Modern Python**: Supports Python 3.8 through 3.12  
✅ **Caching Optimized**: Intelligent dependency caching for faster builds  
✅ **Production Ready**: Battle-tested workflows used in real projects

## Installation

### Using zenive (Recommended)

```bash
# Install from GitHub repository
zen add https://github.com/TheRaj71/Zenive/tree/main/components/github-actions-python

# Or install from raw URL
zen add https://raw.githubusercontent.com/TheRaj71/Zenive/main/components/github-actions-python/component.json
```

### Direct Installation

```bash
# Install with default configuration
python -m components.github-actions-python.installer

# Install with preset configuration
python -m components.github-actions-python.installer --preset standard

# List available options
python -m components.github-actions-python.installer --list
```

### Preset Configurations

- **minimal**: Basic CI and code quality for small projects
- **standard**: Comprehensive setup for most Python projects  
- **library**: Complete setup for Python libraries and packages
- **enterprise**: Full setup with all security and quality features

### Custom Installation

```bash
# Install specific workflows
python -m components.github-actions-python.installer \
  --workflows basic_ci,code_quality,security_scan \
  --configs pre_commit,dependabot

# Interactive selection
python -m components.github-actions-python.installer
```

## Available Workflows

### Continuous Integration

#### `ci-basic.yml` - Basic CI Workflow
- **Purpose**: Simple CI workflow for small projects or getting started
- **Python Version**: 3.11 (single version)
- **OS**: Ubuntu only
- **Features**: 
  - Dependency installation with caching
  - Test execution with pytest
  - Code coverage reporting with codecov
- **Triggers**: Push to main/master, pull requests
- **Best For**: Small projects, prototypes, simple libraries

#### `ci-matrix.yml` - Matrix CI Workflow  
- **Purpose**: Comprehensive testing across multiple environments
- **Python Versions**: 3.8, 3.9, 3.10, 3.11, 3.12
- **OS**: Ubuntu, Windows, macOS
- **Features**:
  - Parallel execution across all combinations
  - Intelligent dependency caching
  - Coverage aggregation and reporting
  - Fail-fast strategy for quick feedback
- **Triggers**: Push to main/master, pull requests
- **Best For**: Libraries, packages, production applications

### Code Quality

#### `code-quality.yml` - Comprehensive Code Quality
- **Tools Integrated**:
  - **Black**: Code formatting (88 character line length)
  - **isort**: Import sorting and organization
  - **flake8**: PEP 8 compliance and basic linting
  - **pylint**: Advanced linting and code analysis
  - **mypy**: Static type checking
- **Features**:
  - Grouped output for easy review
  - Configurable strictness levels
  - Integration with popular IDEs
- **Triggers**: Push, pull requests
- **Best For**: All projects wanting consistent code quality

#### `security-scan.yml` - Security Analysis
- **Tools Integrated**:
  - **Bandit**: Python security linting
  - **Safety**: Dependency vulnerability scanning
  - **CodeQL**: Advanced semantic code analysis
- **Features**:
  - Scheduled weekly scans
  - Security advisory integration
  - SARIF report generation
- **Triggers**: Push to main, pull requests, weekly schedule
- **Best For**: Production applications, security-conscious projects

### Publishing

#### `publish-pypi.yml` - Production Publishing
- **Purpose**: Automated package publishing to PyPI on releases
- **Features**:
  - Secure token-based authentication
  - Build verification before publishing
  - Version validation and conflict detection
  - Both source and wheel distribution building
  - Attestation generation for supply chain security
- **Triggers**: Release tag creation (v*)
- **Required Secrets**: `PYPI_API_TOKEN`
- **Best For**: Production packages, libraries

#### `publish-testpypi.yml` - Test Publishing
- **Purpose**: Test package publishing for validation
- **Features**: Same as PyPI workflow but targets TestPyPI
- **Triggers**: Push to develop branch, manual dispatch
- **Required Secrets**: `TEST_PYPI_API_TOKEN`
- **Best For**: Testing package builds before production release

### Documentation

#### `docs-sphinx.yml` - Sphinx Documentation
- **Purpose**: Build and deploy Sphinx documentation
- **Features**:
  - Automatic API documentation from docstrings
  - GitHub Pages deployment
  - Multi-version documentation support
  - Link checking and validation
  - Custom theme support
- **Triggers**: Push to main, pull requests
- **Requirements**: `docs/` directory with Sphinx configuration
- **Best For**: API documentation, technical documentation

#### `docs-mkdocs.yml` - MkDocs Documentation
- **Purpose**: Build and deploy MkDocs documentation
- **Features**:
  - Material theme integration
  - GitHub Pages deployment
  - Markdown-based documentation
  - Plugin ecosystem support
- **Triggers**: Push to main, pull requests  
- **Requirements**: `mkdocs.yml` configuration file
- **Best For**: User guides, tutorials, project documentation

### Maintenance

#### `dependency-update.yml` - Dependency Management
- **Purpose**: Automated dependency maintenance and security
- **Features**:
  - Automated dependency updates
  - Security vulnerability notifications
  - Requirements file generation
  - License compliance checking
  - Integration with GitHub security advisories
- **Triggers**: Weekly schedule, manual dispatch
- **Best For**: All projects wanting automated maintenance

#### `performance-test.yml` - Performance Monitoring
- **Purpose**: Performance regression detection and benchmarking
- **Features**:
  - Benchmark execution with pytest-benchmark
  - Performance comparison with baseline
  - Memory usage profiling with memory-profiler
  - Results archival and trending
  - Performance alerts on regression
- **Triggers**: Push to main, pull requests, manual dispatch
- **Best For**: Performance-critical applications, libraries

## Configuration Files

- **dependabot.yml**: Dependabot configuration for automated dependency updates
- **.pre-commit-config.yaml**: Pre-commit hooks for local development quality gates
- **pyproject.toml.template**: Template for modern Python packaging configuration

## Usage Instructions

### After Installation

#### 1. Commit and Push Workflow Files
```bash
git add .github/
git commit -m "Add GitHub Actions workflows"
git push origin main
```

#### 2. Configure Repository Secrets
Navigate to your repository → Settings → Secrets and variables → Actions:

**For Publishing Workflows:**
- `PYPI_API_TOKEN`: Your PyPI API token (get from https://pypi.org/manage/account/token/)
- `TEST_PYPI_API_TOKEN`: Your TestPyPI API token (get from https://test.pypi.org/manage/account/token/)

**For Documentation Workflows:**
- GitHub Pages will be automatically configured when the workflow runs

#### 3. Set Up Pre-commit Hooks (if selected)
```bash
# Install pre-commit
pip install pre-commit

# Install the hooks
pre-commit install

# Test the setup (optional)
pre-commit run --all-files
```

#### 4. Configure Documentation (if selected)

**For Sphinx Documentation:**
```bash
# Create docs directory structure
mkdir -p docs
cd docs

# Initialize Sphinx (if not already done)
sphinx-quickstart

# Ensure your docs/conf.py includes:
# extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode', 'sphinx.ext.napoleon']
```

**For MkDocs Documentation:**
```bash
# Create mkdocs.yml in project root
cat > mkdocs.yml << EOF
site_name: Your Project Name
theme:
  name: material
nav:
  - Home: index.md
  - API Reference: api.md
EOF

# Create docs directory
mkdir -p docs
echo "# Welcome" > docs/index.md
```

#### 5. Enable GitHub Pages
1. Go to repository Settings → Pages
2. Select "Deploy from a branch"
3. Choose "gh-pages" branch (created automatically by documentation workflows)

### Workflow Customization

Each workflow file includes comprehensive inline comments explaining:
- Configuration options and environment variables
- Required secrets and permissions
- Customization instructions and examples
- Best practices and common patterns

#### Common Customizations

**Modify Python Versions (ci-matrix.yml):**
```yaml
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11']  # Remove or add versions as needed
```

**Change Code Quality Tools (code-quality.yml):**
```yaml
- name: Install code quality tools
  run: |
    # Add or remove tools as needed
    pip install black isort flake8 pylint mypy bandit
```

**Customize Test Commands:**
```yaml
- name: Run tests
  run: |
    # Customize test execution
    pytest tests/ --cov=src --cov-report=xml
    # Or use unittest
    python -m unittest discover tests/
```

**Configure Coverage Thresholds:**
```yaml
- name: Check coverage
  run: |
    coverage report --fail-under=80  # Set minimum coverage percentage
```

### Example Project Structure

After installation, your project will have:

```
your-project/
├── .github/
│   ├── workflows/
│   │   ├── ci-matrix.yml              # Multi-version testing
│   │   ├── code-quality.yml           # Linting and formatting
│   │   ├── security-scan.yml          # Security analysis
│   │   ├── publish-pypi.yml           # Package publishing
│   │   ├── docs-sphinx.yml            # Documentation building
│   │   └── dependency-update.yml      # Dependency management
│   └── dependabot.yml                 # Dependabot configuration
├── .pre-commit-config.yaml            # Local development hooks
└── pyproject.toml.template            # Modern Python packaging
```

## Usage Examples

### Example 1: Simple Library Setup
Perfect for a small Python library:

```bash
# Install minimal setup
python -m components.github-actions-python.installer --preset minimal

# This installs:
# - ci-basic.yml (single version testing)
# - code-quality.yml (formatting and linting)
# - pre-commit configuration
```

### Example 2: Production Application
Comprehensive setup for production applications:

```bash
# Install standard setup
python -m components.github-actions-python.installer --preset standard

# This installs:
# - ci-matrix.yml (multi-version testing)
# - code-quality.yml (comprehensive quality checks)
# - security-scan.yml (security analysis)
# - dependency-update.yml (automated maintenance)
# - dependabot.yml (dependency updates)
# - pre-commit configuration
```

### Example 3: Open Source Package
Full setup for open source Python packages:

```bash
# Install library preset
python -m components.github-actions-python.installer --preset library

# This installs:
# - ci-matrix.yml (comprehensive testing)
# - code-quality.yml (quality assurance)
# - security-scan.yml (security scanning)
# - publish-pypi.yml (automated publishing)
# - publish-testpypi.yml (test publishing)
# - docs-sphinx.yml (API documentation)
# - dependency-update.yml (maintenance)
# - All configuration files
```

### Example 4: Custom Selection
Choose specific workflows for your needs:

```bash
# Interactive selection
python -m components.github-actions-python.installer

# Or specify exactly what you want
python -m components.github-actions-python.installer \
  --workflows matrix_ci,code_quality,security_scan \
  --configs pre_commit,dependabot
```

### Example 5: Documentation-Focused Project
For projects that prioritize documentation:

```bash
# Install documentation workflows
python -m components.github-actions-python.installer \
  --workflows basic_ci,docs_sphinx,docs_mkdocs \
  --configs pre_commit

# Then set up your documentation
mkdir docs
sphinx-quickstart docs  # For Sphinx
# OR
echo "site_name: My Project" > mkdocs.yml  # For MkDocs
```

## Programmatic Usage

```python
from components.github_actions_python import (
    install_component,
    install_with_selection,
    list_available_options
)

# Install with default options
result = install_component(project_root=".", overwrite=False)

# Install with preset
result = install_with_selection(preset="standard", overwrite=False)

# Install with custom options
custom_options = {
    "workflows": {
        "matrix_ci": True,
        "code_quality": True,
        "security_scan": True
    },
    "configs": {
        "dependabot": True,
        "pre_commit": True
    }
}
result = install_with_selection(custom_options=custom_options)

# List available options
options = list_available_options()
print(f"Available workflows: {list(options['workflows'].keys())}")
```

## Requirements

- Python 3.8+
- GitHub repository with Actions enabled
- Appropriate repository secrets for publishing workflows

## Troubleshooting

### Common Issues and Solutions

#### Workflow Files Not Triggering
**Problem**: Workflows don't run after installation  
**Solutions**:
- Ensure files are committed and pushed to the repository
- Check that the branch names match your default branch (main vs master)
- Verify GitHub Actions is enabled in repository settings
- Check the Actions tab for any error messages

#### Publishing Workflow Failures
**Problem**: Package publishing fails  
**Solutions**:
- Verify `PYPI_API_TOKEN` or `TEST_PYPI_API_TOKEN` secrets are correctly set
- Ensure the token has appropriate permissions for your package
- Check that your package name doesn't conflict with existing packages
- Verify your `setup.py` or `pyproject.toml` configuration is valid
- For first-time publishing, you may need to create the package manually on PyPI

#### Code Quality Failures
**Problem**: Code quality checks fail unexpectedly  
**Solutions**:
- Run tools locally first: `black --check .`, `flake8 .`, `mypy .`
- Check if your code follows the expected style (88 character line length for Black)
- Review pylint and mypy configuration - they may need project-specific settings
- Consider adding a `.flake8`, `pyproject.toml`, or `mypy.ini` configuration file

#### Documentation Build Failures
**Problem**: Documentation workflows fail to build  
**Solutions**:
- **Sphinx**: Ensure `docs/conf.py` exists and is properly configured
- **MkDocs**: Verify `mkdocs.yml` exists in project root
- Check that all documentation dependencies are listed in requirements
- Ensure docstrings follow proper format (Google, NumPy, or Sphinx style)
- Verify all internal links and references are valid

#### Permission and Access Issues
**Problem**: Workflows fail with permission errors  
**Solutions**:
- Check repository Settings → Actions → General → Workflow permissions
- Ensure "Read and write permissions" is selected for GITHUB_TOKEN
- For GitHub Pages deployment, enable Pages in repository settings
- Verify branch protection rules don't block the workflows

#### Pre-commit Hook Issues
**Problem**: Pre-commit hooks not working or failing  
**Solutions**:
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Update hook versions
pre-commit autoupdate

# Run hooks manually to test
pre-commit run --all-files

# Skip hooks temporarily (not recommended for regular use)
git commit -m "message" --no-verify
```

#### Dependency and Environment Issues
**Problem**: Dependency installation or environment setup fails  
**Solutions**:
- Ensure `requirements.txt` or `pyproject.toml` is properly formatted
- Check for conflicting dependencies
- Verify Python version compatibility
- Consider pinning dependency versions for reproducible builds
- Use `pip-tools` or `poetry` for better dependency management

#### Performance Test Issues
**Problem**: Performance tests fail or are unreliable  
**Solutions**:
- Performance tests can be flaky in CI environments
- Consider using relative performance comparisons instead of absolute thresholds
- Add `continue-on-error: true` for performance tests in CI
- Use consistent runner types (avoid mixing different OS/hardware)

### Advanced Troubleshooting

#### Debugging Workflow Runs
1. **Check the Actions tab** in your repository for detailed logs
2. **Enable debug logging** by setting repository secret `ACTIONS_STEP_DEBUG` to `true`
3. **Add debug steps** to workflows:
   ```yaml
   - name: Debug Environment
     run: |
       echo "Python version: $(python --version)"
       echo "Pip version: $(pip --version)"
       echo "Working directory: $(pwd)"
       echo "Files in directory: $(ls -la)"
   ```

#### Common Configuration Files

**`.flake8` configuration:**
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,venv,.venv,build,dist
```

**`pyproject.toml` tool configuration:**
```toml
[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.8"
ignore_missing_imports = true
```

### Getting Help

1. **Check workflow logs**: Go to Actions tab → Select failed workflow → Review step-by-step logs
2. **Review inline documentation**: Each workflow file contains detailed comments and examples
3. **Validate configuration**: Ensure all required secrets, environment variables, and files are properly configured
4. **Test locally**: Run the same commands locally to isolate CI-specific issues
5. **Community resources**: 
   - [GitHub Actions Documentation](https://docs.github.com/en/actions)
   - [Python Packaging Guide](https://packaging.python.org/)
   - [Pre-commit Documentation](https://pre-commit.com/)

### Best Practices

- **Start simple**: Begin with basic workflows and gradually add more complex ones
- **Test locally first**: Always test code quality tools and tests locally before pushing
- **Use branch protection**: Require status checks to pass before merging
- **Monitor workflow usage**: Keep an eye on GitHub Actions usage to avoid hitting limits
- **Keep secrets secure**: Regularly rotate API tokens and review access permissions
- **Document customizations**: Add comments when you modify workflow files

## License

MIT License - see LICENSE file for details.