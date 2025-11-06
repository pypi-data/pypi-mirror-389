"""
GitHub Actions Python Component

A comprehensive suite of pre-configured GitHub Actions workflow templates
for Python development projects.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from zen.core.logger import get_logger
from zen.core.exceptions import InstallationError

__version__ = "1.0.0"
__author__ = "zen"
__description__ = "Comprehensive GitHub Actions workflows for Python development"

logger = get_logger()


class GitHubActionsInstaller:
    """Custom installer for GitHub Actions Python component."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.component_dir = Path(__file__).parent
        self.workflows_dir = self.project_root / ".github" / "workflows"
        self.github_dir = self.project_root / ".github"
        
    def install(self, options: Optional[Dict] = None, overwrite: bool = False) -> Dict:
        """
        Install GitHub Actions workflows with selective options.
        
        Args:
            options: Installation options dict with workflows and configs selections
            overwrite: Whether to overwrite existing files without prompting
            
        Returns:
            Installation summary dict
        """
        logger.step("Installing GitHub Actions Python workflows")
        
        # Load component configuration
        component_config = self._load_component_config()
        
        # Use provided options or defaults from component.json
        install_options = options or component_config.get("installation_options", {})
        
        # Ensure .github/workflows directory exists
        self._ensure_directories()
        
        # Check for existing files and handle conflicts
        conflicts = self._check_file_conflicts(install_options)
        if conflicts and not overwrite:
            resolved_conflicts = self._handle_conflicts(conflicts)
            if not resolved_conflicts:
                logger.warning("Installation cancelled due to file conflicts")
                return {"status": "cancelled", "reason": "file_conflicts"}
        
        # Install selected workflows
        installed_workflows = self._install_workflows(install_options.get("workflows", {}))
        
        # Install selected configuration files
        installed_configs = self._install_configs(install_options.get("configs", {}))
        
        # Generate installation summary
        summary = self._generate_summary(installed_workflows, installed_configs)
        
        logger.success(f"Successfully installed {len(installed_workflows + installed_configs)} files")
        return summary
    
    def _load_component_config(self) -> Dict:
        """Load component.json configuration."""
        config_path = self.component_dir / "component.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise InstallationError(f"Failed to load component configuration: {e}")
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.github_dir,
            self.workflows_dir
        ]
        
        for directory in directories:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {directory}")
    
    def _check_file_conflicts(self, options: Dict) -> List[Tuple[str, Path]]:
        """
        Check for existing files that would be overwritten.
        
        Returns:
            List of (file_type, file_path) tuples for conflicting files
        """
        conflicts = []
        
        # Check workflow files
        workflows = options.get("workflows", {})
        for workflow_name, enabled in workflows.items():
            if enabled:
                workflow_file = self._get_workflow_filename(workflow_name)
                target_path = self.workflows_dir / workflow_file
                if target_path.exists():
                    conflicts.append(("workflow", target_path))
        
        # Check config files
        configs = options.get("configs", {})
        config_mappings = {
            "dependabot": self.github_dir / "dependabot.yml",
            "pre_commit": self.project_root / ".pre-commit-config.yaml",
            "pyproject_template": self.project_root / "pyproject.toml.template"
        }
        
        for config_name, enabled in configs.items():
            if enabled and config_name in config_mappings:
                target_path = config_mappings[config_name]
                if target_path.exists():
                    conflicts.append(("config", target_path))
        
        return conflicts
    
    def _handle_conflicts(self, conflicts: List[Tuple[str, Path]]) -> bool:
        """
        Handle file conflicts by prompting user for resolution.
        
        Returns:
            True if conflicts resolved, False if installation should be cancelled
        """
        logger.warning(f"Found {len(conflicts)} existing files that would be overwritten:")
        
        for file_type, file_path in conflicts:
            logger.warning(f"  - {file_type}: {file_path}")
        
        # In a real implementation, this would prompt the user
        # For now, we'll return False to indicate conflicts need manual resolution
        logger.info("Use --overwrite flag to overwrite existing files")
        return False
    
    def _install_workflows(self, workflow_options: Dict[str, bool]) -> List[str]:
        """Install selected workflow files."""
        installed = []
        workflows_source_dir = self.component_dir / "workflows"
        
        for workflow_name, enabled in workflow_options.items():
            if not enabled:
                continue
                
            source_file = self._get_workflow_filename(workflow_name)
            source_path = workflows_source_dir / source_file
            target_path = self.workflows_dir / source_file
            
            if not source_path.exists():
                logger.warning(f"Workflow template not found: {source_file}")
                continue
            
            try:
                shutil.copy2(source_path, target_path)
                installed.append(source_file)
                logger.debug(f"Installed workflow: {source_file}")
            except Exception as e:
                logger.error(f"Failed to install workflow {source_file}: {e}")
        
        return installed
    
    def _install_configs(self, config_options: Dict[str, bool]) -> List[str]:
        """Install selected configuration files."""
        installed = []
        configs_source_dir = self.component_dir / "configs"
        
        config_mappings = {
            "dependabot": ("dependabot.yml", self.github_dir / "dependabot.yml"),
            "pre_commit": (".pre-commit-config.yaml", self.project_root / ".pre-commit-config.yaml"),
            "pyproject_template": ("pyproject.toml.template", self.project_root / "pyproject.toml.template")
        }
        
        for config_name, enabled in config_options.items():
            if not enabled or config_name not in config_mappings:
                continue
            
            source_file, target_path = config_mappings[config_name]
            source_path = configs_source_dir / source_file
            
            if not source_path.exists():
                logger.warning(f"Config template not found: {source_file}")
                continue
            
            try:
                # Ensure target directory exists
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target_path)
                installed.append(str(target_path.name))
                logger.debug(f"Installed config: {target_path.name}")
            except Exception as e:
                logger.error(f"Failed to install config {source_file}: {e}")
        
        return installed
    
    def _get_workflow_filename(self, workflow_name: str) -> str:
        """Map workflow option name to actual filename."""
        workflow_mappings = {
            "basic_ci": "ci-basic.yml",
            "matrix_ci": "ci-matrix.yml",
            "code_quality": "code-quality.yml",
            "security_scan": "security-scan.yml",
            "publish_pypi": "publish-pypi.yml",
            "publish_testpypi": "publish-testpypi.yml",
            "docs_sphinx": "docs-sphinx.yml",
            "docs_mkdocs": "docs-mkdocs.yml",
            "dependency_update": "dependency-update.yml",
            "performance_test": "performance-test.yml"
        }
        return workflow_mappings.get(workflow_name, f"{workflow_name}.yml")
    
    def _generate_summary(self, workflows: List[str], configs: List[str]) -> Dict:
        """Generate installation summary."""
        return {
            "status": "success",
            "workflows_installed": workflows,
            "configs_installed": configs,
            "total_files": len(workflows) + len(configs),
            "workflows_dir": str(self.workflows_dir),
            "usage_instructions": self._get_usage_instructions(workflows, configs)
        }
    
    def _get_usage_instructions(self, workflows: List[str], configs: List[str]) -> Dict:
        """Generate usage instructions for installed files."""
        instructions = {
            "workflows": {},
            "configs": {},
            "next_steps": []
        }
        
        # Workflow-specific instructions
        workflow_instructions = {
            "ci-basic.yml": "Basic CI workflow will run on push/PR. Customize Python version in the workflow file.",
            "ci-matrix.yml": "Matrix CI tests multiple Python versions and OS. Configure matrix in the workflow file.",
            "code-quality.yml": "Code quality checks run automatically. Install pre-commit hooks for local development.",
            "security-scan.yml": "Security scanning runs weekly. Check Actions tab for vulnerability reports.",
            "publish-pypi.yml": "Set PYPI_API_TOKEN secret in repository settings before using.",
            "publish-testpypi.yml": "Set TEST_PYPI_API_TOKEN secret for TestPyPI publishing.",
            "docs-sphinx.yml": "Configure Sphinx in docs/ directory. Set up GitHub Pages in repository settings.",
            "docs-mkdocs.yml": "Configure MkDocs with mkdocs.yml file. Set up GitHub Pages in repository settings.",
            "dependency-update.yml": "Automated dependency updates. Review and merge PRs as needed.",
            "performance-test.yml": "Performance tests run on schedule. Add pytest-benchmark tests to your project."
        }
        
        for workflow in workflows:
            if workflow in workflow_instructions:
                instructions["workflows"][workflow] = workflow_instructions[workflow]
        
        # Config-specific instructions
        config_instructions = {
            "dependabot.yml": "Dependabot will create PRs for dependency updates automatically.",
            ".pre-commit-config.yaml": "Run 'pre-commit install' to set up local git hooks.",
            "pyproject.toml.template": "Rename to pyproject.toml and customize for your project."
        }
        
        for config in configs:
            if config in config_instructions:
                instructions["configs"][config] = config_instructions[config]
        
        # General next steps
        if workflows:
            instructions["next_steps"].append("Commit and push the workflow files to trigger GitHub Actions")
        if "dependabot.yml" in configs:
            instructions["next_steps"].append("Enable Dependabot in repository settings if not already enabled")
        if ".pre-commit-config.yaml" in configs:
            instructions["next_steps"].append("Install pre-commit hooks: pip install pre-commit && pre-commit install")
        
        return instructions


