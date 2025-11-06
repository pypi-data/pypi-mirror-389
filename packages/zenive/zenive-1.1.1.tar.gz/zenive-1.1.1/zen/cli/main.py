#!/usr/bin/env python3
"""
zen CLI - A component registry for discovering, installing, and managing reusable code components
"""

import click
import sys
from pathlib import Path
from zen.core.logger import get_logger, setup_logging
from zen.core.installer import ComponentInstaller
from zen.core.exceptions import (
    InstallationError, 
    ConfigurationError
)

logger = get_logger()

@click.group()
@click.version_option(version="1.0.0", prog_name="zen")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose):
    """zen - A component registry for discovering, installing, and managing reusable code components
    
    Inspired by shadcn/ui, zen helps you build projects by installing individual components
    rather than full project templates. Each component is self-contained and can be
    easily integrated into your existing codebase.
    """
    setup_logging(verbose=verbose)

@cli.command()
@click.option("--force", "-f", is_flag=True, help="Overwrite existing configuration")
def init(force):
    """Initialize zen component registry in the current directory
    
    Creates a .zen/config.yaml file to track installed components and project metadata.
    This is required before you can install components with 'zen add'.
    """
    try:
        current_path = Path.cwd()
        config_path = current_path / ".zen" / "config.yaml"
        
        # Check if zen is already initialized
        if config_path.exists() and not force:
            logger.error("zen is already initialized in this directory. Use --force to overwrite.")
            sys.exit(1)
        
        logger.info("Initializing zen component registry...")
        
        # Initialize zen configuration
        _initialize_zen_config()
        
        logger.success("✨ Successfully initialized zen component registry")
        logger.info("You can now run 'zen add <component-url>' to install components")
        
        next_steps = """[cyan]Next steps:[/cyan]
  [dim]1.[/dim] Run [green]zen add <component-url>[/green] to install components
  [dim]2.[/dim] Use [green]zen list[/green] to see installed components
  [dim]3.[/dim] Use [green]zen info <component>[/green] for component details"""
        
        from rich.panel import Panel
        logger.console.print(Panel(next_steps, border_style="cyan", padding=(1, 2)))
        
    except Exception as e:
        logger.error(f"Failed to initialize zen: {e}")
        sys.exit(1)

@cli.command()
@click.argument("component_url")
@click.option("--path", "-p", help="Custom installation path")
@click.option("--overwrite", "-o", is_flag=True, help="Overwrite existing files")
@click.option("--dry-run", "-d", is_flag=True, help="Show what would be done without doing it")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompts")
def add(component_url, path, overwrite, dry_run, yes):
    """Install a reusable component from a URL into your project
    
    Downloads and installs a component along with its dependencies. Components are
    self-contained pieces of code that can be easily integrated into your project.
    
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



@cli.command()
def list():
    """List all components installed in the current project
    
    Shows a table of installed components with their versions, categories,
    and source URLs for easy reference and management.
    """
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
    """Show detailed information about a specific installed component
    
    Displays comprehensive details including version, category, source URL,
    dependencies, and other metadata for the specified component.
    """
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
    """Remove a component from the project registry
    
    Removes the component from the zen configuration. Note that this does not
    automatically delete the component files - you may need to manually clean
    up files and dependencies.
    """
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







def _initialize_zen_config():
    """Initialize zen component registry configuration"""
    import yaml
    
    # Create .zen directory
    zen_dir = Path(".zen")
    zen_dir.mkdir(exist_ok=True)
    
    # Create component registry config
    config = {
        "name": Path.cwd().name,
        "version": "1.0.0",
        "description": f"zen component registry for {Path.cwd().name}",
        "components": {}
    }
    
    config_path = zen_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    
    logger.info(f"Created zen configuration: {config_path}")
    
    # Create or update .gitignore to include .zen/
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            content = f.read()
        if ".zen/" not in content:
            with open(gitignore_path, "a") as f:
                f.write("\n# zen component registry\n.zen/\n")
            logger.info("Updated .gitignore to exclude .zen/ directory")
    else:
        with open(gitignore_path, "w") as f:
            f.write("# zen component registry\n.zen/\n")
        logger.info("Created .gitignore")

def main():
    """Entry point for the CLI"""
    cli()

if __name__ == "__main__":
    main()
