"""
JSON-based component installer for zen.
"""

import json
import os
import requests
from pathlib import Path
from typing import List, Optional
from zen.schemas.component import ComponentSchema, load_component_from_url, load_component_from_json, fetch_file_content
from zen.core.logger import get_logger
from zen.core.exceptions import InstallationError

logger = get_logger()

class ComponentInstaller:
    """Handles installation of JSON-based components."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.requirements_file = self.project_root / "requirements.txt"
        logger.debug(f"Component installer initialized for: {self.project_root}")
    
    def install_from_url(self, url: str, custom_path: Optional[str] = None, overwrite: bool = False) -> dict:
        """
        Install component from JSON URL.
        
        Args:
            url: URL to JSON component definition
            custom_path: Custom installation path (optional)
            overwrite: Whether to overwrite existing files
            
        Returns:
            Installation summary dict
        """
        logger.step(f"Installing component from: {url}")
        
        try:
            # Load component from URL
            component = load_component_from_url(url)
            logger.info(f"Component: {component.name} v{component.version}")
            logger.info(f"Description: {component.description}")
            
            # Install files
            installed_files = self._install_component_files(component, custom_path, overwrite)
            
            # Update dependencies
            added_deps = self._update_dependencies(component.dependencies)
            
            # Update project config
            self._update_project_config(url, component)
            
            return {
                "component": component.name,
                "version": component.version,
                "files_installed": len(installed_files),
                "dependencies_added": len(added_deps),
                "install_path": custom_path or self._get_default_path(component.category)
            }
            
        except Exception as e:
            logger.error(f"Installation failed: {e}")
            raise InstallationError(f"Failed to install component: {e}")
    
    def install_from_json(self, json_content: str, custom_path: Optional[str] = None, overwrite: bool = False) -> dict:
        """
        Install component from JSON string.
        
        Args:
            json_content: JSON component definition
            custom_path: Custom installation path (optional) 
            overwrite: Whether to overwrite existing files
            
        Returns:
            Installation summary dict
        """
        try:
            component = load_component_from_json(json_content)
            logger.info(f"Installing component: {component.name} v{component.version}")
            
            # Install files
            installed_files = self._install_component_files(component, custom_path, overwrite)
            
            # Update dependencies
            added_deps = self._update_dependencies(component.dependencies)
            
            return {
                "component": component.name,
                "version": component.version,
                "files_installed": len(installed_files),
                "dependencies_added": len(added_deps),
                "install_path": custom_path or self._get_default_path(component.category)
            }
            
        except Exception as e:
            logger.error(f"Installation failed: {e}")
            raise InstallationError(f"Failed to install component: {e}")
    
    def _install_component_files(self, component: ComponentSchema, custom_path: Optional[str], overwrite: bool) -> List[str]:
        """Install component files to target locations."""
        installed_files = []
        base_path = Path(custom_path) if custom_path else self._get_default_path(component.category)
        
        logger.progress("Installing component files...")
        
        for file_info in component.files:
            # Determine target file path
            if custom_path:
                # Use custom path as base
                target_path = self.project_root / base_path / file_info.name
            else:
                # Use the path specified in the component
                target_path = self.project_root / file_info.path
            
            # Special handling for requirements.txt - merge instead of overwrite
            if file_info.name == "requirements.txt" and target_path.name == "requirements.txt":
                self._handle_requirements_file(file_info, target_path)
                installed_files.append(str(target_path))
                continue
            
            # Create parent directories
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists
            if target_path.exists() and not overwrite:
                logger.warning(f"File exists, skipping: {target_path}")
                continue
            
            # Write file content. If content is missing but a URL is provided, fetch it.
            try:
                content_to_write = getattr(file_info, "content", None)
                if not content_to_write and getattr(file_info, "url", None):
                    try:
                        content_to_write = fetch_file_content(file_info.url, base=self._get_component_base_url())
                    except Exception as e:
                        logger.error(f"Failed to fetch file {file_info.name} from {file_info.url}: {e}")
                        raise InstallationError(f"Failed to fetch file {file_info.name} from {file_info.url}: {e}")
                
                if content_to_write is None:
                    logger.error(f"No content available for file {file_info.name}")
                    raise InstallationError(f"No content available for file {file_info.name}")

                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(content_to_write)
                
                installed_files.append(str(target_path))
                logger.debug(f"Installed: {file_info.name} -> {target_path}")
                
            except Exception as e:
                logger.error(f"Failed to write file {target_path}: {e}")
                raise InstallationError(f"Failed to write file {target_path}: {e}")
        
        logger.success(f"Installed {len(installed_files)} files")
        return installed_files
    
    def _handle_requirements_file(self, file_info, target_path: Path):
        """Handle requirements.txt files by merging dependencies."""
        try:
            # Get component requirements content
            content_to_merge = getattr(file_info, "content", None)
            if not content_to_merge and getattr(file_info, "url", None):
                content_to_merge = fetch_file_content(file_info.url, base=self._get_component_base_url())
            
            if not content_to_merge:
                return
            
            # Parse component requirements
            component_deps = []
            for line in content_to_merge.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    component_deps.append(line)
            
            if not component_deps:
                return
            
            # Read existing requirements
            existing_deps = self._read_requirements()
            
            # Find new dependencies
            new_deps = []
            for dep in component_deps:
                dep_name = self._extract_package_name(dep)
                if not any(self._extract_package_name(existing) == dep_name for existing in existing_deps):
                    new_deps.append(dep)
            
            if new_deps:
                self._append_requirements(new_deps)
                logger.info(f"Merged {len(new_deps)} dependencies into requirements.txt")
            
        except Exception as e:
            logger.warning(f"Failed to merge requirements.txt: {e}")
    
    def _get_component_base_url(self) -> Optional[str]:
        """Get the base URL for the current component being installed."""
        # This would be set during installation - for now return None
        # In a full implementation, this would be passed through the installation context
        return None
    
    def _update_dependencies(self, dependencies: List[str]) -> List[str]:
        """Update requirements.txt with new dependencies."""
        if not dependencies:
            return []
        
        logger.progress("Updating dependencies...")
        
        # Read existing requirements
        existing_deps = self._read_requirements()
        
        # Find new dependencies
        new_deps = []
        for dep in dependencies:
            dep_name = self._extract_package_name(dep)
            if not any(self._extract_package_name(existing) == dep_name for existing in existing_deps):
                new_deps.append(dep)
        
        if new_deps:
            # Append new dependencies
            self._append_requirements(new_deps)
            logger.info(f"Added {len(new_deps)} new dependencies")
        else:
            logger.info("All dependencies already satisfied")
        
        return new_deps
    
    def _read_requirements(self) -> List[str]:
        """Read existing requirements.txt."""
        if not self.requirements_file.exists():
            return []
        
        with open(self.requirements_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Filter out comments and empty lines
        return [line.strip() for line in lines if line.strip() and not line.startswith('#')]
    
    def _append_requirements(self, new_deps: List[str]):
        """Append new dependencies to requirements.txt."""
        # Create file if it doesn't exist
        if not self.requirements_file.exists():
            self.requirements_file.touch()
        
        with open(self.requirements_file, 'a', encoding='utf-8') as f:
            # Add newline if file doesn't end with one
            if self.requirements_file.stat().st_size > 0:
                with open(self.requirements_file, 'rb') as check_f:
                    check_f.seek(-1, 2)
                    if check_f.read(1) != b'\n':
                        f.write('\n')
            
            # Add dependencies
            for dep in new_deps:
                f.write(f'{dep}\n')
    
    def _extract_package_name(self, dep: str) -> str:
        """Extract package name from dependency specification."""
        import re
        # Extract name before version specifiers
        match = re.match(r'^([a-zA-Z0-9_.-]+)', dep)
        return match.group(1).lower() if match else dep.lower()
    
    def _get_default_path(self, category: str) -> Path:
        """Get default installation path for category."""
        category_paths = {
            "utils": "src/utils",
            "auth": "src/auth", 
            "data": "src/data",
            "ml": "src/models",
            "api": "src/api",
            "web": "src/api",
            "database": "src/database"
        }
        return Path(category_paths.get(category, "src/components"))
    
    def _update_project_config(self, source_url: str, component: ComponentSchema):
        """Update project configuration with installed component."""
        config_path = self.project_root / ".zen" / "config.yaml"
        
        if not config_path.exists():
            logger.warning("No project configuration found")
            return
        
        try:
            import yaml
            
            # Read existing config
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            # Update components section
            if "components" not in config:
                config["components"] = {}
            
            config["components"][component.name] = {
                "name": component.name,
                "version": component.version,
                "source": source_url,
                "category": component.category,
                "dependencies": component.dependencies
            }
            
            # Write updated config
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
                
            logger.debug(f"Updated project configuration for {component.name}")
            
        except Exception as e:
            logger.warning(f"Failed to update project configuration: {e}")
