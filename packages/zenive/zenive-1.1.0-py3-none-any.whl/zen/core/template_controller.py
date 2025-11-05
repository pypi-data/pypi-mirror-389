"""
Template controller for zen - orchestrates template operations.

This module provides the TemplateController class that coordinates between
the CLI, template registry, and project initializer to provide a unified
interface for template-based project creation.
"""

import click
from pathlib import Path
from typing import Dict, List, Optional, Any, NamedTuple
from zen.core.template_registry import TemplateRegistry
from zen.core.project_initializer import ProjectInitializer, ProjectResult
from zen.schemas.template import TemplateSchema
from zen.core.logger import get_logger
from zen.core.exceptions import ConfigurationError

logger = get_logger()


class TemplateInfo(NamedTuple):
    """Template information for display."""
    name: str
    version: str
    description: str
    complexity: str
    category: str
    file_count: int
    dependency_count: int


class TemplateDetails(NamedTuple):
    """Detailed template information."""
    name: str
    version: str
    description: str
    complexity: str
    category: str
    extends: Optional[str]
    dependencies: List[str]
    dev_dependencies: List[str]
    directories: List[str]
    files: List[str]
    template_vars: Dict[str, Any]
    python_requires: str
    author: Optional[str]
    license: str
    keywords: List[str]