def install_component(project_root: str = ".", options: Optional[Dict] = None, overwrite: bool = False) -> Dict:
    """
    Convenience function to install GitHub Actions Python component.
    
    Args:
        project_root: Target project directory
        options: Installation options
        overwrite: Whether to overwrite existing files
        
    Returns:
        Installation summary
    """
    installer = GitHubActionsInstaller(project_root)
    return installer.install(options, overwrite)

class WorkflowSelector:
    """Interactive workflow selection utility."""
    
    def __init__(self, installer: GitHubActionsInstaller):
        self.installer = installer
        self.component_config = installer._load_component_config()
    
    def get_available_workflows(self) -> Dict[str, Dict]:
        """Get available workflows with descriptions."""
        return {
            "basic_ci": {
                "name": "Basic CI",
                "description": "Simple CI workflow for single Python version testing",
                "files": ["ci-basic.yml"],
                "recommended_for": "Small projects, quick setup"
            },
            "matrix_ci": {
                "name": "Matrix CI", 
                "description": "Comprehensive testing across multiple Python versions and OS",
                "files": ["ci-matrix.yml"],
                "recommended_for": "Production projects, libraries"
            },
            "code_quality": {
                "name": "Code Quality",
                "description": "Automated code formatting, linting, and type checking",
                "files": ["code-quality.yml"],
                "recommended_for": "All projects"
            },
            "security_scan": {
                "name": "Security Scanning",
                "description": "Security vulnerability detection and code analysis",
                "files": ["security-scan.yml"],
                "recommended_for": "Production projects"
            },
            "publish_pypi": {
                "name": "PyPI Publishing",
                "description": "Automated package publishing to PyPI on releases",
                "files": ["publish-pypi.yml"],
                "recommended_for": "Python packages"
            },
            "publish_testpypi": {
                "name": "TestPyPI Publishing",
                "description": "Test package publishing to TestPyPI",
                "files": ["publish-testpypi.yml"],
                "recommended_for": "Package development"
            },
            "docs_sphinx": {
                "name": "Sphinx Documentation",
                "description": "Build and deploy Sphinx documentation to GitHub Pages",
                "files": ["docs-sphinx.yml"],
                "recommended_for": "Projects with Sphinx docs"
            },
            "docs_mkdocs": {
                "name": "MkDocs Documentation",
                "description": "Build and deploy MkDocs documentation to GitHub Pages",
                "files": ["docs-mkdocs.yml"],
                "recommended_for": "Projects with MkDocs"
            },
            "dependency_update": {
                "name": "Dependency Updates",
                "description": "Automated dependency updates and security scanning",
                "files": ["dependency-update.yml"],
                "recommended_for": "All projects"
            },
            "performance_test": {
                "name": "Performance Testing",
                "description": "Performance benchmarking and regression detection",
                "files": ["performance-test.yml"],
                "recommended_for": "Performance-critical projects"
            }
        }
    
    def get_available_configs(self) -> Dict[str, Dict]:
        """Get available configuration files with descriptions."""
        return {
            "dependabot": {
                "name": "Dependabot Configuration",
                "description": "Automated dependency updates configuration",
                "files": ["dependabot.yml"],
                "location": ".github/dependabot.yml"
            },
            "pre_commit": {
                "name": "Pre-commit Hooks",
                "description": "Local development quality gates and git hooks",
                "files": [".pre-commit-config.yaml"],
                "location": ".pre-commit-config.yaml"
            },
            "pyproject_template": {
                "name": "Modern Python Project Template",
                "description": "Template for modern Python packaging with pyproject.toml",
                "files": ["pyproject.toml.template"],
                "location": "pyproject.toml.template"
            }
        }
    
    def create_preset_configurations(self) -> Dict[str, Dict]:
        """Create preset configurations for common use cases."""
        return {
            "minimal": {
                "name": "Minimal Setup",
                "description": "Basic CI and code quality for small projects",
                "workflows": {
                    "basic_ci": True,
                    "code_quality": True,
                    "matrix_ci": False,
                    "security_scan": False,
                    "publish_pypi": False,
                    "publish_testpypi": False,
                    "docs_sphinx": False,
                    "docs_mkdocs": False,
                    "dependency_update": False,
                    "performance_test": False
                },
                "configs": {
                    "dependabot": False,
                    "pre_commit": True,
                    "pyproject_template": False
                }
            },
            "standard": {
                "name": "Standard Setup",
                "description": "Comprehensive setup for most Python projects",
                "workflows": {
                    "basic_ci": False,
                    "matrix_ci": True,
                    "code_quality": True,
                    "security_scan": True,
                    "publish_pypi": False,
                    "publish_testpypi": False,
                    "docs_sphinx": False,
                    "docs_mkdocs": False,
                    "dependency_update": True,
                    "performance_test": False
                },
                "configs": {
                    "dependabot": True,
                    "pre_commit": True,
                    "pyproject_template": False
                }
            },
            "library": {
                "name": "Python Library",
                "description": "Complete setup for Python libraries and packages",
                "workflows": {
                    "basic_ci": False,
                    "matrix_ci": True,
                    "code_quality": True,
                    "security_scan": True,
                    "publish_pypi": True,
                    "publish_testpypi": True,
                    "docs_sphinx": True,
                    "docs_mkdocs": False,
                    "dependency_update": True,
                    "performance_test": False
                },
                "configs": {
                    "dependabot": True,
                    "pre_commit": True,
                    "pyproject_template": True
                }
            },
            "enterprise": {
                "name": "Enterprise Setup",
                "description": "Full setup with all security and quality features",
                "workflows": {
                    "basic_ci": False,
                    "matrix_ci": True,
                    "code_quality": True,
                    "security_scan": True,
                    "publish_pypi": False,
                    "publish_testpypi": False,
                    "docs_sphinx": True,
                    "docs_mkdocs": False,
                    "dependency_update": True,
                    "performance_test": True
                },
                "configs": {
                    "dependabot": True,
                    "pre_commit": True,
                    "pyproject_template": True
                }
            }
        }
    
    def validate_selection(self, options: Dict) -> Tuple[bool, List[str]]:
        """
        Validate workflow selection for conflicts and dependencies.
        
        Returns:
            (is_valid, list_of_warnings)
        """
        warnings = []
        workflows = options.get("workflows", {})
        configs = options.get("configs", {})
        
        # Check for conflicting CI workflows
        ci_workflows = ["basic_ci", "matrix_ci"]
        enabled_ci = [w for w in ci_workflows if workflows.get(w, False)]
        if len(enabled_ci) > 1:
            warnings.append("Multiple CI workflows selected. Consider using only one CI workflow.")
        
        # Check for conflicting documentation workflows
        doc_workflows = ["docs_sphinx", "docs_mkdocs"]
        enabled_docs = [w for w in doc_workflows if workflows.get(w, False)]
        if len(enabled_docs) > 1:
            warnings.append("Multiple documentation workflows selected. Choose either Sphinx or MkDocs.")
        
        # Check for publishing workflows without CI
        publish_workflows = ["publish_pypi", "publish_testpypi"]
        enabled_publish = [w for w in publish_workflows if workflows.get(w, False)]
        if enabled_publish and not any(workflows.get(w, False) for w in ci_workflows):
            warnings.append("Publishing workflows selected without CI. Consider adding a CI workflow.")
        
        # Check for code quality dependencies
        if workflows.get("code_quality", False) and not configs.get("pre_commit", False):
            warnings.append("Code quality workflow works best with pre-commit hooks. Consider enabling pre_commit config.")
        
        # Check for dependency management
        if workflows.get("dependency_update", False) and not configs.get("dependabot", False):
            warnings.append("Dependency update workflow complements Dependabot configuration.")
        
        return len(warnings) == 0, warnings


