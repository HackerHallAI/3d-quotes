"""
Validation utilities for the 3D Quotes application.
"""
import re
from typing import List, Optional

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError


class ValidationError(Exception):
    """
    Custom validation error for application-specific validation.
    """
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class ProcessingError(Exception):
    """
    Custom error for file processing failures.
    """
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class EmailValidator:
    """
    Email validation utilities.
    """

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if valid email format
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


class FileValidator:
    """
    File validation utilities.
    """

    @staticmethod
    def validate_filename(filename: str, allowed_extensions: List[str]) -> bool:
        """
        Validate filename and extension.
        
        Args:
            filename: Filename to validate
            allowed_extensions: List of allowed extensions
            
        Returns:
            bool: True if valid filename
        """
        if not filename or len(filename.strip()) == 0:
            return False

        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in filename for char in invalid_chars):
            return False

        # Check extension
        filename_lower = filename.lower()
        return any(filename_lower.endswith(ext.lower()) for ext in allowed_extensions)

    @staticmethod
    def validate_file_size(file_size: int, max_size: int) -> bool:
        """
        Validate file size.
        
        Args:
            file_size: File size in bytes
            max_size: Maximum allowed size in bytes
            
        Returns:
            bool: True if file size is valid
        """
        return 0 < file_size <= max_size


class PricingValidator:
    """
    Pricing validation utilities.
    """

    @staticmethod
    def validate_minimum_order(total: float, minimum: float) -> bool:
        """
        Validate minimum order value.
        
        Args:
            total: Total order value
            minimum: Minimum required value
            
        Returns:
            bool: True if meets minimum order requirement
        """
        return total >= minimum

    @staticmethod
    def validate_quantity(quantity: int, max_quantity: int = 1000) -> bool:
        """
        Validate quantity value.
        
        Args:
            quantity: Quantity to validate
            max_quantity: Maximum allowed quantity
            
        Returns:
            bool: True if quantity is valid
        """
        return 1 <= quantity <= max_quantity

    @staticmethod
    def validate_price(price: float) -> bool:
        """
        Validate price value.
        
        Args:
            price: Price to validate
            
        Returns:
            bool: True if price is valid
        """
        return price >= 0 and price < 1000000  # Reasonable upper limit


class AddressValidator:
    """
    Address validation utilities.
    """

    @staticmethod
    def validate_postal_code(postal_code: str, country: str = "NZ") -> bool:
        """
        Validate postal code format.
        
        Args:
            postal_code: Postal code to validate
            country: Country code (default: NZ)
            
        Returns:
            bool: True if valid postal code format
        """
        if country.upper() == "NZ":
            # New Zealand postal codes are 4 digits
            return re.match(r'^\d{4}$', postal_code) is not None

        # Add more country-specific validation as needed
        return len(postal_code.strip()) > 0

    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """
        Validate phone number format (basic validation).
        
        Args:
            phone: Phone number to validate
            
        Returns:
            bool: True if valid phone number format
        """
        # Remove common separators and spaces
        cleaned = re.sub(r'[^\d+]', '', phone)

        # Check for reasonable length (7-15 digits, possibly with + prefix)
        if cleaned.startswith('+'):
            return 8 <= len(cleaned) <= 16
        else:
            return 7 <= len(cleaned) <= 15


def validate_model_data(model_class: BaseModel, data: dict) -> tuple[bool, List[str]]:
    """
    Validate data against a Pydantic model.
    
    Args:
        model_class: Pydantic model class
        data: Data to validate
        
    Returns:
        tuple: (is_valid, list_of_errors)
    """
    try:
        model_class(**data)
        return True, []
    except PydanticValidationError as e:
        errors = []
        for error in e.errors():
            field = '.'.join(str(loc) for loc in error['loc'])
            message = error['msg']
            errors.append(f"{field}: {message}")
        return False, errors


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove invalid characters
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')

    # Limit length
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        sanitized = name[:max_name_length] + ('.' + ext if ext else '')

    return sanitized


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate UUID format.
    
    Args:
        uuid_string: UUID string to validate
        
    Returns:
        bool: True if valid UUID format
    """
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return re.match(uuid_pattern, uuid_string.lower()) is not None