class TemplateController:
    """Orchestrates template operations."""
    
    def __init__(self):
        """Initialize template controller."""
        self.registry = TemplateRegistry()
        self.initializer = ProjectInitializer(self.registry)
        logger.debug("Template controller initialized")
    
    def list_available_templates(self) -> List[TemplateInfo]:
        """Get list of available templates with basic information.
        
        Returns:
            List of template information objects
        """
        templates = self.registry.list_templates()
        template_infos = []
        
        for template in templates:
            try:
                resolved_template = self.registry.resolve_inheritance(template)
                template_info = TemplateInfo(
                    name=template.name,
                    version=template.version,
                    description=template.description,
                    complexity=template.complexity,
                    category=template.category,
                    file_count=len(resolved_template.files),
                    dependency_count=len(resolved_template.dependencies)
                )
                template_infos.append(template_info)
            except Exception as e:
                logger.warning(f"Failed to get info for template {template.name}: {e}")
        
        # Sort by complexity and name
        complexity_order = {"minimal": 0, "moderate": 1, "industry": 2}
        template_infos.sort(key=lambda t: (complexity_order.get(t.complexity, 99), t.name))
        
        return template_infos
    
    def get_template_details(self, template_name: str) -> TemplateDetails:
        """Get detailed information about a template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Detailed template information
            
        Raises:
            KeyError: If template not found
        """
        template = self.registry.get_template(template_name)
        resolved_template = self.registry.resolve_inheritance(template)
        
        return TemplateDetails(
            name=template.name,
            version=template.version,
            description=template.description,
            complexity=template.complexity,
            category=template.category,
            extends=template.extends,
            dependencies=resolved_template.dependencies,
            dev_dependencies=resolved_template.dev_dependencies,
            directories=resolved_template.directories,
            files=[f.name for f in resolved_template.files],
            template_vars=resolved_template.template_vars,
            python_requires=resolved_template.python_requires,
            author=template.author,
            license=template.license,
            keywords=template.keywords
        )
    
    def validate_project_name(self, project_name: str) -> List[str]:
        """Validate project name.
        
        Args:
            project_name: Project name to validate
            
        Returns:
            List of validation issues (empty if valid)
        """
        return self.initializer.validate_project_name(project_name)
    
    def check_project_directory_conflict(self, project_name: str, target_directory: Optional[str] = None) -> bool:
        """Check if project directory already exists.
        
        Args:
            project_name: Name of the project
            target_directory: Target directory (defaults to current directory)
            
        Returns:
            True if directory already exists (conflict)
        """
        return not self.initializer.check_project_directory_availability(project_name, target_directory)
    
    def collect_user_preferences(self) -> Dict[str, Any]:
        """Collect general user preferences for project creation.
        
        Returns:
            Dictionary of user preferences
        """
        preferences = {}
        
        logger.info("🔧 Project Preferences:")
        logger.info("(These settings will be applied to your project)")
        logger.info("")
        
        try:
            # Ask about dependency installation
            preferences["install_dependencies"] = click.confirm(
                "Install dependencies automatically?", 
                default=True
            )
            
            # Ask about virtual environment
            preferences["create_venv"] = click.confirm(
                "Create virtual environment?", 
                default=True
            )
            
            # Ask about git initialization
            preferences["init_git"] = click.confirm(
                "Initialize git repository?", 
                default=True
            )
            
            # Ask about development tools
            preferences["include_dev_tools"] = click.confirm(
                "Include development tools (linting, formatting)?", 
                default=True
            )
            
        except click.Abort:
            # Use defaults if user cancels
            preferences = {
                "install_dependencies": True,
                "create_venv": True,
                "init_git": True,
                "include_dev_tools": True
            }
        
        return preferences
    
    def validate_template_variables(self, template_name: str, variables: Dict[str, Any]) -> List[str]:
        """Validate template variables against template requirements.
        
        Args:
            template_name: Name of the template
            variables: Template variables to validate
            
        Returns:
            List of validation issues (empty if valid)
        """
        try:
            template = self.registry.get_template(template_name)
            resolved_template = self.registry.resolve_inheritance(template)
            
            issues = []
            
            # Check required variables
            for var_name, var_config in resolved_template.template_vars.items():
                if isinstance(var_config, dict):
                    required = var_config.get("required", False)
                    if required and (var_name not in variables or not variables[var_name]):
                        issues.append(f"Required variable '{var_name}' is missing or empty")
                    
                    # Validate choices
                    choices = var_config.get("choices")
                    if choices and var_name in variables:
                        value = variables[var_name]
                        if value not in choices and str(value) not in map(str, choices):
                            issues.append(f"Variable '{var_name}' must be one of: {', '.join(map(str, choices))}")
                    
                    # Validate type
                    expected_type = var_config.get("type")
                    if expected_type and var_name in variables:
                        value = variables[var_name]
                        if expected_type == "int" and not isinstance(value, int):
                            try:
                                int(value)
                            except (ValueError, TypeError):
                                issues.append(f"Variable '{var_name}' must be an integer")
                        elif expected_type == "float" and not isinstance(value, (int, float)):
                            try:
                                float(value)
                            except (ValueError, TypeError):
                                issues.append(f"Variable '{var_name}' must be a number")
                        elif expected_type == "bool" and not isinstance(value, bool):
                            if str(value).lower() not in ["true", "false", "yes", "no", "1", "0"]:
                                issues.append(f"Variable '{var_name}' must be a boolean value")
            
            return issues
            
        except Exception as e:
            return [f"Template validation error: {e}"]
    
    def create_project_interactive(self, project_name: str, template_name: Optional[str] = None) -> ProjectResult:
        """Create a project with interactive template selection and customization.
        
        Args:
            project_name: Name of the project to create
            template_name: Optional template name (if not provided, user will be prompted)
            
        Returns:
            Project creation result
        """
        try:
            # Validate project name
            name_issues = self.validate_project_name(project_name)
            if name_issues:
                logger.error("Invalid project name:")
                for issue in name_issues:
                    logger.error(f"  • {issue}")
                return ProjectResult(
                    project_name=project_name,
                    project_path=Path(),
                    template_name="",
                    template_version="",
                    files_created=0,
                    directories_created=0,
                    dependencies_installed=False,
                    success=False,
                    message="Invalid project name"
                )
            
            # Check for directory conflicts
            if self.check_project_directory_conflict(project_name):
                logger.error(f"Directory '{project_name}' already exists in current location")
                if not click.confirm("Overwrite existing directory?", default=False):
                    return ProjectResult(
                        project_name=project_name,
                        project_path=Path(),
                        template_name="",
                        template_version="",
                        files_created=0,
                        directories_created=0,
                        dependencies_installed=False,
                        success=False,
                        message="Directory conflict - user cancelled"
                    )
                
                # Remove existing directory
                import shutil
                existing_path = Path.cwd() / project_name
                shutil.rmtree(existing_path)
                logger.info(f"Removed existing directory: {existing_path}")
            
            # Select template if not provided
            if not template_name:
                template_name = self._interactive_template_selection()
                if not template_name:
                    return ProjectResult(
                        project_name=project_name,
                        project_path=Path(),
                        template_name="",
                        template_version="",
                        files_created=0,
                        directories_created=0,
                        dependencies_installed=False,
                        success=False,
                        message="No template selected"
                    )
            
            # Validate template exists
            try:
                template = self.registry.get_template(template_name)
            except KeyError:
                logger.error(f"Template '{template_name}' not found")
                return ProjectResult(
                    project_name=project_name,
                    project_path=Path(),
                    template_name=template_name,
                    template_version="",
                    files_created=0,
                    directories_created=0,
                    dependencies_installed=False,
                    success=False,
                    message=f"Template '{template_name}' not found"
                )
            
            # Collect user preferences
            user_preferences = self.collect_user_preferences()
            
            # Gather template customization options
            template_variables = self._gather_template_customization(template)
            
            # Validate template variables
            validation_issues = self.validate_template_variables(template_name, template_variables)
            if validation_issues:
                logger.error("Template variable validation failed:")
                for issue in validation_issues:
                    logger.error(f"  • {issue}")
                return ProjectResult(
                    project_name=project_name,
                    project_path=Path(),
                    template_name=template_name,
                    template_version=template.version,
                    files_created=0,
                    directories_created=0,
                    dependencies_installed=False,
                    success=False,
                    message="Template variable validation failed"
                )
            
            # Show creation summary and confirm
            self._show_creation_summary(project_name, template, template_variables, user_preferences)
            if not click.confirm("Create project?", default=True):
                return ProjectResult(
                    project_name=project_name,
                    project_path=Path(),
                    template_name=template_name,
                    template_version=template.version,
                    files_created=0,
                    directories_created=0,
                    dependencies_installed=False,
                    success=False,
                    message="Project creation cancelled by user"
                )
            
            # Create the project
            logger.info("")
            result = self.initializer.create_project(
                project_name=project_name,
                template_name=template_name,
                template_variables=template_variables,
                install_dependencies=user_preferences.get("install_dependencies", True),
                create_venv=user_preferences.get("create_venv", True)
            )
            
            if result.success:
                # Handle additional setup based on preferences
                if user_preferences.get("init_git", True):
                    self._initialize_git_repository(result.project_path)
                
                self._show_success_message(result, user_preferences)
            
            return result
            
        except Exception as e:
            logger.error(f"Project creation failed: {e}")
            return ProjectResult(
                project_name=project_name,
                project_path=Path(),
                template_name=template_name or "",
                template_version="",
                files_created=0,
                directories_created=0,
                dependencies_installed=False,
                success=False,
                message=str(e)
            )
    
    def _interactive_template_selection(self) -> Optional[str]:
        """Interactive template selection interface.
        
        Returns:
            Selected template name or None if cancelled
        """
        templates = self.list_available_templates()
        
        if not templates:
            logger.error("No templates available")
            return None
        
        logger.info("Available templates:")
        logger.info("")
        
        # Display templates in a nice format
        from rich.table import Table
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Index", style="dim", width=6)
        table.add_column("Name", style="green", no_wrap=True)
        table.add_column("Complexity", style="yellow", width=12)
        table.add_column("Description", style="white")
        table.add_column("Files", style="blue", width=8)
        
        for i, template in enumerate(templates, 1):
            table.add_row(
                str(i),
                template.name,
                template.complexity.title(),
                template.description,
                str(template.file_count)
            )
        
        logger.console.print(table)
        logger.info("")
        
        # Get user selection
        while True:
            try:
                choice = click.prompt(
                    f"Select template (1-{len(templates)}) or 'q' to quit",
                    type=str
                )
                
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(templates):
                    selected_template = templates[index]
                    logger.info(f"Selected: {selected_template.name} ({selected_template.complexity})")
                    return selected_template.name
                else:
                    logger.error(f"Invalid selection. Please choose 1-{len(templates)}")
                    
            except ValueError:
                logger.error("Invalid input. Please enter a number or 'q'")
            except click.Abort:
                return None
    
    def _gather_template_customization(self, template: TemplateSchema) -> Dict[str, Any]:
        """Gather template customization options from user.
        
        Args:
            template: Template schema
            
        Returns:
            Dictionary of template variables
        """
        variables = {}
        
        # Get resolved template to see all available variables
        resolved_template = self.registry.resolve_inheritance(template)
        
        if not resolved_template.template_vars:
            logger.debug("No template variables to customize")
            return variables
        
        logger.info("")
        logger.info("🎨 Template customization options:")
        logger.info("(Press Enter to use default values)")
        logger.info("")
        
        # Group variables by category for better organization
        categorized_vars = self._categorize_template_variables(resolved_template.template_vars)
        
        for category, vars_in_category in categorized_vars.items():
            if category != "general":
                logger.info(f"📋 {category.title()} Settings:")
            
            for var_name, var_config in vars_in_category.items():
                # Skip standard variables that are auto-generated
                if var_name.startswith("project_name"):
                    continue
                
                try:
                    value = self._prompt_for_variable(var_name, var_config)
                    variables[var_name] = value
                    
                except click.Abort:
                    # User cancelled, use default
                    variables[var_name] = var_config.get("default", "")
            
            if category != "general" and len(categorized_vars) > 1:
                logger.info("")
        
        # Show customization preview
        if variables:
            self._show_customization_preview(variables)
        
        return variables
    
    def _categorize_template_variables(self, template_vars: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Categorize template variables for better organization.
        
        Args:
            template_vars: Template variables dictionary
            
        Returns:
            Dictionary of categorized variables
        """
        categories = {
            "database": {},
            "authentication": {},
            "deployment": {},
            "monitoring": {},
            "general": {}
        }
        
        for var_name, default_value in template_vars.items():
            var_config = self._parse_variable_config(var_name, default_value)
            
            # Categorize based on variable name patterns
            var_lower = var_name.lower()
            if any(keyword in var_lower for keyword in ["db", "database", "postgres", "mysql", "sqlite"]):
                categories["database"][var_name] = var_config
            elif any(keyword in var_lower for keyword in ["auth", "jwt", "oauth", "login", "user"]):
                categories["authentication"][var_name] = var_config
            elif any(keyword in var_lower for keyword in ["docker", "k8s", "kubernetes", "deploy", "port"]):
                categories["deployment"][var_name] = var_config
            elif any(keyword in var_lower for keyword in ["monitor", "log", "metric", "sentry", "prometheus"]):
                categories["monitoring"][var_name] = var_config
            else:
                categories["general"][var_name] = var_config
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def _parse_variable_config(self, var_name: str, default_value: Any) -> Dict[str, Any]:
        """Parse variable configuration from default value.
        
        Args:
            var_name: Variable name
            default_value: Default value (can be simple value or config dict)
            
        Returns:
            Variable configuration dictionary
        """
        if isinstance(default_value, dict) and "default" in default_value:
            # Advanced configuration format
            return default_value
        else:
            # Simple default value format
            return {
                "default": default_value,
                "type": type(default_value).__name__,
                "description": self._generate_variable_description(var_name)
            }
    
    def _generate_variable_description(self, var_name: str) -> str:
        """Generate a human-readable description for a variable.
        
        Args:
            var_name: Variable name
            
        Returns:
            Human-readable description
        """
        # Convert snake_case to readable format
        words = var_name.replace("_", " ").split()
        return " ".join(word.capitalize() for word in words)
    
    def _prompt_for_variable(self, var_name: str, var_config: Dict[str, Any]) -> Any:
        """Prompt user for a template variable value.
        
        Args:
            var_name: Variable name
            var_config: Variable configuration
            
        Returns:
            User-provided value
        """
        default_value = var_config.get("default", "")
        description = var_config.get("description", self._generate_variable_description(var_name))
        var_type = var_config.get("type", "str")
        choices = var_config.get("choices")
        
        # Create prompt text
        prompt_text = f"  {description}"
        if choices:
            prompt_text += f" ({'/'.join(map(str, choices))})"
        
        try:
            if choices:
                # Multiple choice variable
                while True:
                    value = click.prompt(prompt_text, default=str(default_value))
                    if value in choices or str(value) in map(str, choices):
                        return type(default_value)(value) if default_value else value
                    else:
                        logger.error(f"Invalid choice. Please select from: {', '.join(map(str, choices))}")
            
            elif isinstance(default_value, bool) or var_type == "bool":
                # Boolean variable
                return click.confirm(prompt_text, default=bool(default_value))
            
            elif isinstance(default_value, (int, float)) or var_type in ["int", "float"]:
                # Numeric variable
                target_type = type(default_value) if default_value else (int if var_type == "int" else float)
                return click.prompt(prompt_text, default=default_value, type=target_type)
            
            else:
                # String variable
                value = click.prompt(prompt_text, default=str(default_value))
                return value
                
        except click.Abort:
            return default_value
    
    def _show_customization_preview(self, variables: Dict[str, Any]) -> None:
        """Show a preview of the customization choices.
        
        Args:
            variables: Template variables dictionary
        """
        if not variables:
            return
        
        logger.info("")
        logger.info("📋 Customization Summary:")
        
        from rich.table import Table
        
        table = Table(show_header=True, header_style="bold cyan", box=None)
        table.add_column("Setting", style="green", no_wrap=True)
        table.add_column("Value", style="white")
        
        for key, value in variables.items():
            if not key.startswith("project_name"):
                # Format the key for display
                display_key = self._generate_variable_description(key)
                display_value = str(value)
                
                # Truncate long values
                if len(display_value) > 50:
                    display_value = display_value[:47] + "..."
                
                table.add_row(display_key, display_value)
        
        logger.console.print(table)
        logger.info("")
    
    def _show_creation_summary(self, project_name: str, template: TemplateSchema, variables: Dict[str, Any], preferences: Dict[str, Any]) -> None:
        """Show project creation summary.
        
        Args:
            project_name: Name of the project
            template: Template schema
            variables: Template variables
            preferences: User preferences
        """
        logger.info("")
        logger.info("📋 Project Creation Summary:")
        logger.info("")
        
        from rich.table import Table
        
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        
        table.add_row("Project name", project_name)
        table.add_row("Template", f"{template.name} v{template.version}")
        table.add_row("Complexity", template.complexity.title())
        table.add_row("Location", str(Path.cwd() / project_name))
        
        # Add preferences
        table.add_row("Install dependencies", "Yes" if preferences.get("install_dependencies", True) else "No")
        table.add_row("Create virtual env", "Yes" if preferences.get("create_venv", True) else "No")
        table.add_row("Initialize git", "Yes" if preferences.get("init_git", True) else "No")
        
        logger.console.print(table)
        
        if variables:
            filtered_vars = {k: v for k, v in variables.items() if not k.startswith("project_name")}
            if filtered_vars:
                logger.info("")
                logger.info("🎨 Template Customizations:")
                
                custom_table = Table(show_header=False, box=None, padding=(0, 2))
                custom_table.add_column("Setting", style="green", no_wrap=True)
                custom_table.add_column("Value", style="white")
                
                for key, value in filtered_vars.items():
                    display_key = self._generate_variable_description(key)
                    custom_table.add_row(display_key, str(value))
                
                logger.console.print(custom_table)
        
        logger.info("")
    
    def _show_success_message(self, result: ProjectResult, preferences: Optional[Dict[str, Any]] = None) -> None:
        """Show success message with next steps.
        
        Args:
            result: Project creation result
            preferences: User preferences used during creation
        """
        if preferences is None:
            preferences = {}
        logger.info("")
        logger.success("🎉 Project created successfully!")
        logger.info("")
        logger.info("Next steps:")
        logger.info(f"  1. cd {result.project_name}")
        
        if result.dependencies_installed:
            logger.info("  2. Activate virtual environment:")
            if Path.cwd().name != "Windows":
                logger.info(f"     source venv/bin/activate")
            else:
                logger.info(f"     venv\\Scripts\\activate")
        else:
            logger.info("  2. Create virtual environment and install dependencies:")
            logger.info("     python -m venv venv")
            logger.info("     source venv/bin/activate  # or venv\\Scripts\\activate on Windows")
            logger.info("     pip install -r requirements.txt")
        
        # Template-specific instructions
        if "fastapi" in result.template_name.lower():
            logger.info("  3. Run the development server:")
            logger.info("     uvicorn app.main:app --reload")
            logger.info("")
            logger.info("  Your FastAPI app will be available at: http://localhost:8000")
            logger.info("  API documentation: http://localhost:8000/docs")
        
        logger.info("")
        logger.info(f"📁 Project location: {result.project_path}")
    
    def _initialize_git_repository(self, project_path: Path) -> bool:
        """Initialize git repository in the project directory.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            True if git repository was initialized successfully
        """
        try:
            import subprocess
            
            # Initialize git repository
            subprocess.run(
                ["git", "init"], 
                cwd=project_path, 
                check=True, 
                capture_output=True, 
                text=True
            )
            
            # Add initial commit
            subprocess.run(
                ["git", "add", "."], 
                cwd=project_path, 
                check=True, 
                capture_output=True, 
                text=True
            )
            
            subprocess.run(
                ["git", "commit", "-m", "Initial commit from zen template"], 
                cwd=project_path, 
                check=True, 
                capture_output=True, 
                text=True
            )
            
            logger.debug("Git repository initialized successfully")
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"Failed to initialize git repository: {e}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error initializing git: {e}")
            return False