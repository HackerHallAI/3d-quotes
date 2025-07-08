"""
Order router for the 3D Quotes application.

This module handles order management endpoints.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status

from models.order import OrderStatus, PaymentStatus
from schemas.order import OrderResponse, OrderSummaryResponse, OrderUpdateRequest
from utils.validators import validate_uuid

# Import order storage from payment router
from routers.payment import orders_storage

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    """
    Get order details by ID.
    
    Args:
        order_id: Order ID
        
    Returns:
        OrderResponse: Order details
    """
    # Validate order ID format
    if not validate_uuid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID format"
        )

    order = orders_storage.get(order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return OrderResponse.from_orm(order)


@router.get("/", response_model=List[OrderSummaryResponse])
async def list_orders(
    customer_email: Optional[str] = None,
    status: Optional[OrderStatus] = None,
    payment_status: Optional[PaymentStatus] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List orders with optional filtering.
    
    Args:
        customer_email: Filter by customer email
        status: Filter by order status
        payment_status: Filter by payment status
        limit: Maximum number of orders to return
        offset: Number of orders to skip
        
    Returns:
        List[OrderSummaryResponse]: List of order summaries
    """
    orders = list(orders_storage.values())

    # Apply filters
    if customer_email:
        orders = [o for o in orders if o.customer.email == customer_email]

    if status:
        orders = [o for o in orders if o.status == status]

    if payment_status:
        orders = [o for o in orders if o.payment_status == payment_status]

    # Sort by creation date (newest first)
    orders.sort(key=lambda x: x.created_at, reverse=True)

    # Apply pagination
    orders = orders[offset:offset + limit]

    # Convert to summary format
    summaries = []
    for order in orders:
        summary = OrderSummaryResponse(
            order_id=order.order_id,
            customer_email=order.customer.email,
            customer_name=f"{order.customer.first_name} {order.customer.last_name}",
            total_amount=order.amount_paid,
            status=order.status,
            payment_status=order.payment_status,
            created_at=order.created_at,
            file_count=len(order.quote.files)
        )
        summaries.append(summary)

    return summaries


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(order_id: str, request: OrderUpdateRequest):
    """
    Update order status and information.
    
    Args:
        order_id: Order ID
        request: Order update request
        
    Returns:
        OrderResponse: Updated order details
    """
    # Validate order ID format
    if not validate_uuid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID format"
        )

    order = orders_storage.get(order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Update fields if provided
    if request.status:
        order.status = request.status

    if request.order_notes:
        order.order_notes = request.order_notes

    if request.zoho_sales_order_id:
        order.zoho_sales_order_id = request.zoho_sales_order_id

    if request.zoho_contact_id:
        order.zoho_contact_id = request.zoho_contact_id

    logger.info(f"Updated order {order_id}")

    return OrderResponse.from_orm(order)


@router.get("/stats/summary")
async def get_order_stats():
    """
    Get order statistics summary.
    
    Returns:
        dict: Order statistics
    """
    orders = list(orders_storage.values())

    # Calculate statistics
    total_orders = len(orders)
    total_revenue = sum(order.amount_paid for order in orders if order.payment_status == PaymentStatus.SUCCESS)

    # Count by status
    status_counts = {}
    for status in OrderStatus:
        status_counts[status.value] = len([o for o in orders if o.status == status])

    # Count by payment status
    payment_counts = {}
    for payment_status in PaymentStatus:
        payment_counts[payment_status.value] = len([o for o in orders if o.payment_status == payment_status])

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "status_counts": status_counts,
        "payment_counts": payment_counts
    }
