"""
Quote data models for the 3D Quotes application.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field, validator


class MaterialType(str, Enum):
    """
    Available material types for 3D printing.
    """
    PA12_GREY = "PA12_GREY"
    PA12_BLACK = "PA12_BLACK"
    PA12_GB = "PA12_GB"


class ShippingSize(str, Enum):
    """
    Shipping size categories for NZ shipping.
    """
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"


class BoundingBox(BaseModel):
    """
    Bounding box dimensions for STL file.
    """
    min_x: float = Field(..., description="Minimum X coordinate")
    min_y: float = Field(..., description="Minimum Y coordinate")
    min_z: float = Field(..., description="Minimum Z coordinate")
    max_x: float = Field(..., description="Maximum X coordinate")
    max_y: float = Field(..., description="Maximum Y coordinate")
    max_z: float = Field(..., description="Maximum Z coordinate")

    @property
    def dimensions(self) -> Tuple[float, float, float]:
        """Calculate dimensions (width, height, depth) of the bounding box."""
        return (
            self.max_x - self.min_x,
            self.max_y - self.min_y,
            self.max_z - self.min_z
        )

    @property
    def volume(self) -> float:
        """Calculate volume of the bounding box."""
        dims = self.dimensions
        return dims[0] * dims[1] * dims[2]


class STLFile(BaseModel):
    """
    STL file data model with calculated properties.
    """
    filename: str = Field(..., min_length=1, max_length=255)
    file_path: Optional[str] = None
    file_size: int = Field(..., gt=0, description="File size in bytes")

    # Calculated properties
    volume: float = Field(..., gt=0, description="Volume in cubic mm")
    bounding_box: BoundingBox
    is_watertight: bool = Field(default=True)

    # Material and quantity
    material: MaterialType
    quantity: int = Field(..., gt=0, le=1000, description="Number of parts to print")

    # Pricing
    unit_price: float = Field(..., ge=0, description="Price per unit in USD")
    total_price: float = Field(..., ge=0, description="Total price for all units in USD")

    # Metadata
    processed_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @validator('filename')
    def validate_filename(cls, v):
        if not v.lower().endswith('.stl'):
            raise ValueError('Filename must end with .stl')
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Quote(BaseModel):
    """
    Complete quote model with files, pricing, and customer information.
    """
    quote_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    files: List[STLFile] = Field(..., min_items=1, max_items=10)

    # Pricing breakdown
    subtotal: float = Field(..., ge=0, description="Subtotal before shipping")
    shipping_cost: float = Field(..., ge=0, description="Shipping cost")
    total: float = Field(..., ge=0, description="Total price including shipping")

    # Shipping information
    shipping_size: ShippingSize
    estimated_shipping_days: int = Field(default=5, ge=1, le=30)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_valid: bool = Field(default=True)

    # Customer reference (optional for initial quote)
    customer_email: Optional[str] = None

    @validator('total')
    def validate_minimum_order(cls, v):
        if v < 20.0:
            raise ValueError('Total order must be at least $20.00 USD')
        return v

    @validator('expires_at', pre=True, always=True)
    def set_expiry_date(cls, v, values):
        if v is None and 'created_at' in values:
            # Quote expires in 24 hours
            created_at = values['created_at']
            return created_at.replace(hour=23, minute=59, second=59)
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QuoteRequest(BaseModel):
    """
    Request model for creating a new quote.
    """
    files: List[dict] = Field(..., min_items=1, max_items=10)
    customer_email: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "files": [
                    {
                        "filename": "test_part.stl",
                        "material": "PA12_GREY",
                        "quantity": 2
                    }
                ],
                "customer_email": "customer@example.com"
            }
        }
