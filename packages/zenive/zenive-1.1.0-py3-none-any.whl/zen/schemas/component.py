"""
Component schema for zen - shadcn/ui inspired Python component registry.

This module supports both embedded content (legacy) and file references for components.
The preferred approach is to use file paths/URLs, making it easy for developers to
organize their components in GitHub repositories just like shadcn/ui.

Supported file sources:
- GitHub repositories (automatically converts blob URLs to raw)
- HTTP/HTTPS URLs
- Local file paths
- Relative paths (resolved against component JSON location)
"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator, model_validator
from pathlib import Path
from urllib.parse import urlparse, urljoin
import requests

class ComponentFile(BaseModel):
    """Represents a file in a component.

    Backwards-compatible: either `content` or `url` must be provided. In the
    preferred workflow components should provide `url` (local relative path,
    file://, or http(s) URL). If `url` is provided but `content` is missing,
    loaders will fetch content automatically.
    """
    name: str = Field(..., description="Name of the file")
    path: str = Field(..., description="Target path where file should be installed")
    content: Optional[str] = Field(None, description="File content (embedded). Deprecated; prefer `url`.")
    url: Optional[str] = Field(None, description="URL or local path to fetch file content from (file://, http(s), or relative path)")

    @model_validator(mode='before')
    @classmethod
    def require_content_or_url(cls, values):
        if isinstance(values, dict):
            content, url = values.get("content"), values.get("url")
            if not content and not url:
                raise ValueError("Either 'content' or 'url' must be provided for each file")
        return values

class ComponentSchema(BaseModel):
    """JSON schema for component definitions."""
    name: str = Field(..., description="Component name")
    version: str = Field(..., description="Component version")
    description: str = Field(..., description="Component description")
    category: str = Field(default="utils", description="Component category")
    type: str = Field(default="component", description="Component type")
    
    # Dependencies
    dependencies: List[str] = Field(default_factory=list, description="Python package dependencies")
    dev_dependencies: List[str] = Field(default_factory=list, description="Development dependencies")
    registry_dependencies: List[str] = Field(default_factory=list, description="Other component dependencies")
    
    # Files (either content or url must be present per file)
    files: List[ComponentFile] = Field(..., description="List of files with embedded content or urls")
    
    # Metadata
    author: Optional[str] = Field(None, description="Component author")
    license: Optional[str] = Field(None, description="Component license")
    python_requires: Optional[str] = Field(None, description="Python version requirement")
    keywords: List[str] = Field(default_factory=list, description="Component keywords")
    homepage: Optional[str] = Field(None, description="Component homepage URL")

    @validator('name')
    def validate_name(cls, v):
        """Validate component name format."""
        if not v or not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Component name must be alphanumeric with optional hyphens/underscores')
        return v.lower()

    @validator('version')
    def validate_version(cls, v):
        """Validate version format (basic semver)."""
        import re
        if not re.match(r'^\d+\.\d+\.\d+', v):
            raise ValueError('Version must follow semantic versioning (e.g., 1.0.0)')
        return v

    @validator('files')
    def validate_files(cls, v):
        """Ensure at least one file is provided."""
        if not v:
            raise ValueError('Component must have at least one file')
        return v

def fetch_file_content(url: str, base: Optional[str] = None, timeout: int = 30) -> str:
    """
    Fetch file content from various sources, with enhanced GitHub support.

    Supported sources:
    - GitHub repositories (blob URLs, raw URLs, API URLs)
    - HTTP/HTTPS URLs  
    - file:// URLs
    - Local absolute/relative paths
    - GitHub tree URLs (for component.json discovery)
    """
    parsed = urlparse(url)

    # Enhanced GitHub support
    if parsed.netloc.lower() == "github.com":
        # Convert various GitHub URL formats to raw content
        if "/blob/" in parsed.path:
            # github.com/user/repo/blob/branch/path -> raw.githubusercontent.com/user/repo/branch/path
            raw_path = parsed.path.replace("/blob/", "/")
            raw_url = f"https://raw.githubusercontent.com{raw_path}"
            resp = requests.get(raw_url, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        elif "/tree/" in parsed.path:
            # github.com/user/repo/tree/branch/path -> look for component.json
            tree_path = parsed.path.replace("/tree/", "/")
            component_url = f"https://raw.githubusercontent.com{tree_path}/component.json"
            resp = requests.get(component_url, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        else:
            # Try as raw URL directly
            raw_url = f"https://raw.githubusercontent.com{parsed.path}"
            resp = requests.get(raw_url, timeout=timeout)
            resp.raise_for_status()
            return resp.text

    # raw.githubusercontent.com URLs
    if parsed.netloc.lower() == "raw.githubusercontent.com":
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text

    # Absolute HTTP(S)
    if parsed.scheme in ("http", "https"):
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text

    # No scheme but base is an HTTP URL -> join and fetch via HTTP
    if (not parsed.scheme or parsed.scheme == "") and base:
        base_parsed = urlparse(base)
        if base_parsed.scheme in ("http", "https"):
            # For relative URLs starting with ./, remove the ./ and join properly
            clean_url = url.lstrip('./')
            if base.endswith('/'):
                joined = base + clean_url
            else:
                joined = base + '/' + clean_url
            resp = requests.get(joined, timeout=timeout)
            resp.raise_for_status()
            return resp.text

    # file:// URLs
    if parsed.scheme == "file":
        path = Path(parsed.path)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    # Local path (absolute or relative)
    p = Path(url)
    if not p.is_absolute():
        if base:
            # If base looks like a filesystem path -> resolve relative to it
            base_parsed = urlparse(base)
            if base_parsed.scheme in ("http", "https"):
                # Should have been handled earlier — fall through to HTTP join if needed
                joined = urljoin(base, url)
                resp = requests.get(joined, timeout=timeout)
                resp.raise_for_status()
                return resp.text
            else:
                # base is a filesystem path or file:// path
                base_path = Path(base)
                # if base is a file path, use its parent
                if base_path.is_file():
                    base_path = base_path.parent
                p = (base_path / p).resolve()
        else:
            p = p.resolve()

    with open(p, "r", encoding="utf-8") as f:
        return f.read()

def load_component_from_json(json_content: str, base: Optional[str] = None) -> ComponentSchema:
    """
    Load component from JSON string and fetch any file contents referenced by URL.

    Args:
        json_content: JSON string containing component definition
        base: Optional base path/URL used to resolve relative file urls. When the
              component JSON was read from disk, this should be the JSON file path.
              When fetched from HTTP, this should be the JSON URL.

    Returns:
        ComponentSchema instance with file content populated when possible
    """
    try:
        data = json.loads(json_content)
        comp = ComponentSchema(**data)
        # For each file, if url provided and content missing -> fetch
        for f in comp.files:
            if not f.content and f.url:
                try:
                    # Convert GitHub tree base URLs to raw URLs for file fetching
                    resolved_base = base
                    if base and "github.com" in base and "/tree/" in base:
                        # Convert tree URL to raw URL base
                        resolved_base = base.replace("github.com", "raw.githubusercontent.com").replace("/tree/", "/")
                    
                    f.content = fetch_file_content(f.url, base=resolved_base)
                except Exception as e:
                    raise ValueError(f"Failed to fetch file '{f.name}' from '{f.url}': {e}")
        return comp
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    except Exception as e:
        raise ValueError(f"Invalid component schema: {e}")

def load_component_from_url(url: str) -> ComponentSchema:
    """
    Load component from various URL formats, with enhanced GitHub support.

    Supports:
    - Direct component.json URLs
    - GitHub repository URLs (auto-discovers component.json)
    - GitHub tree/blob URLs
    - Local file:// URLs

    Args:
        url: URL pointing to component or repository

    Returns:
        ComponentSchema instance with file content fetched/resolved
    """
    try:
        parsed_url = urlparse(url)
        
        # Handle GitHub repository URLs
        if parsed_url.netloc.lower() == "github.com":
            if "/tree/" in parsed_url.path or "/blob/" in parsed_url.path:
                # GitHub tree or blob URL - fetch component.json from that path
                content = fetch_file_content(url)
                return load_component_from_json(content, base=url)
            elif parsed_url.path.endswith('.json'):
                # Direct JSON file URL
                content = fetch_file_content(url)
                return load_component_from_json(content, base=url)
            else:
                # Repository root - try to find component.json
                repo_url = f"https://github.com{parsed_url.path}"
                component_url = f"{repo_url}/blob/main/component.json"
                try:
                    content = fetch_file_content(component_url)
                    return load_component_from_json(content, base=component_url)
                except:
                    # Try master branch
                    component_url = f"{repo_url}/blob/master/component.json"
                    content = fetch_file_content(component_url)
                    return load_component_from_json(content, base=component_url)
        
        # Handle file:// URLs
        if parsed_url.scheme == 'file':
            file_path = parsed_url.path
            base = file_path  # filesystem path for resolving relative file urls
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return load_component_from_json(content, base=base)
        
        # Handle HTTP/HTTPS URLs
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        # Use the directory containing the JSON as base for resolving relative file urls
        base_url = url.rsplit('/', 1)[0] + '/'
        return load_component_from_json(response.text, base=base_url)
    except (requests.RequestException, FileNotFoundError, OSError) as e:
        raise ValueError(f"Failed to fetch component from {url}: {e}")

def create_sample_component_json() -> str:
    """Create a sample component JSON for testing (uses url-based files)."""
    sample = {
        "name": "email-validator",
        "version": "1.0.0",
        "description": "Simple email validation utility",
        "category": "utils",
        "type": "component",
        "dependencies": ["email-validator"],
        "files": [
            {
                "name": "validator.py",
                "path": "src/utils/validator.py",
                "url": "./src/utils/validator.py"
            },
            {
                "name": "__init__.py",
                "path": "src/utils/__init__.py",
                "url": "./src/utils/__init__.py"
            }
        ],
        "author": "zen",
        "license": "MIT"
    }
    return json.dumps(sample, indent=2)
