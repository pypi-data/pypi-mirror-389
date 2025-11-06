# zen Examples

This example demonstrates the improved shadcn/ui-like workflow for zen.

## 🚀 Quick Demo

### 1. Initialize a New Project

```bash
# Create a new zen project
zen init my-awesome-app
cd my-awesome-app

# Project structure is created automatically
ls -la
# .zen/config.yaml
# src/
# requirements.txt
# README.md
# .gitignore
```

### 2. Install Components from GitHub

```bash
# Install email validator component
zen add https://github.com/TheRaj71/Zenive/tree/main/components/email-validator

# Preview what will be installed:
# Component: email-validator v1.0.0
# Description: Simple email validation utility with multiple validation methods
# Category: utils
# Dependencies: email-validator, re
# Files: 3 files
# Install to: src/utils
# Proceed with installation? [y/N]: y

# ✨ Successfully installed email-validator
# 📁 Files installed: 3
# 📦 Dependencies added: 2
# 🎉 Component is ready to use!
```

### 3. Install JWT Authentication Component

```bash
# Install JWT auth component to custom path
zen add https://github.com/TheRaj71/Zenive/tree/main/components/jwt-auth --path src/auth

# Skip confirmation with --yes flag
zen add https://github.com/TheRaj71/Zenive/tree/main/components/jwt-auth --path src/auth --yes
```

### 4. Use the Installed Components

```python
# In your application code
from src.utils.validator import validate_email, is_business_email
from src.auth.jwt_handler import JWTHandler, create_user_tokens

# Email validation
email = "user@example.com"
if validate_email(email):
    print(f"Valid email: {email}")
    
if is_business_email(email):
    print("This is a business email")

# JWT authentication
jwt_handler = JWTHandler("your-secret-key")
tokens = create_user_tokens("user123", email, ["user"], jwt_handler)
print(f"Access token: {tokens['access_token']}")
```

### 5. Install Dependencies

```bash
# Install all component dependencies
pip install -r requirements.txt

# Your requirements.txt now contains:
# email-validator>=2.0.0
# PyJWT>=2.4.0
# cryptography>=3.4.0
```

### 6. Manage Components

```bash
# List installed components
zen list
# 📦 Installed components (2):
#   • email-validator v1.0.0
#     Category: utils
#   • jwt-auth v2.0.0
#     Category: auth

# Show component details
zen info email-validator

# Remove a component (config only)
zen remove email-validator
```

## 🏗️ Creating Your Own Components

### 1. Create Component Directory Structure

```bash
mkdir my-component
cd my-component

# Create your Python files
touch component.json
touch main.py
touch __init__.py
touch requirements.txt
```

### 2. Define component.json

```json
{
  "name": "my-component",
  "version": "1.0.0",
  "description": "My awesome Python component",
  "category": "utils",
  "dependencies": ["requests"],
  "files": [
    {
      "name": "main.py",
      "path": "src/utils/main.py",
      "url": "./main.py"
    },
    {
      "name": "__init__.py",
      "path": "src/utils/__init__.py",
      "url": "./__init__.py"
    },
    {
      "name": "requirements.txt",
      "path": "requirements.txt",
      "url": "./requirements.txt"
    }
  ],
  "author": "Your Name",
  "license": "MIT",
  "python_requires": ">=3.8"
}
```

### 3. Write Your Component Code

**main.py:**
```python
"""My awesome component."""
import requests

def fetch_data(url: str) -> dict:
    """Fetch data from URL."""
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
```

**__init__.py:**
```python
"""My component package."""
from .main import fetch_data

__all__ = ['fetch_data']
```

**requirements.txt:**
```
# My component dependencies
requests>=2.25.0
```

### 4. Host on GitHub

```bash
git init
git add .
git commit -m "Add my awesome component"
git remote add origin https://github.com/yourusername/my-component
git push -u origin main
```

### 5. Share with Others

Users can now install your component with:

```bash
# Any of these formats work:
zen add https://github.com/yourusername/my-component
zen add https://github.com/yourusername/my-component/tree/main
zen add https://raw.githubusercontent.com/yourusername/my-component/main/component.json
```

## 🔄 Migration from Old Format

If you have components with embedded content, use the migration script:

```bash
# Migrate old embedded-content components
python scripts/migrate_embedded_to_url.py old-component.json

# Creates a new directory structure:
# component-name-migrated/
# ├── component.json (updated)
# ├── file1.py (extracted)
# ├── file2.py (extracted)
# └── requirements.txt (created)
```

## 🌟 Advanced Features

### Dry Run Mode
```bash
# Preview installation without making changes
zen add https://github.com/user/component --dry-run
```

### Custom Installation Paths
```bash
# Install to specific directory
zen add https://github.com/user/auth-component --path src/authentication
```

### Overwrite Existing Files
```bash
# Force overwrite existing files
zen add https://github.com/user/component --overwrite
```

### Skip Confirmations
```bash
# Skip all confirmation prompts
zen add https://github.com/user/component --yes
```

## 🎯 Benefits Over Traditional Approaches

| Feature | zen | pip packages | git submodules |
|---------|--------------|--------------|----------------|
| **Easy Installation** | ✅ `zen add <url>` | ✅ `pip install` | ❌ Complex setup |
| **Code Ownership** | ✅ Files in project | ❌ External dependency | ✅ Files in project |
| **No Registry Lock-in** | ✅ Any GitHub URL | ❌ PyPI only | ✅ Any git repo |
| **Automatic Dependencies** | ✅ Updates requirements.txt | ✅ Auto-installed | ❌ Manual management |
| **Easy Customization** | ✅ Edit copied files | ❌ Hard to modify | ✅ Easy to modify |
| **Preview Before Install** | ✅ Shows what will happen | ❌ No preview | ❌ No preview |
| **Component Management** | ✅ List, info, remove | ❌ Limited | ❌ Manual tracking |

This makes zen perfect for:
- **Internal company components** that aren't suitable for PyPI
- **Rapid prototyping** with reusable code snippets
- **Educational projects** where students can see and modify all code
- **Custom utilities** that need project-specific modifications
- **Component-based development** similar to shadcn/ui for React