# zen Usage Guide

This guide shows you how to use the zen Python component registry system.

## 🚀 Quick Start

### 1. Install zen
```bash
# Install from PyPI 
pip install zen

# Or install from source
git clone https://github.com/TheRaj71/Zenive
cd Zenive
pip install -e .
```

### 2. Create a New Project
```bash
# Initialize a new project
zen init my-project
cd my-project

# Project structure created:
# my-project/
# ├── .zenive/
# │   └── config.yaml
# ├── src/
# │   ├── components/
# │   ├── utils/
# │   ├── models/
# │   └── services/
# ├── requirements.txt
# ├── .gitignore
# └── README.md
```

### 3. Install Components from URLs

#### From GitHub Repository
```bash
# Create a demo component repository (example)
cd /tmp
mkdir -p zenive-demo-components/email-validator
cd zenive-demo-components/email-validator

# Create component.yaml
cat > component.yaml << 'EOF'
name: email-validator
version: 1.0.0
description: Simple email validation utility
category: utils
author: demo@zenive.dev
license: MIT
python_requires: ">=3.8"

files:
  - src: validator.py
    dest: src/utils/
  - src: __init__.py
    dest: src/utils/

dependencies:
  - email-validator
EOF

# Create Python files
cat > validator.py << 'EOF'
"""Simple email validation utility."""
import re
from typing import Union
from email_validator import validate_email as _validate_email, EmailNotValidError

def validate_email(email: str) -> bool:
    """Validate email address using email-validator package."""
    try:
        _validate_email(email)
        return True
    except EmailNotValidError:
        return False

def extract_domain(email: str) -> Union[str, None]:
    """Extract domain from email address."""
    if validate_email(email):
        return email.split('@')[1]
    return None
EOF

cat > __init__.py << 'EOF'
"""Email validation utilities for Python projects."""
from .validator import validate_email, extract_domain
__all__ = ['validate_email', 'extract_domain']
EOF

# Initialize git repository
git init
git add .
git commit -m "Add email validator component"

# Push to GitHub (or use local file:// URL for testing)
# git remote add origin https://github.com/yourusername/demo-components
# git push -u origin main
```

#### Install from Local Directory (for testing)
```bash
# Go back to your project
cd my-project

# Install from local directory using file:// URL
zen add https://github.com/TheRaj71/Zenive/tree/main/components/email-validator

# Output:
# INFO → Installing component: file:///tmp/zenive-demo-components/email-validator
# INFO → Fetching component from URL...
# INFO → Component: email-validator v1.0.0
# INFO → Description: Simple email validation utility
# INFO → Category: utils
# INFO → Installing to: src/utils
# INFO → Installing component files...
# INFO → Installed: validator.py -> /path/to/project/src/utils/validator.py
# INFO → Installed: __init__.py -> /path/to/project/src/utils/__init__.py
# INFO → Updating dependencies...
# INFO → Added 1 new dependencies
# ✓ ✨ Successfully installed email-validator
# INFO → Files installed: 2
# INFO → Dependencies added: 1
# 🎉 Component email-validator is ready to use!
```

#### Install from GitHub (real example)
```bash
# Install from GitHub repository
zen add https://github.com/TheRaj71/Zenive/tree/main/components/email-validator

# Install from specific path in a multi-component repo
zen add https://github.com/TheRaj71/Zenive/tree/main/components/jwt-auth

# Install to custom directory
zen add https://github.com/TheRaj71/Zenive/tree/main/components/jwt-auth --path src/auth
```

## 📁 What Happens During Installation

### 1. Component Files Are Copied
```bash
# Before installation:
src/utils/
├── __init__.py (empty)

# After installation:
src/utils/
├── __init__.py (updated with component exports)
├── validator.py (email validation functions)
```

### 2. Requirements.txt Is Updated
```bash
# Before:
# Project dependencies

# After:
# Project dependencies
email-validator
```

### 3. Project Configuration Is Updated
```yaml
# .zenive/config.yaml
name: my-project
version: 1.0.0
structure:
  utils: src/utils
  models: src/models
  api: src/api
  auth: src/auth

components:
  file:///tmp/zenive-demo-components/email-validator:
    name: email-validator
    version: 1.0.0
    install_path: src/utils
    dependencies: 
      - email-validator
```

## 🧪 Using Installed Components

### 1. Import and Use
```python
# In your project files
from src.utils.validator import validate_email, extract_domain

# Use the functions
print(validate_email("test@example.com"))  # True
print(extract_domain("user@gmail.com"))    # gmail.com
```

### 2. Install Dependencies
```bash
# Install the actual Python packages
pip install -r requirements.txt

# Now your code will work with the real packages
```

## 🔧 Advanced Features

### 1. Dry Run Mode
```bash
# See what would be installed without making changes
zenive add https://github.com/user/component --dry-run

# Output:
# 🔍 DRY RUN - No changes will be made
# Component: jwt-auth v1.0.0
# Description: JWT authentication utilities
# Category: auth
# Would install to: src/auth
# Would add dependencies: PyJWT, cryptography
```

### 2. Custom Installation Path
```bash
# Install to specific directory
zenive add https://github.com/user/data-tools --path src/data/processors

# Install multiple components to organized structure
zenive add https://github.com/user/auth-jwt --path src/auth/jwt
zenive add https://github.com/user/auth-oauth --path src/auth/oauth
```

