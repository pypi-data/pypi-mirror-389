"""
Template utilities for zen.

This module provides utility functions for template management,
including integrity checking, dependency analysis, and template
maintenance operations.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from zen.schemas.template import TemplateSchema
from zen.core.template_registry import TemplateRegistry
from zen.core.template_validator import TemplateValidator, ValidationResult
from zen.core.logger import get_logger

logger = get_logger()


class TemplateIntegrityChecker:
    """Checks template file integrity and consistency."""
    
    def __init__(self):
        """Initialize integrity checker."""
        self.registry = TemplateRegistry()
        self.validator = TemplateValidator(self.registry)
    
    def check_template_integrity(self, template_name: str) -> ValidationResult:
        """Check integrity of a specific template.
        
        Args:
            template_name: Name of template to check
            
        Returns:
            Validation result with integrity status
        """
        result = ValidationResult()
        
        try:
            template = self.registry.get_template(template_name)
            
            # Find template directory
            template_path = self._find_template_path(template_name)
            if not template_path:
                result.add_error(f"Template directory not found for {template_name}")
                return result
            
            # Check directory integrity
            dir_result = self.validator.validate_template_integrity(template_path)
            result.merge(dir_result)
            
            # Check file integrity
            file_result = self._check_file_integrity(template, template_path)
            result.merge(file_result)
            
            # Check template.json consistency
            json_result = self._check_template_json_consistency(template, template_path)
            result.merge(json_result)
            
        except Exception as e:
            result.add_error(f"Integrity check failed: {e}")
        
        return result
    
    def check_all_templates_integrity(self) -> Dict[str, ValidationResult]:
        """Check integrity of all templates.
        
        Returns:
            Dictionary mapping template names to integrity results
        """
        results = {}
        templates = self.registry.list_templates()
        
        for template in templates:
            results[template.name] = self.check_template_integrity(template.name)
        
        return results
    
    def generate_template_checksums(self, template_name: str) -> Dict[str, str]:
        """Generate checksums for all template files.
        
        Args:
            template_name: Name of template
            
        Returns:
            Dictionary mapping file paths to checksums
        """
        checksums = {}
        
        try:
            template = self.registry.get_template(template_name)
            template_path = self._find_template_path(template_name)
            
            if not template_path:
                return checksums
            
            for file_info in template.files:
                if hasattr(file_info, 'content_path') and file_info.content_path:
                    content_path = Path(file_info.content_path)
                    if not content_path.is_absolute():
                        content_path = template_path / file_info.content_path
                    
                    if content_path.exists():
                        checksum = self._calculate_file_checksum(content_path)
                        checksums[file_info.path] = checksum
        
        except Exception as e:
            logger.warning(f"Failed to generate checksums for {template_name}: {e}")
        
        return checksums
    
    def _find_template_path(self, template_name: str) -> Optional[Path]:
        """Find the filesystem path for a template.
        
        Args:
            template_name: Name of template
            
        Returns:
            Path to template directory or None if not found
        """
        # Look in standard template locations
        possible_paths = [
            Path("zen/templates") / template_name,
            Path("templates") / template_name,
            Path(".") / template_name
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_dir():
                template_json = path / "template.json"
                if template_json.exists():
                    return path
        
        return None
    
    def _check_file_integrity(self, template: TemplateSchema, template_path: Path) -> ValidationResult:
        """Check integrity of template files.
        
        Args:
            template: Template schema
            template_path: Path to template directory
            
        Returns:
            Validation result
        """
        result = ValidationResult()
        
        for file_info in template.files:
            if hasattr(file_info, 'content_path') and file_info.content_path:
                content_path = Path(file_info.content_path)
                if not content_path.is_absolute():
                    content_path = template_path / file_info.content_path
                
                if not content_path.exists():
                    result.add_error(f"Template file missing: {content_path}")
                elif content_path.is_dir():
                    result.add_error(f"Template file is a directory: {content_path}")
                else:
                    # Check file is readable
                    try:
                        with open(content_path, 'rb') as f:
                            f.read(1)  # Try to read first byte
                    except Exception as e:
                        result.add_error(f"Cannot read template file {content_path}: {e}")
        
        return result
    
    def _check_template_json_consistency(self, template: TemplateSchema, template_path: Path) -> ValidationResult:
        """Check consistency between template schema and template.json.
        
        Args:
            template: Template schema
            template_path: Path to template directory
            
        Returns:
            Validation result
        """
        result = ValidationResult()
        
        template_json_path = template_path / "template.json"
        if not template_json_path.exists():
            result.add_error("template.json file missing")
            return result
        
        try:
            with open(template_json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Check basic fields match
            if json_data.get('name') != template.name:
                result.add_error(f"Name mismatch: schema='{template.name}', json='{json_data.get('name')}'")
            
            if json_data.get('version') != template.version:
                result.add_error(f"Version mismatch: schema='{template.version}', json='{json_data.get('version')}'")
            
            if json_data.get('description') != template.description:
                result.add_warning(f"Description mismatch between schema and JSON")
            
            # Check file lists consistency
            json_files = {f.get('path') for f in json_data.get('files', [])}
            schema_files = {f.path for f in template.files}
            
            missing_in_json = schema_files - json_files
            missing_in_schema = json_files - schema_files
            
            if missing_in_json:
                result.add_error(f"Files in schema but not in JSON: {missing_in_json}")
            
            if missing_in_schema:
                result.add_error(f"Files in JSON but not in schema: {missing_in_schema}")
        
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON in template.json: {e}")
        except Exception as e:
            result.add_error(f"Failed to check template.json consistency: {e}")
        
        return result
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hexadecimal checksum string
        """
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
        except Exception:
            return ""
        
        return sha256_hash.hexdigest()


