#!/usr/bin/env python3
"""
GitHub Actions Python Component Installer CLI

Command-line interface for installing GitHub Actions workflows with interactive selection.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

from . import (
    install_component,
    install_with_selection, 
    list_available_options,
    GitHubActionsInstaller,
    WorkflowSelector
)
from zen.core.logger import get_logger

logger = get_logger()


def print_available_options():
    """Print all available workflows, configs, and presets."""
    options = list_available_options()
    
    print("\n🔧 Available Workflows:")
    print("=" * 50)
    for key, info in options["workflows"].items():
        status = "✓" if key in ["basic_ci", "code_quality", "security_scan", "dependency_update"] else " "
        print(f"  {status} {key:<20} - {info['name']}")
        print(f"    {info['description']}")
        print(f"    Recommended for: {info['recommended_for']}")
        print()
    
    print("\n⚙️  Available Configurations:")
    print("=" * 50)
    for key, info in options["configs"].items():
        status = "✓" if key in ["dependabot", "pre_commit"] else " "
        print(f"  {status} {key:<20} - {info['name']}")
        print(f"    {info['description']}")
        print(f"    Location: {info['location']}")
        print()
    
    print("\n📦 Available Presets:")
    print("=" * 50)
    for key, info in options["presets"].items():
        print(f"  • {key:<15} - {info['name']}")
        print(f"    {info['description']}")
        print()


def interactive_selection() -> Dict:
    """Interactive workflow selection."""
    installer = GitHubActionsInstaller(".")
    selector = WorkflowSelector(installer)
    
    print("\n🎯 GitHub Actions Python Component Installation")
    print("=" * 60)
    
    # Ask for preset or custom
    print("\nChoose installation method:")
    print("1. Use preset configuration (recommended)")
    print("2. Custom selection")
    
    while True:
        choice = input("\nEnter choice (1-2): ").strip()
        if choice in ["1", "2"]:
            break
        print("Please enter 1 or 2")
    
    if choice == "1":
        # Preset selection
        presets = selector.create_preset_configurations()
        print("\nAvailable presets:")
        for i, (key, info) in enumerate(presets.items(), 1):
            print(f"{i}. {info['name']} - {info['description']}")
        
        while True:
            try:
                preset_choice = int(input(f"\nSelect preset (1-{len(presets)}): "))
                if 1 <= preset_choice <= len(presets):
                    preset_key = list(presets.keys())[preset_choice - 1]
                    return {"preset": preset_key}
                print(f"Please enter a number between 1 and {len(presets)}")
            except ValueError:
                print("Please enter a valid number")
    
    else:
        # Custom selection
        print("\n🔧 Select Workflows:")
        workflows = selector.get_available_workflows()
        selected_workflows = {}
        
        for key, info in workflows.items():
            default = "y" if key in ["basic_ci", "code_quality"] else "n"
            while True:
                response = input(f"\nInstall {info['name']}? ({info['description']}) [y/N]: ").strip().lower()
                if response in ["", "n", "no"]:
                    selected_workflows[key] = False
                    break
                elif response in ["y", "yes"]:
                    selected_workflows[key] = True
                    break
                print("Please enter y/yes or n/no")
        
        print("\n⚙️  Select Configurations:")
        configs = selector.get_available_configs()
        selected_configs = {}
        
        for key, info in configs.items():
            while True:
                response = input(f"\nInstall {info['name']}? ({info['description']}) [y/N]: ").strip().lower()
                if response in ["", "n", "no"]:
                    selected_configs[key] = False
                    break
                elif response in ["y", "yes"]:
                    selected_configs[key] = True
                    break
                print("Please enter y/yes or n/no")
        
        return {
            "custom_options": {
                "workflows": selected_workflows,
                "configs": selected_configs
            }
        }


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Install GitHub Actions Python workflows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive installation
  python -m components.github-actions-python.installer
  
  # Install with preset
  python -m components.github-actions-python.installer --preset standard
  
  # List available options
  python -m components.github-actions-python.installer --list
  
  # Install specific workflows
  python -m components.github-actions-python.installer --workflows basic_ci,code_quality --configs pre_commit
        """
    )
    
    parser.add_argument(
        "--preset", 
        choices=["minimal", "standard", "library", "enterprise"],
        help="Use preset configuration"
    )
    
    parser.add_argument(
        "--workflows",
        help="Comma-separated list of workflows to install"
    )
    
    parser.add_argument(
        "--configs", 
        help="Comma-separated list of configs to install"
    )
    
    parser.add_argument(
        "--list", 
        action="store_true",
        help="List available workflows, configs, and presets"
    )
    
    parser.add_argument(
        "--overwrite",
        action="store_true", 
        help="Overwrite existing files without prompting"
    )
    
    parser.add_argument(
        "--project-root",
        default=".",
        help="Target project directory (default: current directory)"
    )
    
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format for results"
    )
    
    args = parser.parse_args()
    
    try:
        if args.list:
            print_available_options()
            return
        
        # Determine installation options
        if args.preset:
            result = install_with_selection(
                project_root=args.project_root,
                preset=args.preset,
                overwrite=args.overwrite
            )
        elif args.workflows or args.configs:
            # Parse command line selections
            workflows = {}
            if args.workflows:
                for workflow in args.workflows.split(","):
                    workflows[workflow.strip()] = True
            
            configs = {}
            if args.configs:
                for config in args.configs.split(","):
                    configs[config.strip()] = True
            
            custom_options = {"workflows": workflows, "configs": configs}
            result = install_with_selection(
                project_root=args.project_root,
                custom_options=custom_options,
                overwrite=args.overwrite
            )
        else:
            # Interactive mode
            selection = interactive_selection()
            if "preset" in selection:
                result = install_with_selection(
                    project_root=args.project_root,
                    preset=selection["preset"],
                    overwrite=args.overwrite
                )
            else:
                result = install_with_selection(
                    project_root=args.project_root,
                    custom_options=selection["custom_options"],
                    overwrite=args.overwrite
                )
        
        # Output results
        if args.output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print_installation_summary(result)
    
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Installation failed: {e}")
        sys.exit(1)


def print_installation_summary(result: Dict):
    """Print human-readable installation summary."""
    if result["status"] == "cancelled":
        print(f"\n❌ Installation cancelled: {result['reason']}")
        return
    
    print(f"\n✅ Installation completed successfully!")
    print(f"📁 Installed {result['total_files']} files")
    
    if result["workflows_installed"]:
        print(f"\n🔧 Workflows installed:")
        for workflow in result["workflows_installed"]:
            print(f"  • {workflow}")
    
    if result["configs_installed"]:
        print(f"\n⚙️  Configurations installed:")
        for config in result["configs_installed"]:
            print(f"  • {config}")
    
    if result.get("selection_warnings"):
        print(f"\n⚠️  Warnings:")
        for warning in result["selection_warnings"]:
            print(f"  • {warning}")
    
    # Print usage instructions
    instructions = result.get("usage_instructions", {})
    
    if instructions.get("workflows"):
        print(f"\n📋 Workflow Instructions:")
        for workflow, instruction in instructions["workflows"].items():
            print(f"  • {workflow}: {instruction}")
    
    if instructions.get("configs"):
        print(f"\n⚙️  Configuration Instructions:")
        for config, instruction in instructions["configs"].items():
            print(f"  • {config}: {instruction}")
    
    if instructions.get("next_steps"):
        print(f"\n🚀 Next Steps:")
        for i, step in enumerate(instructions["next_steps"], 1):
            print(f"  {i}. {step}")
    
    print(f"\n📂 Files installed in: {result['workflows_dir']}")


if __name__ == "__main__":
    main()