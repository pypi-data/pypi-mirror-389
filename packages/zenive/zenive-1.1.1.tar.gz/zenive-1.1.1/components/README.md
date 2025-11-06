# zen Example Components

This directory contains example components demonstrating the zen component system.

## Available Components

### 📧 Email Validator
**Path:** `email-validator/`
**Description:** Comprehensive email validation utility with multiple validation methods
**Dependencies:** `email-validator`

Features:
- Basic regex validation
- Advanced validation with email-validator package
- Domain extraction
- Business email detection

### 🔐 JWT Authentication
**Path:** `jwt-auth/`
**Description:** Complete JWT authentication system with middleware support
**Dependencies:** `PyJWT`, `cryptography`

Features:
- Token generation and validation
- Access and refresh tokens
- Flask and FastAPI middleware
- Role-based access control
- RSA key generation

## Installation

Install any component using:

```bash
# From this repository
zen add https://github.com/TheRaj71/Zenive/tree/main/components/email-validator
zen add https://github.com/TheRaj71/Zenive/tree/main/components/jwt-auth

# Or from raw URLs
zen add https://raw.githubusercontent.com/TheRaj71/Zenive/main/components/email-validator/component.json
```

## Creating Your Own Components

1. Create a directory for your component
2. Add your Python files
3. Create a `component.json` file referencing your files
4. Push to GitHub and share the URL

See the existing components as examples of the structure and format.