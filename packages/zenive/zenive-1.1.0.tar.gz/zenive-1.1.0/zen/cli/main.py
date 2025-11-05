#!/usr/bin/env python3
"""
zen CLI - Python component registry like shadcn/ui
"""

import click
import sys
from pathlib import Path
from zen.core.logger import get_logger, setup_logging
from zen.core.installer import ComponentInstaller
from zen.core.template_controller import TemplateController
from zen.core.exceptions import (
    InstallationError, 
    ConfigurationError, 
    TemplateError, 
    TemplateNotFoundError, 
    ProjectCreationError
)

logger = get_logger()

@click.group()
@click.version_option(version="1.0.0", prog_name="zen")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose):
    """zen - Python component registry like shadcn/ui"""
    setup_logging(verbose=verbose)

@cli.command()
@click.argument("project_name", required=False)
@click.option("--force", "-f", is_flag=True, help="Overwrite existing project")
@click.option("--minimal", "-m", is_flag=True, help="Minimal setup (just .zen config)")
def init(project_name, force, minimal):
    """Initialize zen in a new or existing project (like shadcn/ui init)"""
    try:
        project_path = Path(project_name) if project_name else Path.cwd()
        is_existing_project = project_path.exists() and project_name is None
        
        if project_name:
            if project_path.exists() and not force:
                logger.error(f"Directory '{project_name}' already exists. Use --force to overwrite.")
                sys.exit(1)
            
            project_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created project directory: {project_path}")
        
        # Check if this is an existing project
        if is_existing_project:
            logger.info("Initializing zen in existing project...")
            if minimal or _detect_existing_project_type():
                _initialize_zen_config()
                logger.success("✨ Successfully initialized zen (minimal setup)")
                logger.info("You can now run 'zen add <component-url>' to install components")
                return
        
        # Full project structure for new projects
        _create_project_structure(project_path)
        
        # Show success with animated banner
        logger.show_animated_banner("🎉 zen Project Initialized!", "Ready to install components")
        
        next_steps = """[cyan]Next steps:[/cyan]
  [dim]1.[/dim] cd into your project directory
  [dim]2.[/dim] Run [green]zen add <component-url>[/green] to install components  
  [dim]3.[/dim] Install dependencies with [green]pip install -r requirements.txt[/green]"""
        
        from rich.panel import Panel
        logger.console.print(Panel(next_steps, border_style="cyan", padding=(1, 2)))
        
    except Exception as e:
        logger.error(f"Failed to initialize project: {e}")
        sys.exit(1)

@cli.command()
@click.argument("component_url")
@click.option("--path", "-p", help="Custom installation path")
@click.option("--overwrite", "-o", is_flag=True, help="Overwrite existing files")
@click.option("--dry-run", "-d", is_flag=True, help="Show what would be done without doing it")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompts")
def add(component_url, path, overwrite, dry_run, yes):
    """Install a component from URL (like shadcn/ui)
    
    Examples:
      zen add https://github.com/user/repo/component.json
      zen add https://github.com/user/components/tree/main/email-validator
      zen add https://raw.githubusercontent.com/user/repo/main/component.json
      zen add file:///path/to/component.json
    """
    try:
        # Check if we're in a zen project, if not, offer to initialize
        config_path = Path(".zen/config.yaml")
        if not config_path.exists():
            logger.warning("No zen configuration found.")
            if not yes and click.confirm("Initialize zen in this directory?"):
                _initialize_zen_config()
                logger.info("✨ Initialized zen configuration")
            elif yes:
                _initialize_zen_config()
                logger.info("✨ Initialized zen configuration")
            else:
                logger.error("Cannot install components without zen configuration.")
                logger.info("Run 'zen init' or use --yes to auto-initialize.")
                sys.exit(1)
        
        installer = ComponentInstaller()
        
        # Fetch component with elegant connecting lines animation
        try:
            from zen.schemas.component import load_component_from_url
            
            with logger.connection_loader(f"Fetching component from {component_url}"):
                component = load_component_from_url(component_url)
            
            # Show beautiful component info
            install_path = path or installer._get_default_path(component.category)
            logger.show_component_info(
                component.name, 
                component.version, 
                component.description,
                component.category,
                component.dependencies,
                len(component.files)
            )
            logger.info(f"[cyan]📍 Install to:[/cyan] {install_path}")
            
        except Exception as e:
            logger.error(f"Failed to fetch component: {e}")
            sys.exit(1)
        
        if dry_run:
            logger.info("")
            logger.info("🔍 DRY RUN - No changes will be made")
            logger.info("Files that would be installed:")
            for file_info in component.files:
                target_path = path or file_info.path
                logger.info(f"  • {file_info.name} -> {target_path}")
            return
        
        # Confirmation prompt (unless --yes)
        if not yes:
            logger.info("")
            if not click.confirm("Proceed with installation?"):
                logger.info("Installation cancelled.")
                return
        
        logger.info("")
        
        # Install component with beautiful wave animation
        with logger.wave_loader("Installing component files and dependencies"):
            result = installer.install_from_url(component_url, path, overwrite)
        
        # Show matrix transition effect before success
        logger.show_matrix_transition(f"Component {result['component']} installed successfully!", 2.0)
        
        # Show beautiful success summary
        logger.show_success_summary(
            result['component'],
            result['files_installed'], 
            result['dependencies_added'],
            result['install_path']
        )
        
    except (InstallationError, ConfigurationError) as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

