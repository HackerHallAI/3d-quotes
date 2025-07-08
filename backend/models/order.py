"""
Order data models for the 3D Quotes application.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from .customer import CustomerInfo
from .quote import Quote


class OrderStatus(str, Enum):
    """
    Order status tracking states.
    """
    QUOTE = "QUOTE"
    PAID = "PAID"
    SUPPLIER_SENT = "SUPPLIER_SENT"
    IN_PRODUCTION = "IN_PRODUCTION"
    DELIVERED = "DELIVERED"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, Enum):
    """
    Payment status for Stripe integration.
    """
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Order(BaseModel):
    """
    Complete order model with quote, customer, and payment information.
    """
    order_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    quote: Quote
    customer: CustomerInfo

    # Payment information
    payment_intent_id: str = Field(..., min_length=1)
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    amount_paid: float = Field(..., ge=0, description="Amount paid in USD")

    # Order tracking
    status: OrderStatus = Field(default=OrderStatus.PAID)
    order_notes: Optional[str] = Field(None, max_length=1000)

    # External system references
    zoho_sales_order_id: Optional[str] = None
    zoho_contact_id: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    paid_at: Optional[datetime] = None
    supplier_notified_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    @validator('amount_paid')
    def validate_payment_amount(cls, v, values):
        if 'quote' in values and values['quote']:
            if abs(v - values['quote'].total) > 0.01:  # Allow for small rounding differences
                raise ValueError('Payment amount must match quote total')
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OrderUpdate(BaseModel):
    """
    Model for updating order status and information.
    """
    status: Optional[OrderStatus] = None
    order_notes: Optional[str] = Field(None, max_length=1000)
    zoho_sales_order_id: Optional[str] = None
    zoho_contact_id: Optional[str] = None

    # Status-specific timestamps
    supplier_notified_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OrderSummary(BaseModel):
    """
    Simplified order summary for listing operations.
    """
    order_id: str
    customer_email: str
    customer_name: str
    total_amount: float
    status: OrderStatus
    payment_status: PaymentStatus
    created_at: datetime
    file_count: int

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SupplierNotification(BaseModel):
    """
    Model for supplier email notification data.
    """
    order_id: str
    customer_info: CustomerInfo
    quote: Quote
    special_instructions: Optional[str] = None
    files_attached: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
