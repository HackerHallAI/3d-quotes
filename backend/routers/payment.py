"""
Payment router for the 3D Quotes application.

This module handles payment intent creation, confirmation, and webhook processing.
"""
import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request, status

from models.customer import CustomerInfo
from models.order import Order, OrderStatus, PaymentStatus
from schemas.order import (
    OrderCreateRequest,
    OrderResponse,
    PaymentConfirmationRequest,
    PaymentIntentRequest,
    PaymentIntentResponse,
)
from services.stripe_service import PaymentError, stripe_service
from utils.validators import ValidationError, validate_uuid

# Import quote storage from quote router
from routers.quote import quotes_storage

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for orders (in production, use a database)
orders_storage: Dict[str, Order] = {}


@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(request: PaymentIntentRequest):
    """
    Create a payment intent for a quote.
    
    Args:
        request: Payment intent request data
        
    Returns:
        PaymentIntentResponse: Payment intent details
    """
    try:
        # Validate quote ID format
        if not validate_uuid(request.quote_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid quote ID format"
            )

        # Get quote from storage
        quote = quotes_storage.get(request.quote_id)
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote not found"
            )

        # Check if quote is still valid
        if not quote.is_valid:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Quote has expired"
            )

        # Create payment intent
        intent_data = await stripe_service.create_payment_intent(
            amount=quote.total,
            quote_id=request.quote_id,
            customer_email=request.customer_email,
            metadata={
                'file_count': str(len(quote.files)),
                'shipping_size': quote.shipping_size.value
            }
        )

        logger.info(f"Created payment intent for quote {request.quote_id}: ${quote.total}")

        return PaymentIntentResponse(
            client_secret=intent_data['client_secret'],
            payment_intent_id=intent_data['payment_intent_id'],
            amount=intent_data['amount'],
            currency=intent_data['currency']
        )

    except PaymentError as e:
        logger.error(f"Payment error creating intent: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error creating payment intent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating payment intent"
        )


@router.post("/create-order", response_model=OrderResponse)
async def create_order_with_payment(request: OrderCreateRequest):
    """
    Create an order with payment intent.
    
    Args:
        request: Order creation request
        
    Returns:
        OrderResponse: Created order details
    """
    try:
        # Validate quote ID format
        if not validate_uuid(request.quote_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid quote ID format"
            )

        # Get quote from storage
        quote = quotes_storage.get(request.quote_id)
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote not found"
            )

        # Check if quote is still valid
        if not quote.is_valid:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Quote has expired"
            )

        # Create customer info
        customer_info = CustomerInfo(**request.customer_info)

        # Create payment intent
        intent_data = await stripe_service.create_payment_intent(
            amount=quote.total,
            quote_id=request.quote_id,
            customer_email=customer_info.email,
            metadata={
                'customer_name': f"{customer_info.first_name} {customer_info.last_name}",
                'file_count': str(len(quote.files)),
                'shipping_size': quote.shipping_size.value
            }
        )

        # Create order
        order = Order(
            quote=quote,
            customer=customer_info,
            payment_intent_id=intent_data['payment_intent_id'],
            payment_status=PaymentStatus.PENDING,
            amount_paid=quote.total,
            status=OrderStatus.QUOTE,  # Will be updated to PAID when payment succeeds
            created_at=datetime.utcnow()
        )

        # Store order
        orders_storage[order.order_id] = order

        logger.info(f"Created order {order.order_id} for quote {request.quote_id}")

        # Return order response with payment intent
        order_response = OrderResponse.from_orm(order)
        order_response.payment_intent_client_secret = intent_data['client_secret']

        return order_response

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except PaymentError as e:
        logger.error(f"Payment error creating order: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error creating order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating order"
        )