def _create_project_structure(project_path: Path):
    """Create the basic project structure"""
    import yaml
    
    # Create directories
    directories = [
        ".zen",
        "src",
        "src/components", 
        "src/utils",
        "src/models",
        "src/services",
        "src/auth",
        "src/data"
    ]
    
    for dir_name in directories:
        dir_path = project_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created directory: {dir_path}")
    
    # Create config file
    config = {
        "name": project_path.name,
        "version": "1.0.0",
        "description": f"zen project: {project_path.name}",
        "structure": {
            "components": "src/components",
            "utils": "src/utils", 
            "models": "src/models",
            "services": "src/services",
            "auth": "src/auth",
            "data": "src/data"
        },
        "components": {}
    }
    
    config_path = project_path / ".zen" / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    logger.info(f"Created configuration file: {config_path}")
    
    # Create requirements.txt with zen dependencies
    requirements_path = project_path / "requirements.txt"
    requirements_content = """# Project dependencies
# Generated by zen

# Core dependencies (uncomment if needed)
# requests>=2.25.0
# pydantic>=1.8.0
# click>=8.0.0

# Add your project dependencies below
"""
    with open(requirements_path, "w") as f:
        f.write(requirements_content)
    logger.info("Created requirements.txt")
    
    # Create .gitignore
    gitignore_path = project_path / ".gitignore"
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
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

# Virtual environments
venv/
env/
ENV/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
.zen/cache/
"""
    with open(gitignore_path, "w") as f:
        f.write(gitignore_content)
    logger.info("Created .gitignore")
    
    # Create README.md
    readme_path = project_path / "README.md"
    readme_content = f"""# {project_path.name}

A zen project.

## Installation

Install dependencies:
```bash
pip install -r requirements.txt
```

## Adding Components

Install components from JSON URLs:
```bash
zen add https://example.com/component.json
zen add https://github.com/user/repo/component.json
```

## Project Structure

```
{project_path.name}/
├── src/
│   ├── components/    # General components
│   ├── utils/         # Utility functions
│   ├── models/        # Data models
│   ├── services/      # Business logic
│   ├── auth/          # Authentication
│   └── data/          # Data processing
├── .zen/
│   └── config.yaml    # Project configuration
├── requirements.txt   # Python dependencies
└── README.md
```

