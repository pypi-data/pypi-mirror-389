# zen

A Python component registry system inspired by shadcn/ui - install Python components from anywhere with a single command.

## 🚀 Quick Start

### Installation

```bash
pip install zen
```

### Initialize a Project

```bash
zen init my-project
cd my-project
```

### Install Components (shadcn/ui style!)

```bash
# Install from GitHub repository (auto-discovers component.json)
zen add https://github.com/user/awesome-components

# Install from specific component directory
zen add https://github.com/user/components/tree/main/email-validator

# Install from direct JSON URL
zen add https://raw.githubusercontent.com/user/repo/main/component.json

# Install to custom path
zen add https://github.com/user/jwt-auth --path src/auth

# Skip confirmation prompts
zen add https://github.com/user/component --yes
```

## 🎯 How It Works

zen works exactly like shadcn/ui but for Python:

1. **Developers** create components in GitHub repositories with separate files
2. **Users** install components directly into their projects from GitHub URLs
3. **Files** are copied into the project with automatic dependency management
4. **No registry lock-in** - install from any GitHub repository or URL

## 📦 Component Format (New & Improved!)

Components are now organized like shadcn/ui - separate files with a simple JSON config:

**Directory Structure:**
```
email-validator/
├── component.json       # Component metadata
├── validator.py         # Main component code
├── __init__.py         # Module initialization  
└── requirements.txt    # Dependencies
```

**component.json:**
```json
{
  "name": "email-validator",
  "version": "1.0.0", 
  "description": "Simple email validation utility",
  "category": "utils",
  "dependencies": ["email-validator"],
  "files": [
    {
      "name": "validator.py",
      "path": "src/utils/validator.py",
      "url": "./validator.py"
    },
    {
      "name": "__init__.py",
      "path": "src/utils/__init__.py", 
      "url": "./__init__.py"
    }
  ]
}
```

**No more embedded content!** Just reference your files with `url` paths.

## 🏗️ Project Structure

zen creates organized Python projects:

```
my-project/
├── .zen/
│   └── config.yaml    # Project configuration
├── src/
│   ├── components/    # General components
│   ├── utils/         # Utility functions
│   ├── models/        # Data models
│   ├── services/      # Business logic
│   ├── auth/          # Authentication
│   └── data/          # Data processing
├── requirements.txt   # Auto-managed dependencies
└── README.md
```

## 🔧 CLI Commands (shadcn/ui inspired)

```bash
# Initialize new project
zen init [project-name]

# Install component from URL (with preview!)
zen add <component-url>

# Skip confirmation prompts
zen add <component-url> --yes

# Install to custom path
zen add <component-url> --path src/custom

# Overwrite existing files
zen add <component-url> --overwrite

# Dry run (show what would happen)
zen add <component-url> --dry-run

# List installed components
zen list

# Show component details
zen info <component-name>

# Remove component
zen remove <component-name>

# Help
zen --help
zen add --help
```

## 📚 Creating Components (The shadcn/ui Way!)

### 1. Component Structure (New!)

Create a directory with separate files (much cleaner!):

```
my-component/
├── component.json      # Metadata only
├── main.py            # Your Python code
├── utils.py           # Additional files
├── __init__.py        # Module init
└── requirements.txt   # Dependencies
```

**component.json** (no embedded content!):
```json
{
  "name": "my-component",
  "version": "1.0.0",
  "description": "What this component does",
  "category": "utils",
  "dependencies": ["requests", "pydantic"],
  "files": [
    {
      "name": "main.py",
      "path": "src/utils/main.py",
      "url": "./main.py"
    },
    {
      "name": "requirements.txt",
      "path": "requirements.txt", 
      "url": "./requirements.txt"
    }
  ]
}
```

### 2. Hosting Components (GitHub First!)

Push your component directory to GitHub:

```bash
git add .
git commit -m "Add my awesome component"
git push origin main
```

### 3. Sharing Components

Users install with any of these formats:
```bash
# Repository root (auto-finds component.json)
zen add https://github.com/user/my-component

# Specific directory in repo
zen add https://github.com/user/components/tree/main/my-component

# Direct JSON URL (still works)
zen add https://raw.githubusercontent.com/user/repo/main/component.json
```