@router.post("/confirm")
async def confirm_payment(request: PaymentConfirmationRequest):
    """
    Confirm payment completion.
    
    Args:
        request: Payment confirmation request
        
    Returns:
        dict: Confirmation result
    """
    try:
        # Validate order ID format
        if not validate_uuid(request.order_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid order ID format"
            )

        # Get order from storage
        order = orders_storage.get(request.order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        # Verify payment intent matches
        if order.payment_intent_id != request.payment_intent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment intent ID does not match order"
            )

        # Retrieve payment intent from Stripe
        intent_data = await stripe_service.retrieve_payment_intent(request.payment_intent_id)

        # Update order status based on payment status
        stripe_status = intent_data['status']
        payment_status = stripe_service.get_payment_status(stripe_status)

        order.payment_status = payment_status

        if payment_status == PaymentStatus.SUCCESS:
            order.status = OrderStatus.PAID
            order.paid_at = datetime.utcnow()

            logger.info(f"Payment confirmed for order {request.order_id}")

            # Here you would typically:
            # 1. Send confirmation email
            # 2. Trigger Zoho integration
            # 3. Notify supplier

            return {
                "status": "success",
                "order_id": request.order_id,
                "payment_intent_id": request.payment_intent_id,
                "amount": intent_data['amount'],
                "currency": intent_data['currency']
            }
        else:
            logger.warning(f"Payment not successful for order {request.order_id}: {stripe_status}")

            return {
                "status": "pending",
                "order_id": request.order_id,
                "payment_intent_id": request.payment_intent_id,
                "stripe_status": stripe_status,
                "message": "Payment is still processing or requires action"
            }

    except PaymentError as e:
        logger.error(f"Payment error confirming payment: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error confirming payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while confirming payment"
        )


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.
    
    Args:
        request: FastAPI request object
        
    Returns:
        dict: Webhook processing result
    """
    try:
        # Get request body and signature
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')

        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe signature header"
            )

        # Verify webhook signature
        if not stripe_service.verify_webhook_signature(payload, sig_header):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature"
            )

        # Parse event
        import json
        event = json.loads(payload)

        # Process event
        result = await stripe_service.process_webhook_event(event)

        # Update order status based on webhook event
        if result.get('status') == 'success':
            await _update_order_from_webhook(result)

        logger.info(f"Processed webhook event: {event['type']}")

        return {"status": "success"}

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing webhook"
        )


async def _update_order_from_webhook(webhook_result: Dict[str, Any]) -> None:
    """
    Update order status based on webhook result.
    
    Args:
        webhook_result: Webhook processing result
    """
    try:
        payment_intent_id = webhook_result.get('payment_intent_id')

        if not payment_intent_id:
            return

        # Find order by payment intent ID
        order = None
        for order_id, stored_order in orders_storage.items():
            if stored_order.payment_intent_id == payment_intent_id:
                order = stored_order
                break

        if not order:
            logger.warning(f"Order not found for payment intent {payment_intent_id}")
            return

        # Update order status
        if webhook_result['status'] == 'success':
            order.payment_status = PaymentStatus.SUCCESS
            order.status = OrderStatus.PAID
            order.paid_at = datetime.utcnow()

            logger.info(f"Updated order {order.order_id} to PAID status")

            # Here you would typically:
            # 1. Send confirmation email
            # 2. Trigger Zoho integration
            # 3. Notify supplier

    except Exception as e:
        logger.error(f"Error updating order from webhook: {e}")


@router.get("/intent/{payment_intent_id}")
async def get_payment_intent(payment_intent_id: str):
    """
    Get payment intent details.
    
    Args:
        payment_intent_id: Payment intent ID
        
    Returns:
        dict: Payment intent details
    """
    try:
        intent_data = await stripe_service.retrieve_payment_intent(payment_intent_id)

        return {
            "payment_intent_id": intent_data['id'],
            "amount": intent_data['amount'],
            "currency": intent_data['currency'],
            "status": intent_data['status'],
            "metadata": intent_data['metadata']
        }

    except PaymentError as e:
        logger.error(f"Payment error retrieving intent: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )


@router.post("/cancel/{payment_intent_id}")
async def cancel_payment_intent(payment_intent_id: str):
    """
    Cancel a payment intent.
    
    Args:
        payment_intent_id: Payment intent ID
        
    Returns:
        dict: Cancellation result
    """
    try:
        result = await stripe_service.cancel_payment_intent(payment_intent_id)

        # Update order status if exists
        for order_id, order in orders_storage.items():
            if order.payment_intent_id == payment_intent_id:
                order.payment_status = PaymentStatus.FAILED
                order.status = OrderStatus.CANCELLED
                break

        return {
            "status": "cancelled",
            "payment_intent_id": payment_intent_id
        }

    except PaymentError as e:
        logger.error(f"Payment error cancelling intent: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )


@router.get("/config")
async def get_payment_config():
    """
    Get payment configuration for frontend.
    
    Returns:
        dict: Payment configuration
    """
    from config.settings import settings

    return {
        "stripe_publishable_key": settings.stripe_publishable_key,
        "currency": settings.currency,
        "minimum_order": settings.minimum_order_usd
    }