class TemplateDependencyAnalyzer:
    """Analyzes template dependencies and conflicts."""
    
    def __init__(self):
        """Initialize dependency analyzer."""
        self.registry = TemplateRegistry()
    
    def analyze_template_dependencies(self, template_name: str) -> Dict[str, Any]:
        """Analyze dependencies for a template.
        
        Args:
            template_name: Name of template to analyze
            
        Returns:
            Dictionary with dependency analysis results
        """
        try:
            template = self.registry.get_template(template_name)
            resolved_template = self.registry.resolve_inheritance(template)
            
            analysis = {
                "template_name": template_name,
                "direct_dependencies": template.dependencies,
                "direct_dev_dependencies": template.dev_dependencies,
                "resolved_dependencies": resolved_template.dependencies,
                "resolved_dev_dependencies": resolved_template.dev_dependencies,
                "dependency_count": len(resolved_template.dependencies),
                "dev_dependency_count": len(resolved_template.dev_dependencies),
                "conflicts": [],
                "recommendations": []
            }
            
            # Check for version conflicts
            conflicts = self._find_dependency_conflicts(resolved_template.dependencies)
            analysis["conflicts"] = conflicts
            
            # Generate recommendations
            recommendations = self._generate_dependency_recommendations(resolved_template)
            analysis["recommendations"] = recommendations
            
            return analysis
            
        except Exception as e:
            return {
                "template_name": template_name,
                "error": str(e),
                "conflicts": [],
                "recommendations": []
            }
    
    def analyze_all_template_dependencies(self) -> Dict[str, Dict[str, Any]]:
        """Analyze dependencies for all templates.
        
        Returns:
            Dictionary mapping template names to dependency analysis
        """
        results = {}
        templates = self.registry.list_templates()
        
        for template in templates:
            results[template.name] = self.analyze_template_dependencies(template.name)
        
        return results
    
    def find_dependency_conflicts_between_templates(self) -> List[Dict[str, Any]]:
        """Find dependency conflicts between different templates.
        
        Returns:
            List of conflict descriptions
        """
        conflicts = []
        templates = self.registry.list_templates()
        
        # Compare each pair of templates
        for i, template1 in enumerate(templates):
            for template2 in templates[i+1:]:
                try:
                    resolved1 = self.registry.resolve_inheritance(template1)
                    resolved2 = self.registry.resolve_inheritance(template2)
                    
                    # Find common dependencies with different versions
                    deps1 = self._parse_dependencies(resolved1.dependencies)
                    deps2 = self._parse_dependencies(resolved2.dependencies)
                    
                    common_packages = set(deps1.keys()) & set(deps2.keys())
                    
                    for package in common_packages:
                        if deps1[package] != deps2[package]:
                            conflicts.append({
                                "package": package,
                                "template1": template1.name,
                                "version1": deps1[package],
                                "template2": template2.name,
                                "version2": deps2[package]
                            })
                
                except Exception as e:
                    logger.warning(f"Failed to compare {template1.name} and {template2.name}: {e}")
        
        return conflicts
    
    def _find_dependency_conflicts(self, dependencies: List[str]) -> List[Dict[str, Any]]:
        """Find conflicts within a single dependency list.
        
        Args:
            dependencies: List of dependency specifications
            
        Returns:
            List of conflict descriptions
        """
        conflicts = []
        parsed_deps = self._parse_dependencies(dependencies)
        
        # Check for duplicate packages with different versions
        package_versions = {}
        for dep in dependencies:
            package_name = self._extract_package_name(dep)
            if package_name in package_versions:
                if package_versions[package_name] != dep:
                    conflicts.append({
                        "package": package_name,
                        "version1": package_versions[package_name],
                        "version2": dep,
                        "type": "duplicate_with_different_versions"
                    })
            else:
                package_versions[package_name] = dep
        
        return conflicts
    
    def _generate_dependency_recommendations(self, template: TemplateSchema) -> List[str]:
        """Generate dependency recommendations for a template.
        
        Args:
            template: Template schema
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Check for common missing dependencies based on template type
        if "fastapi" in template.name.lower():
            fastapi_deps = [dep for dep in template.dependencies if "fastapi" in dep.lower()]
            if not fastapi_deps:
                recommendations.append("Consider adding FastAPI as a dependency")
            
            uvicorn_deps = [dep for dep in template.dependencies if "uvicorn" in dep.lower()]
            if not uvicorn_deps:
                recommendations.append("Consider adding uvicorn for development server")
        
        # Check for security-related dependencies
        security_packages = ["cryptography", "bcrypt", "passlib"]
        has_security = any(any(pkg in dep.lower() for pkg in security_packages) for dep in template.dependencies)
        
        if template.complexity in ["moderate", "industry"] and not has_security:
            recommendations.append("Consider adding security-related packages for authentication")
        
        # Check for testing dependencies
        test_packages = ["pytest", "unittest", "nose"]
        has_testing = any(any(pkg in dep.lower() for pkg in test_packages) for dep in template.dev_dependencies)
        
        if not has_testing:
            recommendations.append("Consider adding testing framework to dev dependencies")
        
        return recommendations
    
    def _parse_dependencies(self, dependencies: List[str]) -> Dict[str, str]:
        """Parse dependency list into package name -> version mapping.
        
        Args:
            dependencies: List of dependency specifications
            
        Returns:
            Dictionary mapping package names to version specs
        """
        parsed = {}
        
        for dep in dependencies:
            package_name = self._extract_package_name(dep)
            parsed[package_name] = dep
        
        return parsed
    
    def _extract_package_name(self, dependency: str) -> str:
        """Extract package name from dependency specification.
        
        Args:
            dependency: Dependency specification (e.g., "fastapi>=0.104.0")
            
        Returns:
            Package name
        """
        import re
        
        # Remove version specifiers and extras
        match = re.match(r'^([a-zA-Z0-9\-_\.]+)', dependency)
        if match:
            return match.group(1)
        
        return dependency


class TemplateMaintenanceUtils:
    """Utilities for template maintenance and updates."""
    
    def __init__(self):
        """Initialize maintenance utilities."""
        self.registry = TemplateRegistry()
        self.integrity_checker = TemplateIntegrityChecker()
        self.dependency_analyzer = TemplateDependencyAnalyzer()
    
    def generate_template_report(self, template_name: str) -> Dict[str, Any]:
        """Generate comprehensive report for a template.
        
        Args:
            template_name: Name of template
            
        Returns:
            Dictionary with template report
        """
        report = {
            "template_name": template_name,
            "timestamp": self._get_current_timestamp(),
            "integrity": {},
            "dependencies": {},
            "validation": {},
            "recommendations": []
        }
        
        try:
            # Integrity check
            integrity_result = self.integrity_checker.check_template_integrity(template_name)
            report["integrity"] = {
                "is_valid": integrity_result.is_valid,
                "errors": integrity_result.errors,
                "warnings": integrity_result.warnings,
                "info": integrity_result.info
            }
            
            # Dependency analysis
            dep_analysis = self.dependency_analyzer.analyze_template_dependencies(template_name)
            report["dependencies"] = dep_analysis
            
            # Validation
            from zen.core.template_validator import TemplateValidator
            validator = TemplateValidator(self.registry)
            template = self.registry.get_template(template_name)
            validation_result = validator.validate_template(template)
            
            report["validation"] = {
                "is_valid": validation_result.is_valid,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "info": validation_result.info
            }
            
            # Generate recommendations
            recommendations = []
            
            if not integrity_result.is_valid:
                recommendations.append("Fix integrity issues before using template")
            
            if not validation_result.is_valid:
                recommendations.append("Address validation errors")
            
            if dep_analysis.get("conflicts"):
                recommendations.append("Resolve dependency conflicts")
            
            recommendations.extend(dep_analysis.get("recommendations", []))
            
            report["recommendations"] = recommendations
            
        except Exception as e:
            report["error"] = str(e)
        
        return report
    
    def generate_all_templates_report(self) -> Dict[str, Any]:
        """Generate comprehensive report for all templates.
        
        Returns:
            Dictionary with overall template system report
        """
        templates = self.registry.list_templates()
        
        report = {
            "timestamp": self._get_current_timestamp(),
            "template_count": len(templates),
            "templates": {},
            "summary": {
                "valid_templates": 0,
                "templates_with_errors": 0,
                "templates_with_warnings": 0,
                "total_errors": 0,
                "total_warnings": 0
            },
            "global_conflicts": []
        }
        
        # Generate individual template reports
        for template in templates:
            template_report = self.generate_template_report(template.name)
            report["templates"][template.name] = template_report
            
            # Update summary
            if template_report.get("validation", {}).get("is_valid", False):
                report["summary"]["valid_templates"] += 1
            
            errors = len(template_report.get("validation", {}).get("errors", []))
            warnings = len(template_report.get("validation", {}).get("warnings", []))
            
            if errors > 0:
                report["summary"]["templates_with_errors"] += 1
            
            if warnings > 0:
                report["summary"]["templates_with_warnings"] += 1
            
            report["summary"]["total_errors"] += errors
            report["summary"]["total_warnings"] += warnings
        
        # Find global conflicts
        global_conflicts = self.dependency_analyzer.find_dependency_conflicts_between_templates()
        report["global_conflicts"] = global_conflicts
        
        return report
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            Current timestamp as ISO string
        """
        from datetime import datetime
        return datetime.now().isoformat()