## 🌟 Features

- **Zero Configuration**: Works out of the box
- **No Registry Lock-in**: Install from any URL
- **Automatic Dependencies**: Updates requirements.txt automatically
- **File Ownership**: Code is copied into your project (you own it)
- **Flexible Paths**: Install to any directory structure
- **Rich CLI**: Beautiful terminal interface with progress indicators

## 🎯 Use Cases

### Company Internal Components
```bash
zen add https://github.com/company/components/tree/main/auth/sso
zen add https://github.com/company/components/tree/main/data/processor
```

### Open Source Components
```bash
zen add https://github.com/TheRaj71/Zenive/tree/main/components/email-validator
zen add https://github.com/TheRaj71/Zenive/tree/main/components/jwt-auth
```

### Personal Collections
```bash
zen add https://github.com/yourusername/my-components/tree/main/text-utils
zen add https://github.com/yourusername/my-components/tree/main/config-loader
```

## 🔄 Development Workflow

1. **Create** component JSON with embedded Python code
2. **Host** JSON file on GitHub, website, CDN, etc.
3. **Share** URL with users
4. **Users install** with `zen add <your-url>`
5. **Files copied** directly into user projects
6. **Dependencies** automatically added to requirements.txt

## 🆚 Why zen?

| Feature | zen | pip packages | git submodules |
|---------|--------------|--------------|----------------|
| **Easy Installation** | ✅ `zen add <url>` | ✅ `pip install` | ❌ Complex setup |
| **Code Ownership** | ✅ Files in project | ❌ External dependency | ✅ Files in project |
| **No Registry Lock-in** | ✅ Any GitHub URL | ❌ PyPI only | ✅ Any git repo |
| **Dependency Management** | ✅ Auto-updates requirements.txt | ✅ Auto-installed | ❌ Manual |
| **Easy Customization** | ✅ Edit copied files | ❌ Hard to modify | ✅ Easy to modify |
| **Preview Before Install** | ✅ Shows what will be added | ❌ No preview | ❌ No preview |

## 📖 Examples

### Email Validator Component
```json
{
  "name": "email-validator", 
  "version": "1.0.0",
  "description": "Email validation utilities with multiple validation methods",
  "category": "utils",
  "dependencies": ["email-validator"],
  "files": [
    {
      "name": "validator.py",
      "path": "src/utils/validator.py",
      "url": "./validator.py"
    },
    {
      "name": "__init__.py",
      "path": "src/utils/__init__.py",
      "url": "./__init__.py"
    }
  ]
}
```

### JWT Auth Component
```json
{
  "name": "jwt-auth",
  "version": "2.0.0", 
  "description": "JWT authentication utilities with middleware support",
  "category": "auth",
  "dependencies": ["PyJWT", "cryptography"],
  "files": [
    {
      "name": "jwt_handler.py",
      "path": "src/auth/jwt_handler.py",
      "url": "./jwt_handler.py"
    },
    {
      "name": "middleware.py",
      "path": "src/auth/middleware.py",
      "url": "./middleware.py"
    }
  ]
}
```

## 📚 Documentation

For detailed documentation, see the [docs](./docs/) folder:

- [Animation Features](./docs/ANIMATION_FEATURES.md) - Beautiful CLI animations and visual effects
- [Usage Guide](./docs/USAGE_GUIDE.md) - Comprehensive usage instructions
- [Examples](./docs/EXAMPLES.md) - Component examples and use cases
- [API Reference](./docs/API_REFERENCE.md) - Complete API documentation
- [Template Development](./docs/TEMPLATE_DEVELOPMENT.md) - Creating custom templates
- [Troubleshooting](./docs/TROUBLESHOOTING.md) - Common issues and solutions

## 🤝 Contributing

zen is open source. Contributions welcome!

- **GitHub**: https://github.com/TheRaj71/Zenive
- **Issues**: https://github.com/TheRaj71/Zenive/issues

## 📄 License

MIT License - see LICENSE file for details.

---

**zen** - Python components made simple, inspired by shadcn/ui ✨