### 3. Skip Dependencies
```bash
# Install files only, don't update requirements.txt
zenive add https://github.com/user/component --no-deps
```

### 4. Overwrite Existing Files
```bash
# Force overwrite if files already exist
zenive add https://github.com/user/component --overwrite
```

## 📊 Managing Components

### List Available Commands
```bash
zenive --help

# Commands:
# init      Initialize a new Zenive project
# add       Install a component from registry or URL
# remove    Remove an installed component
# list      List available components in registry
# search    Search for components
# info      Show detailed information about a component
# update    Update installed components
# config    Manage project configuration
```

### View Project Status
```bash
# List installed components
zenive list --installed

# Show component details
zenive info email-validator

# Update components
zenive update
```

## 🏗️ Creating Your Own Components

### 1. Component Structure
```
my-component/
├── component.yaml      # Metadata and configuration
├── main_file.py       # Your Python code
├── __init__.py        # Module initialization
├── utils.py           # Additional files
└── README.md          # Documentation (optional)
```

### 2. component.yaml Format
```yaml
name: my-awesome-component
version: 1.2.0
description: Description of what this component does
category: utils  # utils, auth, data, ml, api, etc.
author: your@email.com
license: MIT
python_requires: ">=3.8"

# Files to copy and their destination paths
files:
  - src: main_file.py
    dest: src/utils/
  - src: utils.py
    dest: src/utils/
  - src: __init__.py
    dest: src/utils/

# Python packages to add to requirements.txt
dependencies:
  - requests
  - pydantic
  - typing-extensions

# Optional: development dependencies
dev_dependencies:
  - pytest
  - black
  - mypy
```

### 3. Share Your Component
```bash
# Option 1: GitHub Repository
git init
git add .
git commit -m "Add my awesome component"
git remote add origin https://github.com/yourusername/my-component
git push -u origin main

# Users can install with:
# zenive add https://github.com/yourusername/my-component
```

```bash
# Option 2: Multi-component Repository
my-components/
├── components/
│   ├── auth/
│   │   ├── jwt-handler/
│   │   │   ├── component.yaml
│   │   │   └── auth.py
│   │   └── oauth/
│   │       ├── component.yaml
│   │       └── oauth.py
│   └── utils/
│       ├── validators/
│       │   ├── component.yaml
│       │   └── validator.py
│       └── helpers/
│           ├── component.yaml
│           └── helper.py

# Users can install specific components:
# zenive add https://github.com/you/components/tree/main/components/auth/jwt-handler
```

## 🔥 Real-World Examples

### Example 1: Company Internal Components
```bash
# Set up company component library
zenive add https://github.com/company/components/tree/main/auth/sso
zenive add https://github.com/company/components/tree/main/data/processors
zenive add https://github.com/company/components/tree/main/api/rate-limiter
```

### Example 2: Open Source Components
```bash
# Install popular community components
zenive add https://github.com/python-validators/email-validator
zenive add https://github.com/ml-utils/data-preprocessor
zenive add https://github.com/api-tools/request-logger
```

### Example 3: Personal Component Collection
```bash
# Your personal utility collection
zenive add https://github.com/yourusername/my-utils/tree/main/text-processing
zenive add https://github.com/yourusername/my-utils/tree/main/file-helpers
zenive add https://github.com/yourusername/my-utils/tree/main/config-loader
```

## 🎯 Best Practices

### 1. Component Design
- ✅ Keep components focused on a single purpose
- ✅ Use clear, descriptive names
- ✅ Include proper documentation
- ✅ Specify exact dependencies needed
- ✅ Use semantic versioning

### 2. Dependency Management
- ✅ Specify minimum required versions only (e.g., `pydantic` not `pydantic>=2.5.0`)
- ✅ Keep dependency lists minimal
- ✅ Avoid version conflicts
- ✅ Test with fresh virtual environments

### 3. File Organization
- ✅ Use consistent file naming
- ✅ Include `__init__.py` files for proper modules
- ✅ Map files to logical destination paths
- ✅ Avoid overwriting core project files

### 4. Sharing Components
- ✅ Use public GitHub repositories for open source
- ✅ Private repositories for internal components
- ✅ Tag releases for stable versions
- ✅ Include usage examples in README

## 🆘 Troubleshooting

### Common Issues

#### 1. "No component.yaml found"
```bash
# Error: Component repository doesn't have component.yaml
# Solution: Ensure component.yaml exists in the root or specify path
zenive add https://github.com/user/repo/tree/main/path/to/component
```

#### 2. "Multiple components found"
```bash
# Error: Repository has multiple component.yaml files
# Solution: Specify the exact component path
zenive add https://github.com/user/repo/tree/main/components/specific-component
```

#### 3. "Dependency conflicts"
```bash
# Error: Package version conflicts
# Solution: Check your requirements.txt and resolve conflicts manually
pip install -r requirements.txt --upgrade
```

#### 4. "Permission denied"
```bash
# Error: Can't write to directory
# Solution: Check directory permissions and ensure you're in a Zenive project
zenive init .  # Initialize if needed
```

This guide should get you started with Zenive! The system works exactly like shadcn/ui but for Python components - simple, powerful, and flexible.
