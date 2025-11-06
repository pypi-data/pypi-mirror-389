"""
Email validation utility for zen projects.

Provides multiple email validation methods:
- Basic regex validation
- Advanced validation using email-validator package
- Domain extraction and validation
"""

import re
from typing import Union, Optional

try:
    from email_validator import validate_email as _validate_email, EmailNotValidError
    HAS_EMAIL_VALIDATOR = True
except ImportError:
    HAS_EMAIL_VALIDATOR = False

# Basic email regex pattern
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

def validate_email_basic(email: str) -> bool:
    """
    Basic email validation using regex.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))

def validate_email_advanced(email: str) -> bool:
    """
    Advanced email validation using email-validator package.
    Falls back to basic validation if package not available.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    if not HAS_EMAIL_VALIDATOR:
        return validate_email_basic(email)
    
    try:
        _validate_email(email)
        return True
    except EmailNotValidError:
        return False
    except Exception:
        return False

def extract_domain(email: str) -> Optional[str]:
    """
    Extract domain from email address.
    
    Args:
        email: Email address
        
    Returns:
        Domain part of email or None if invalid
    """
    if validate_email_basic(email):
        return email.split('@')[1].lower()
    return None

def is_business_email(email: str, exclude_domains: Optional[list] = None) -> bool:
    """
    Check if email is likely a business email (not from common free providers).
    
    Args:
        email: Email address to check
        exclude_domains: Additional domains to exclude (optional)
        
    Returns:
        True if likely business email, False otherwise
    """
    if not validate_email_basic(email):
        return False
    
    domain = extract_domain(email)
    if not domain:
        return False
    
    # Common free email providers
    free_providers = {
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'aol.com', 'icloud.com', 'protonmail.com', 'mail.com'
    }
    
    if exclude_domains:
        free_providers.update(d.lower() for d in exclude_domains)
    
    return domain not in free_providers

# Main validation function (recommended)
def validate_email(email: str, advanced: bool = True) -> bool:
    """
    Validate email address with configurable validation level.
    
    Args:
        email: Email address to validate
        advanced: Use advanced validation if available (default: True)
        
    Returns:
        True if email is valid, False otherwise
    """
    if advanced:
        return validate_email_advanced(email)
    else:
        return validate_email_basic(email)

if __name__ == "__main__":
    # Test the validators
    test_emails = [
        "user@example.com",
        "invalid.email",
        "test@gmail.com",
        "business@company.co.uk"
    ]
    
    print("Email Validation Tests:")
    for email in test_emails:
        basic = validate_email_basic(email)
        advanced = validate_email_advanced(email)
        domain = extract_domain(email)
        business = is_business_email(email)
        
        print(f"  {email}")
        print(f"    Basic: {basic}, Advanced: {advanced}")
        print(f"    Domain: {domain}, Business: {business}")
        print()