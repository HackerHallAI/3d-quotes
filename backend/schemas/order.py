"""
Order API schemas for the 3D Quotes application.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from models.order import OrderStatus, PaymentStatus
from .customer import CustomerResponse
from .quote import QuoteResponse


class OrderCreateRequest(BaseModel):
    """
    Schema for creating a new order from a quote.
    """
    quote_id: str = Field(..., min_length=1)
    customer_info: dict = Field(..., description="Customer information")
    payment_method_id: Optional[str] = Field(None, description="Stripe payment method ID")

    class Config:
        schema_extra = {
            "example": {
                "quote_id": "123e4567-e89b-12d3-a456-426614174000",
                "customer_info": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "phone": "+64 9 123 4567",
                    "address_line1": "123 Queen Street",
                    "city": "Auckland",
                    "postal_code": "1010",
                    "country": "NZ"
                },
                "payment_method_id": "pm_1234567890"
            }
        }


class OrderUpdateRequest(BaseModel):
    """
    Schema for updating order status and information.
    """
    status: Optional[OrderStatus] = None
    order_notes: Optional[str] = Field(None, max_length=1000)
    zoho_sales_order_id: Optional[str] = None
    zoho_contact_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "status": "IN_PRODUCTION",
                "order_notes": "Order is in production, estimated completion in 3 days",
                "zoho_sales_order_id": "SO-123456"
            }
        }


class OrderResponse(BaseModel):
    """
    Schema for order API responses.
    """
    order_id: str
    quote: QuoteResponse
    customer: CustomerResponse
    payment_intent_id: str
    payment_status: PaymentStatus
    amount_paid: float
    status: OrderStatus
    order_notes: Optional[str] = None
    zoho_sales_order_id: Optional[str] = None
    zoho_contact_id: Optional[str] = None
    created_at: datetime
    paid_at: Optional[datetime] = None
    supplier_notified_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OrderSummaryResponse(BaseModel):
    """
    Schema for order summary in list operations.
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
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaymentIntentRequest(BaseModel):
    """
    Schema for creating Stripe payment intent.
    """
    quote_id: str = Field(..., min_length=1)
    customer_email: str = Field(..., min_length=1)

    class Config:
        schema_extra = {
            "example": {
                "quote_id": "123e4567-e89b-12d3-a456-426614174000",
                "customer_email": "customer@example.com"
            }
        }


class PaymentIntentResponse(BaseModel):
    """
    Schema for payment intent API responses.
    """
    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str

    class Config:
        schema_extra = {
            "example": {
                "client_secret": "pi_1234567890_secret_abcdefghijk",
                "payment_intent_id": "pi_1234567890",
                "amount": 2500,
                "currency": "usd"
            }
        }


class PaymentConfirmationRequest(BaseModel):
    """
    Schema for confirming payment completion.
    """
    payment_intent_id: str = Field(..., min_length=1)
    order_id: str = Field(..., min_length=1)

    class Config:
        schema_extra = {
            "example": {
                "payment_intent_id": "pi_1234567890",
                "order_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class SupplierNotificationRequest(BaseModel):
    """
    Schema for triggering supplier notifications.
    """
    order_id: str = Field(..., min_length=1)
    special_instructions: Optional[str] = Field(None, max_length=1000)

    class Config:
        schema_extra = {
            "example": {
                "order_id": "123e4567-e89b-12d3-a456-426614174000",
                "special_instructions": "Rush order - please prioritize"
            }
        }
