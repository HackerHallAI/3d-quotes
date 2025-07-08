"""
Customer data models for the 3D Quotes application.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class CustomerInfo(BaseModel):
    """
    Customer information model.
    
    Contains customer details required for order processing.
    """
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=100)

    # Shipping address
    address_line1: str = Field(..., min_length=1, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(default="NZ", max_length=10)

    # Metadata
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    zoho_contact_id: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CustomerContact(BaseModel):
    """
    Simplified customer contact model for quick operations.
    """
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=100)
