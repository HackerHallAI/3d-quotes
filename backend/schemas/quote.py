"""
Quote API schemas for the 3D Quotes application.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from models.quote import BoundingBox, MaterialType, ShippingSize


class FileUploadRequest(BaseModel):
    """
    Schema for individual file in upload request.
    """
    filename: str = Field(..., min_length=1, max_length=255)
    material: MaterialType
    quantity: int = Field(..., gt=0, le=1000)

    @validator('filename')
    def validate_filename(cls, v):
        if not v.lower().endswith('.stl'):
            raise ValueError('Filename must end with .stl')
        return v

    class Config:
        schema_extra = {
            "example": {
                "filename": "test_part.stl",
                "material": "PA12_GREY",
                "quantity": 2
            }
        }


class QuoteCreateRequest(BaseModel):
    """
    Schema for creating a new quote.
    """
    files: List[FileUploadRequest] = Field(..., min_items=1, max_items=10)
    customer_email: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "files": [
                    {
                        "filename": "part1.stl",
                        "material": "PA12_GREY",
                        "quantity": 1
                    },
                    {
                        "filename": "part2.stl",
                        "material": "PA12_BLACK",
                        "quantity": 3
                    }
                ],
                "customer_email": "customer@example.com"
            }
        }


class STLFileResponse(BaseModel):
    """
    Schema for STL file in API responses.
    """
    filename: str
    file_size: int
    volume: float
    bounding_box: BoundingBox
    is_watertight: bool
    material: MaterialType
    quantity: int
    unit_price: float
    total_price: float
    processed_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QuoteResponse(BaseModel):
    """
    Schema for quote API responses.
    """
    quote_id: str
    files: List[STLFileResponse]
    subtotal: float
    shipping_cost: float
    total: float
    shipping_size: ShippingSize
    estimated_shipping_days: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_valid: bool
    customer_email: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QuoteUpdateRequest(BaseModel):
    """
    Schema for updating quote file quantities or materials.
    """
    file_updates: List[dict] = Field(..., min_items=1)

    class Config:
        schema_extra = {
            "example": {
                "file_updates": [
                    {
                        "filename": "part1.stl",
                        "quantity": 5,
                        "material": "PA12_BLACK"
                    }
                ]
            }
        }


class QuoteSummary(BaseModel):
    """
    Schema for quote summary in list operations.
    """
    quote_id: str
    file_count: int
    total: float
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_valid: bool
    customer_email: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PricingBreakdown(BaseModel):
    """
    Schema for detailed pricing breakdown.
    """
    material_cost: float
    quantity_discount: float
    markup: float
    subtotal: float
    shipping_cost: float
    total: float

    class Config:
        schema_extra = {
            "example": {
                "material_cost": 15.50,
                "quantity_discount": 0.00,
                "markup": 2.33,
                "subtotal": 17.83,
                "shipping_cost": 5.00,
                "total": 22.83
            }
        }
