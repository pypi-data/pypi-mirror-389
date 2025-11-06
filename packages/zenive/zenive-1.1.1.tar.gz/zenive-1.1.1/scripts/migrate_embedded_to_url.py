#!/usr/bin/env python3
"""
Migration script to convert embedded content components to URL-based components.

This script helps developers migrate from the old embedded content format
to the new URL-based format that's more like shadcn/ui.

Usage:
    python scripts/migrate_embedded_to_url.py components/old-component.json
"""

import json
import sys
from pathlib import Path
import argparse

def migrate_component(input_file: Path, output_dir: Path = None):
    """
    Migrate a component from embedded content to URL-based files.
    
    Args:
        input_file: Path to the JSON component with embedded content
        output_dir: Directory to create the new component structure
    """
    if not input_file.exists():
        print(f"Error: Input file {input_file} does not exist")
        return False
    
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_file}: {e}")
        return False
    
    # Handle array of components
    if isinstance(data, list):
        print(f"Found {len(data)} components in array. Processing each...")
        success = True
        for i, component_data in enumerate(data):
            component_name = component_data.get('name', f'component-{i}')
            component_output_dir = input_file.parent / f"{component_name}-migrated"
            print(f"\nProcessing component: {component_name}")
            if not migrate_single_component(component_data, component_output_dir):
                success = False
        return success
    
    # Single component
    return migrate_single_component(data, output_dir)

def migrate_single_component(data: dict, output_dir: Path):
    """Migrate a single component."""
    # Determine output directory
    if output_dir is None:
        output_dir = Path(f"{data.get('name', 'component')}-migrated")
    
    output_dir.mkdir(exist_ok=True)
    print(f"Creating migrated component in: {output_dir}")
    
    # Process files
    migrated_files = []
    
    for file_info in data.get('files', []):
        file_name = file_info.get('name')
        content = file_info.get('content', '')
        
        if not file_name or not content:
            print(f"Warning: Skipping file with missing name or content")
            continue
        
        # Write file content to separate file
        file_path = output_dir / file_name
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  Created: {file_name}")
        
        # Update file info to use URL instead of content
        migrated_file = {
            "name": file_info.get('name'),
            "path": file_info.get('path'),
            "url": f"./{file_name}"
        }
        migrated_files.append(migrated_file)
    
    # Update component data
    data['files'] = migrated_files
    
    # Write new component.json
    component_file = output_dir / 'component.json'
    with open(component_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"  Created: component.json")
    
    # Create requirements.txt if component has dependencies
    deps = data.get('dependencies', [])
    if deps:
        req_file = output_dir / 'requirements.txt'
        with open(req_file, 'w') as f:
            f.write(f"# {data.get('name', 'Component')} dependencies\n")
            for dep in deps:
                f.write(f"{dep}\n")
        print(f"  Created: requirements.txt")
        
        # Add requirements.txt to component files
        data['files'].append({
            "name": "requirements.txt",
            "path": "requirements.txt", 
            "url": "./requirements.txt"
        })
        
        # Update component.json with requirements file
        with open(component_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    print(f"\n✅ Migration complete for {data.get('name', 'component')}!")
    print(f"📁 New component structure: {output_dir}")
    print(f"🔗 You can now host this directory on GitHub and use:")
    print(f"   zen add https://github.com/user/repo/tree/main/{output_dir.name}")
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Migrate zen components from embedded content to URL-based files"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the JSON component file with embedded content"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        help="Output directory for migrated component (default: auto-generated)"
    )
    
    args = parser.parse_args()
    
    success = migrate_component(args.input_file, args.output_dir)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()