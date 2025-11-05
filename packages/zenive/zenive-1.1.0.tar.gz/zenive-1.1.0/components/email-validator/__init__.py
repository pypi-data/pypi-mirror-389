"""
Email validation utilities for zen projects.

This module provides comprehensive email validation functionality including:
- Basic regex validation
- Advanced validation with email-validator package
- Domain extraction and business email detection

Usage:
    from utils.validator import validate_email, extract_domain, is_business_email
    
    # Basic usage
    is_valid = validate_email("user@example.com")
    
    # Extract domain
    domain = extract_domain("user@example.com")  # Returns "example.com"
    
    # Check if business email
    is_biz = is_business_email("user@company.com")  # Returns True
"""

from .validator import (
    validate_email,
    validate_email_basic,
    validate_email_advanced,
    extract_domain,
    is_business_email
)

__all__ = [
    'validate_email',
    'validate_email_basic', 
    'validate_email_advanced',
    'extract_domain',
    'is_business_email'
]

__version__ = "1.0.0"
__author__ = "zen"