def install_with_selection(project_root: str = ".", preset: Optional[str] = None, 
                          custom_options: Optional[Dict] = None, overwrite: bool = False) -> Dict:
    """
    Install GitHub Actions component with workflow selection.
    
    Args:
        project_root: Target project directory
        preset: Preset configuration name (minimal, standard, library, enterprise)
        custom_options: Custom installation options
        overwrite: Whether to overwrite existing files
        
    Returns:
        Installation summary with selection details
    """
    installer = GitHubActionsInstaller(project_root)
    selector = WorkflowSelector(installer)
    
    # Determine installation options
    if preset:
        presets = selector.create_preset_configurations()
        if preset not in presets:
            raise InstallationError(f"Unknown preset: {preset}. Available: {list(presets.keys())}")
        options = presets[preset]
        logger.info(f"Using preset configuration: {preset}")
    elif custom_options:
        options = custom_options
        logger.info("Using custom configuration")
    else:
        # Use default from component.json
        component_config = installer._load_component_config()
        options = component_config.get("installation_options", {})
        logger.info("Using default configuration")
    
    # Validate selection
    is_valid, warnings = selector.validate_selection(options)
    if warnings:
        logger.warning("Configuration warnings:")
        for warning in warnings:
            logger.warning(f"  - {warning}")
    
    # Install with selected options
    result = installer.install(options, overwrite)
    
    # Add selection details to result
    result["preset_used"] = preset
    result["selection_warnings"] = warnings
    result["available_presets"] = list(selector.create_preset_configurations().keys())
    
    return result


def list_available_options() -> Dict:
    """
    List all available workflows, configs, and presets.
    
    Returns:
        Dictionary with available options and descriptions
    """
    installer = GitHubActionsInstaller(".")
    selector = WorkflowSelector(installer)
    
    return {
        "workflows": selector.get_available_workflows(),
        "configs": selector.get_available_configs(),
        "presets": selector.create_preset_configurations()
    }