Built with [zen](https://github.com/TheRaj71/Zenive)
"""
    with open(readme_path, "w") as f:
        f.write(readme_content)
    logger.info("Created README.md")
    
    # Create __init__.py files
    init_files = [
        "src/__init__.py",
        "src/components/__init__.py",
        "src/utils/__init__.py", 
        "src/models/__init__.py",
        "src/services/__init__.py",
        "src/auth/__init__.py",
        "src/data/__init__.py"
    ]
    
    for init_file in init_files:
        init_path = project_path / init_file
        with open(init_path, "w") as f:
            f.write("")
        logger.debug(f"Created {init_path}")

@cli.command()
def list():
    """List installed components"""
    try:
        config_path = Path(".zen/config.yaml")
        if not config_path.exists():
            logger.error("Not in a zen project. Run 'zen init' first.")
            sys.exit(1)
        
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        
        components = config.get("components", {})
        
        if not components:
            logger.info("No components installed.")
            return
        
        # Show components in a beautiful table
        from rich.table import Table
        
        table = Table(title=f"📦 Installed Components ({len(components)})", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="green", no_wrap=True)
        table.add_column("Version", style="blue")
        table.add_column("Category", style="yellow")
        table.add_column("Source", style="dim", overflow="ellipsis", max_width=50)
        
        for comp_name, comp_info in components.items():
            name = comp_info.get("name", comp_name)
            version = comp_info.get("version", "unknown")
            category = comp_info.get("category", "unknown")
            source = comp_info.get("source", "unknown")
            
            table.add_row(name, version, category, source)
        
        logger.console.print(table)
            
    except Exception as e:
        logger.error(f"Failed to list components: {e}")
        sys.exit(1)

@cli.command()
@click.argument("component_name")
def info(component_name):
    """Show detailed information about an installed component"""
    try:
        config_path = Path(".zen/config.yaml")
        if not config_path.exists():
            logger.error("Not in a zen project. Run 'zen init' first.")
            sys.exit(1)
        
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        
        components = config.get("components", {})
        
        if component_name not in components:
            logger.error(f"Component '{component_name}' not found.")
            logger.info("Run 'zen list' to see installed components.")
            sys.exit(1)
        
        comp_info = components[component_name]
        
        logger.info(f"📦 Component: {comp_info.get('name', component_name)}")
        logger.info(f"Version: {comp_info.get('version', 'unknown')}")
        logger.info(f"Category: {comp_info.get('category', 'unknown')}")
        logger.info(f"Source: {comp_info.get('source', 'unknown')}")
        
        deps = comp_info.get('dependencies', [])
        if deps:
            logger.info(f"Dependencies: {', '.join(deps)}")
        
    except Exception as e:
        logger.error(f"Failed to show component info: {e}")
        sys.exit(1)

@cli.command()
@click.option("--show", is_flag=True, help="Show current animation settings")
@click.option("--disable-all", is_flag=True, help="Disable all animations")
@click.option("--enable-all", is_flag=True, help="Enable all animations")
@click.option("--minimal", is_flag=True, help="Enable minimal animations only")
@click.option("--demo", is_flag=True, help="Show animation demo")
@click.option("--reset", is_flag=True, help="Reset to default settings")
def animations(show, disable_all, enable_all, minimal, demo, reset):
    """Configure CLI animations and visual effects
    
    Examples:
      zen animations --show           # Show current settings
      zen animations --demo           # Show animation demo
      zen animations --disable-all    # Disable all animations
      zen animations --enable-all     # Enable all animations
      zen animations --minimal        # Enable minimal animations
      zen animations --reset          # Reset to defaults
    """
    try:
        from zen.core.animation_config import get_animation_manager
        
        manager = get_animation_manager()
        
        if demo:
            logger.info("🎨 Starting animation demo...")
            try:
                from zen.demo_animations import main as demo_main
                demo_main()
            except ImportError:
                logger.error("Demo script not found")
            return
        
        if reset:
            manager.reset_to_defaults()
            logger.success("✨ Animation settings reset to defaults")
            return
        
        if disable_all:
            manager.disable_all_animations()
            logger.success("🚫 All animations disabled")
            return
        
        if enable_all:
            manager.enable_full_animations()
            logger.celebrate("All animations enabled!")
            return
        
        if minimal:
            manager.enable_minimal_animations()
            logger.success("⚡ Minimal animations enabled")
            return
        
        if show:
            config = manager.config
            
            # Create settings table
            from rich.table import Table
            
            table = Table(title="🎨 Animation Settings", show_header=True, header_style="bold cyan")
            table.add_column("Setting", style="yellow", no_wrap=True)
            table.add_column("Value", style="white")
            table.add_column("Description", style="dim")
            
            settings = [
                ("enable_animations", config.enable_animations, "Master animation toggle"),
                ("enable_connection_loader", config.enable_connection_loader, "Connection lines animation"),
                ("enable_wave_loader", config.enable_wave_loader, "Wave loading animation"),
                ("enable_pulse_loader", config.enable_pulse_loader, "Pulse loading animation"),
                ("enable_elegant_borders", config.enable_elegant_borders, "Elegant border effects"),
                ("enable_rainbow_text", config.enable_rainbow_text, "Rainbow colored text"),
                ("enable_typewriter_effect", config.enable_typewriter_effect, "Typewriter text animation"),
                ("connection_speed", f"{config.connection_speed}s", "Connection animation speed"),
                ("wave_speed", f"{config.wave_speed}s", "Wave animation speed"),
                ("pulse_speed", f"{config.pulse_speed}s", "Pulse animation speed"),
                ("primary_color", config.primary_color, "Primary UI color"),
                ("success_color", config.success_color, "Success message color"),
            ]
            
            for setting, value, description in settings:
                status = "✅" if value is True else "❌" if value is False else str(value)
                table.add_row(setting, status, description)
            
            logger.console.print(table)
            
            logger.info("")
            logger.info("💡 Use the following commands to modify settings:")
            logger.info("  zen animations --disable-all  # Disable all animations")
            logger.info("  zen animations --enable-all   # Enable all animations")
            logger.info("  zen animations --minimal      # Enable minimal animations")
            logger.info("  zen animations --demo         # Show animation demo")
            
            return
        
        # Default: show help
        logger.info("Use 'zen animations --help' for available options")
        logger.info("Try 'zen animations --demo' to see all animations!")
        
    except Exception as e:
        logger.error(f"Failed to configure animations: {e}")
        sys.exit(1)

@cli.command()
@click.argument("component_name")
@click.option("--force", "-f", is_flag=True, help="Force removal without confirmation")
def remove(component_name, force):
    """Remove an installed component"""
    try:
        config_path = Path(".zen/config.yaml")
        if not config_path.exists():
            logger.error("Not in a zen project. Run 'zen init' first.")
            sys.exit(1)
        
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        
        components = config.get("components", {})
        
        if component_name not in components:
            logger.error(f"Component '{component_name}' not found.")
            sys.exit(1)
        
        comp_info = components[component_name]
        
        if not force:
            logger.info(f"This will remove component: {comp_info.get('name', component_name)}")
            logger.warning("Note: Files will not be automatically deleted.")
            logger.warning("You may need to manually remove files and clean up dependencies.")
            
            if not click.confirm("Continue?"):
                logger.info("Removal cancelled.")
                return
        
        # Remove from config
        del components[component_name]
        config["components"] = components
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        logger.celebrate(f"Component {component_name} removed successfully!")
        logger.info("💡 Consider manually removing files and cleaning up dependencies.")
        
    except Exception as e:
        logger.error(f"Failed to remove component: {e}")
        sys.exit(1)

@cli.command()
@click.option("--template", "-t", help="Validate specific template")
@click.option("--all", "-a", is_flag=True, help="Validate all templates")
@click.option("--test", is_flag=True, help="Run comprehensive tests")
@click.option("--fix", is_flag=True, help="Attempt to fix validation issues")
def validate(template, all, test, fix):
    """Validate templates and run tests
    
    Examples:
      zenive validate --all                    # Validate all templates
      zenive validate -t fastapi-minimal       # Validate specific template
      zenive validate --all --test             # Run comprehensive tests
    """
    try:
        from zen.core.template_validator import TemplateValidator, TemplateTestFramework
        
        controller = TemplateController()
        validator = TemplateValidator(controller.registry)
        test_framework = TemplateTestFramework(controller.registry)
        
        if all:
            # Validate all templates
            templates = controller.list_available_templates()
            if not templates:
                logger.info("No templates found to validate")
                return
            
            logger.show_elegant_border(f"Validating {len(templates)} templates", 40)
            logger.info("")
            
            total_errors = 0
            total_warnings = 0
            
            for template_info in templates:
                logger.info(f"📋 Validating {template_info.name}...")
                
                try:
                    template_schema = controller.registry.get_template(template_info.name)
                    
                    if test:
                        result = test_framework.test_template(template_info.name)
                    else:
                        result = validator.validate_template(template_schema)
                    
                    if result.is_valid:
                        logger.success(f"✅ {template_info.name}: Valid")
                    else:
                        logger.error(f"❌ {template_info.name}: {len(result.errors)} errors")
                    
                    if result.warnings:
                        logger.warning(f"⚠️  {template_info.name}: {len(result.warnings)} warnings")
                    
                    # Show details if there are issues
                    if result.errors or result.warnings:
                        for error in result.errors:
                            logger.error(f"   • {error}")
                        for warning in result.warnings:
                            logger.warning(f"   • {warning}")
                    
                    if result.info:
                        for info in result.info:
                            logger.info(f"   ℹ️  {info}")
                    
                    total_errors += len(result.errors)
                    total_warnings += len(result.warnings)
                    
                except Exception as e:
                    logger.error(f"❌ {template_info.name}: Validation failed - {e}")
                    total_errors += 1
                
                logger.info("")
            
            # Summary
            logger.info("📊 Validation Summary:")
            logger.info(f"   Templates: {len(templates)}")
            logger.info(f"   Errors: {total_errors}")
            logger.info(f"   Warnings: {total_warnings}")
            
            if total_errors > 0:
                logger.error("❌ Validation failed with errors")
                sys.exit(1)
            elif total_warnings > 0:
                logger.warning("⚠️  Validation completed with warnings")
            else:
                logger.celebrate("All templates are valid!")
                logger.rainbow_text("🎉 VALIDATION SUCCESS 🎉")
        
        elif template:
            # Validate specific template
            logger.info(f"Validating template: {template}")
            
            try:
                template_schema = controller.registry.get_template(template)
                
                if test:
                    result = test_framework.test_template(template)
                else:
                    result = validator.validate_template(template_schema)
                
                if result.is_valid:
                    logger.success(f"✅ Template '{template}' is valid")
                else:
                    logger.error(f"❌ Template '{template}' has {len(result.errors)} errors")
                
                # Show all results
                for error in result.errors:
                    logger.error(f"   Error: {error}")
                
                for warning in result.warnings:
                    logger.warning(f"   Warning: {warning}")
                
                for info in result.info:
                    logger.info(f"   Info: {info}")
                
                if not result.is_valid:
                    sys.exit(1)
                    
            except KeyError:
                logger.error(f"Template '{template}' not found")
                logger.info("Use 'zenive create --list-templates' to see available templates")
                sys.exit(1)
        
        else:
            logger.error("Please specify --template or --all")
            logger.info("Use 'zenive validate --help' for usage information")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

@cli.command()
@click.argument("project_name", required=False)
@click.option("--template", "-t", help="Template name to use")
@click.option("--list-templates", is_flag=True, help="List available templates")
@click.option("--template-info", help="Show detailed information about a template")
@click.option("--no-deps", is_flag=True, help="Skip dependency installation")
@click.option("--no-venv", is_flag=True, help="Skip virtual environment creation")
def create(project_name, template, list_templates, template_info, no_deps, no_venv):
    """Create a new project from template
    
    Examples:
      zenive create my-api                    # Interactive template selection
      zenive create my-api -t fastapi-minimal # Use specific template
      zenive create --list-templates          # Show available templates
      zenive create --template-info fastapi-moderate  # Show template details
    """
    try:
        controller = TemplateController()
        
        # Handle list templates option
        if list_templates:
            templates = controller.list_available_templates()
            if not templates:
                logger.info("No templates available")
                return
            
            logger.info("Available templates:")
            logger.info("")
            
            from rich.table import Table
            
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Name", style="green", no_wrap=True)
            table.add_column("Complexity", style="yellow", width=12)
            table.add_column("Category", style="blue", width=12)
            table.add_column("Description", style="white")
            table.add_column("Files", style="dim", width=8)
            
            for template_info in templates:
                table.add_row(
                    template_info.name,
                    template_info.complexity.title(),
                    template_info.category.title(),
                    template_info.description,
                    str(template_info.file_count)
                )
            
            logger.console.print(table)
            return
        
        # Handle template info option
        if template_info:
            try:
                details = controller.get_template_details(template_info)
                
                logger.info(f"Template: {details.name} v{details.version}")
                logger.info(f"Description: {details.description}")
                logger.info(f"Complexity: {details.complexity}")
                logger.info(f"Category: {details.category}")
                logger.info(f"Python requires: {details.python_requires}")
                
                if details.extends:
                    logger.info(f"Extends: {details.extends}")
                
                if details.author:
                    logger.info(f"Author: {details.author}")
                
                logger.info(f"License: {details.license}")
                
                if details.keywords:
                    logger.info(f"Keywords: {', '.join(details.keywords)}")
                
                logger.info("")
                logger.info(f"Dependencies ({len(details.dependencies)}):")
                for dep in details.dependencies:
                    logger.info(f"  • {dep}")
                
                if details.dev_dependencies:
                    logger.info(f"Development dependencies ({len(details.dev_dependencies)}):")
                    for dep in details.dev_dependencies:
                        logger.info(f"  • {dep}")
                
                logger.info("")
                logger.info(f"Directories ({len(details.directories)}):")
                for directory in details.directories:
                    logger.info(f"  📁 {directory}")
                
                logger.info("")
                logger.info(f"Files ({len(details.files)}):")
                for file_name in details.files:
                    logger.info(f"  📄 {file_name}")
                
                if details.template_vars:
                    logger.info("")
                    logger.info("Template variables:")
                    for var_name, default_value in details.template_vars.items():
                        logger.info(f"  {var_name}: {default_value}")
                
                return
                
            except KeyError:
                logger.error(f"Template '{template_info}' not found")
                logger.info("Use --list-templates to see available templates")
                sys.exit(1)
        
        # Validate project name is provided for creation
        if not project_name:
            logger.error("Project name is required for project creation")
            logger.info("Use 'zenive create --help' for usage information")
            sys.exit(1)
        
        # Validate project name format
        name_issues = controller.validate_project_name(project_name)
        if name_issues:
            logger.error("Invalid project name:")
            for issue in name_issues:
                logger.error(f"  • {issue}")
            sys.exit(1)
        
        # Check for directory conflicts
        if controller.check_project_directory_conflict(project_name):
            logger.warning(f"Directory '{project_name}' already exists")
            if not click.confirm("Continue and overwrite?", default=False):
                logger.info("Project creation cancelled")
                return
        
        # Create project with interactive or specified template
        if template:
            # Validate template exists
            try:
                controller.get_template_details(template)
            except KeyError:
                logger.error(f"Template '{template}' not found")
                logger.info("Use --list-templates to see available templates")
                sys.exit(1)
        
        # Create the project
        result = controller.create_project_interactive(project_name, template)
        
        if not result.success:
            logger.error(f"Project creation failed: {result.message}")
            sys.exit(1)
        
    except TemplateNotFoundError as e:
        logger.error(f"Template not found: {e.template_name}")
        logger.info("Use --list-templates to see available templates")
        sys.exit(1)
    except ProjectCreationError as e:
        logger.error(f"Project creation failed: {e.message}")
        if e.project_name:
            logger.info(f"Failed project: {e.project_name}")
        if e.template_name:
            logger.info(f"Template used: {e.template_name}")
        sys.exit(1)
    except TemplateError as e:
        logger.error(f"Template system error: {e.message}")
        if e.template_name:
            logger.info(f"Template: {e.template_name}")
        sys.exit(1)
    except (InstallationError, ConfigurationError) as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during project creation: {e}")
        sys.exit(1)

def _detect_existing_project_type():
    """Detect if this is an existing Python project"""
    indicators = [
        "setup.py", "pyproject.toml", "requirements.txt", 
        "Pipfile", "poetry.lock", "src/", "app.py", "main.py"
    ]
    return any(Path(indicator).exists() for indicator in indicators)

def _initialize_zen_config():
    """Initialize minimal zen configuration in existing project (like shadcn/ui)"""
    import yaml
    
    # Create .zen directory
    zen_dir = Path(".zen")
    zen_dir.mkdir(exist_ok=True)
    
    # Create minimal config
    config = {
        "name": Path.cwd().name,
        "version": "1.0.0",
        "components": {}
    }
    
    config_path = zen_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    
    # Create or update .gitignore to include .zen/
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            content = f.read()
        if ".zen/" not in content:
            with open(gitignore_path, "a") as f:
                f.write("\n# zen\n.zen/\n")
    else:
        with open(gitignore_path, "w") as f:
            f.write("# zen\n.zen/\n")

def main():
    """Entry point for the CLI"""
    cli()

if __name__ == "__main__":
    main()
