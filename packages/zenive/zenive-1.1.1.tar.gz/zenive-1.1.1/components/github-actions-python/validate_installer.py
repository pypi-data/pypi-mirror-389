#!/usr/bin/env python3
"""
Simple validation script for the installer logic (no external dependencies).
"""

import json
from pathlib import Path


def validate_component_structure():
    """Validate the component structure and configuration."""
    print("Validating component structure...")
    
    component_dir = Path(__file__).parent
    
    # Check required files exist
    required_files = [
        "__init__.py",
        "installer.py", 
        "component.json",
        "requirements.txt"
    ]
    
    for file_name in required_files:
        file_path = component_dir / file_name
        if not file_path.exists():
            print(f"❌ Missing required file: {file_name}")
            return False
        print(f"✓ Found: {file_name}")
    
    # Check workflows directory
    workflows_dir = component_dir / "workflows"
    if workflows_dir.exists():
        workflow_files = list(workflows_dir.glob("*.yml"))
        print(f"✓ Found {len(workflow_files)} workflow files")
    else:
        print("⚠ Workflows directory not found")
    
    # Check configs directory
    configs_dir = component_dir / "configs"
    if configs_dir.exists():
        config_files = list(configs_dir.glob("*"))
        print(f"✓ Found {len(config_files)} config files")
    else:
        print("⚠ Configs directory not found")
    
    return True


def validate_component_json():
    """Validate component.json structure."""
    print("\nValidating component.json...")
    
    component_dir = Path(__file__).parent
    config_path = component_dir / "component.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check required fields
        required_fields = ["name", "version", "description", "files", "installation_options"]
        for field in required_fields:
            if field not in config:
                print(f"❌ Missing required field: {field}")
                return False
            print(f"✓ Found field: {field}")
        
        # Check installation options structure
        install_opts = config["installation_options"]
        if "workflows" not in install_opts or "configs" not in install_opts:
            print("❌ Missing workflows or configs in installation_options")
            return False
        
        workflows = install_opts["workflows"]
        configs = install_opts["configs"]
        
        print(f"✓ Found {len(workflows)} workflow options")
        print(f"✓ Found {len(configs)} config options")
        
        # Check installer configuration
        if "installer" in config:
            installer_config = config["installer"]
            print(f"✓ Found installer configuration: {installer_config.get('type', 'unknown')}")
        
        # Check presets
        if "presets" in config:
            presets = config["presets"]
            print(f"✓ Found {len(presets)} preset configurations")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading component.json: {e}")
        return False


def validate_installer_code():
    """Validate installer code structure."""
    print("\nValidating installer code...")
    
    component_dir = Path(__file__).parent
    init_path = component_dir / "__init__.py"
    installer_path = component_dir / "installer.py"
    
    try:
        # Check __init__.py for required classes
        with open(init_path, 'r') as f:
            init_content = f.read()
        
        required_classes = ["GitHubActionsInstaller", "WorkflowSelector"]
        required_functions = ["install_component", "install_with_selection", "list_available_options"]
        
        for class_name in required_classes:
            if f"class {class_name}" in init_content:
                print(f"✓ Found class: {class_name}")
            else:
                print(f"❌ Missing class: {class_name}")
                return False
        
        for func_name in required_functions:
            if f"def {func_name}" in init_content:
                print(f"✓ Found function: {func_name}")
            else:
                print(f"❌ Missing function: {func_name}")
                return False
        
        # Check installer.py for CLI functionality
        with open(installer_path, 'r') as f:
            installer_content = f.read()
        
        if "def main()" in installer_content:
            print("✓ Found CLI main function")
        else:
            print("❌ Missing CLI main function")
            return False
        
        if "argparse" in installer_content:
            print("✓ Found argparse for CLI")
        else:
            print("❌ Missing argparse for CLI")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating installer code: {e}")
        return False


def validate_workflow_mappings():
    """Validate workflow name mappings."""
    print("\nValidating workflow mappings...")
    
    # Expected workflow mappings from the installer
    expected_mappings = {
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
    
    component_dir = Path(__file__).parent
    workflows_dir = component_dir / "workflows"
    
    if not workflows_dir.exists():
        print("⚠ Workflows directory not found - skipping mapping validation")
        return True
    
    for workflow_key, filename in expected_mappings.items():
        workflow_path = workflows_dir / filename
        if workflow_path.exists():
            print(f"✓ Found workflow file: {filename}")
        else:
            print(f"⚠ Missing workflow file: {filename}")
    
    return True


def main():
    """Run all validations."""
    print("🔍 Validating GitHub Actions Python Component Installer")
    print("=" * 60)
    
    validations = [
        validate_component_structure,
        validate_component_json,
        validate_installer_code,
        validate_workflow_mappings
    ]
    
    all_passed = True
    for validation in validations:
        if not validation():
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All validations passed! The installer implementation looks good.")
    else:
        print("❌ Some validations failed. Please review the issues above.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)