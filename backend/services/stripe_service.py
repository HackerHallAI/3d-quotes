"""
Stripe payment service for the 3D Quotes application.

This module handles payment intent creation, payment confirmation,
and webhook processing for Stripe payments.
"""
import logging
from typing import Any, Dict, Optional

import stripe
from stripe.error import StripeError

from config.settings import settings
from models.order import PaymentStatus

logger = logging.getLogger(__name__)

# Configure Stripe with API key
stripe.api_key = settings.stripe_secret_key


class PaymentError(Exception):
    """
    Custom payment error for payment processing failures.
    """
    def __init__(self, message: str, stripe_error: Optional[StripeError] = None):
        self.message = message
        self.stripe_error = stripe_error
        super().__init__(self.message)


class StripeService:
    """
    Service for handling Stripe payment operations.
    """

    def __init__(self):
        self.webhook_secret = settings.stripe_webhook_secret
        self.currency = settings.currency.lower()

    async def create_payment_intent(
        self,
        amount: float,
        quote_id: str,
        customer_email: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a payment intent for a quote.
        
        Args:
            amount: Payment amount in USD
            quote_id: Quote ID
            customer_email: Customer email address
            metadata: Optional additional metadata
            
        Returns:
            dict: Payment intent data
            
        Raises:
            PaymentError: If payment intent creation fails
        """
        try:
            # Convert amount to cents (Stripe expects amounts in cents)
            amount_cents = int(amount * 100)

            # Prepare metadata
            intent_metadata = {
                'quote_id': quote_id,
                'customer_email': customer_email,
                'source': '3d_quotes_tool'
            }

            if metadata:
                intent_metadata.update(metadata)

            # PATTERN: Use payment intents, not charges
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=self.currency,
                metadata=intent_metadata,
                receipt_email=customer_email,
                automatic_payment_methods={'enabled': True}
            )

            logger.info(f"Created payment intent {intent.id} for quote {quote_id}: ${amount:.2f}")

            return {
                'payment_intent_id': intent.id,
                'client_secret': intent.client_secret,
                'amount': amount_cents,
                'currency': self.currency,
                'status': intent.status
            }

        except StripeError as e:
            logger.error(f"Stripe error creating payment intent: {e}")
            raise PaymentError(f"Payment processing failed: {e.user_message or str(e)}", e)
        except Exception as e:
            logger.error(f"Unexpected error creating payment intent: {e}")
            raise PaymentError(f"Payment processing failed: {str(e)}")

    async def retrieve_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Retrieve a payment intent by ID.
        
        Args:
            payment_intent_id: Payment intent ID
            
        Returns:
            dict: Payment intent data
            
        Raises:
            PaymentError: If retrieval fails
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                'id': intent.id,
                'amount': intent.amount,
                'currency': intent.currency,
                'status': intent.status,
                'metadata': intent.metadata,
                'receipt_email': intent.receipt_email,
                'created': intent.created
            }

        except StripeError as e:
            logger.error(f"Stripe error retrieving payment intent {payment_intent_id}: {e}")
            raise PaymentError(f"Failed to retrieve payment: {e.user_message or str(e)}", e)

    async def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Confirm a payment intent.
        
        Args:
            payment_intent_id: Payment intent ID
            payment_method_id: Optional payment method ID
            
        Returns:
            dict: Confirmed payment intent data
            
        Raises:
            PaymentError: If confirmation fails
        """
        try:
            confirm_params = {}
            if payment_method_id:
                confirm_params['payment_method'] = payment_method_id

            intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                **confirm_params
            )

            logger.info(f"Confirmed payment intent {payment_intent_id}: {intent.status}")

            return {
                'id': intent.id,
                'status': intent.status,
                'amount': intent.amount,
                'currency': intent.currency,
                'metadata': intent.metadata
            }

        except StripeError as e:
            logger.error(f"Stripe error confirming payment intent {payment_intent_id}: {e}")
            raise PaymentError(f"Payment confirmation failed: {e.user_message or str(e)}", e)

    async def cancel_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Cancel a payment intent.
        
        Args:
            payment_intent_id: Payment intent ID
            
        Returns:
            dict: Cancelled payment intent data
            
        Raises:
            PaymentError: If cancellation fails
        """
        try:
            intent = stripe.PaymentIntent.cancel(payment_intent_id)

            logger.info(f"Cancelled payment intent {payment_intent_id}")

            return {
                'id': intent.id,
                'status': intent.status,
                'amount': intent.amount,
                'currency': intent.currency
            }

        except StripeError as e:
            logger.error(f"Stripe error cancelling payment intent {payment_intent_id}: {e}")
            raise PaymentError(f"Payment cancellation failed: {e.user_message or str(e)}", e)

    async def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a refund for a payment intent.
        
        Args:
            payment_intent_id: Payment intent ID
            amount: Refund amount (if None, full refund)
            reason: Refund reason
            
        Returns:
            dict: Refund data
            
        Raises:
            PaymentError: If refund creation fails
        """
        try:
            refund_params = {
                'payment_intent': payment_intent_id
            }

            if amount:
                refund_params['amount'] = int(amount * 100)  # Convert to cents

            if reason:
                refund_params['reason'] = reason

            refund = stripe.Refund.create(**refund_params)

            logger.info(f"Created refund {refund.id} for payment intent {payment_intent_id}")

            return {
                'id': refund.id,
                'amount': refund.amount,
                'currency': refund.currency,
                'status': refund.status,
                'reason': refund.reason,
                'payment_intent': refund.payment_intent
            }

        except StripeError as e:
            logger.error(f"Stripe error creating refund for {payment_intent_id}: {e}")
            raise PaymentError(f"Refund creation failed: {e.user_message or str(e)}", e)

    def verify_webhook_signature(self, payload: bytes, sig_header: str) -> bool:
        """
        Verify webhook signature for security.
        
        Args:
            payload: Webhook payload
            sig_header: Stripe signature header
            
        Returns:
            bool: True if signature is valid
        """
        try:
            stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return True
        except ValueError:
            logger.error("Invalid webhook payload")
            return False
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            return False

    async def process_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process webhook events from Stripe.
        
        Args:
            event: Stripe webhook event
            
        Returns:
            dict: Processing result
        """
        event_type = event['type']
        event_data = event['data']['object']

        logger.info(f"Processing webhook event: {event_type}")

        try:
            if event_type == 'payment_intent.succeeded':
                return await self._handle_payment_succeeded(event_data)
            elif event_type == 'payment_intent.payment_failed':
                return await self._handle_payment_failed(event_data)
            elif event_type == 'payment_intent.canceled':
                return await self._handle_payment_canceled(event_data)
            elif event_type == 'payment_intent.requires_action':
                return await self._handle_payment_requires_action(event_data)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return {'status': 'ignored', 'event_type': event_type}

        except Exception as e:
            logger.error(f"Error processing webhook event {event_type}: {e}")
            return {'status': 'error', 'message': str(e)}

    async def _handle_payment_succeeded(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle successful payment webhook.
        
        Args:
            payment_intent: Payment intent data
            
        Returns:
            dict: Processing result
        """
        payment_intent_id = payment_intent['id']
        metadata = payment_intent.get('metadata', {})
        quote_id = metadata.get('quote_id')

        logger.info(f"Payment succeeded for intent {payment_intent_id}, quote {quote_id}")

        # Here you would typically:
        # 1. Update order status to paid
        # 2. Send confirmation email
        # 3. Trigger Zoho integration
        # 4. Notify supplier

        return {
            'status': 'success',
            'payment_intent_id': payment_intent_id,
            'quote_id': quote_id,
            'amount': payment_intent['amount'],
            'currency': payment_intent['currency']
        }

    async def _handle_payment_failed(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle failed payment webhook.
        
        Args:
            payment_intent: Payment intent data
            
        Returns:
            dict: Processing result
        """
        payment_intent_id = payment_intent['id']
        metadata = payment_intent.get('metadata', {})
        quote_id = metadata.get('quote_id')

        logger.warning(f"Payment failed for intent {payment_intent_id}, quote {quote_id}")

        # Here you would typically:
        # 1. Update order status to failed
        # 2. Send failure notification
        # 3. Log failure reason

        return {
            'status': 'failed',
            'payment_intent_id': payment_intent_id,
            'quote_id': quote_id,
            'last_payment_error': payment_intent.get('last_payment_error')
        }

    async def _handle_payment_canceled(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle canceled payment webhook.
        
        Args:
            payment_intent: Payment intent data
            
        Returns:
            dict: Processing result
        """
        payment_intent_id = payment_intent['id']
        metadata = payment_intent.get('metadata', {})
        quote_id = metadata.get('quote_id')

        logger.info(f"Payment canceled for intent {payment_intent_id}, quote {quote_id}")

        return {
            'status': 'canceled',
            'payment_intent_id': payment_intent_id,
            'quote_id': quote_id
        }

    async def _handle_payment_requires_action(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle payment requiring action webhook.
        
        Args:
            payment_intent: Payment intent data
            
        Returns:
            dict: Processing result
        """
        payment_intent_id = payment_intent['id']
        metadata = payment_intent.get('metadata', {})
        quote_id = metadata.get('quote_id')

        logger.info(f"Payment requires action for intent {payment_intent_id}, quote {quote_id}")

        return {
            'status': 'requires_action',
            'payment_intent_id': payment_intent_id,
            'quote_id': quote_id,
            'next_action': payment_intent.get('next_action')
        }

    def get_payment_status(self, stripe_status: str) -> PaymentStatus:
        """
        Convert Stripe payment status to internal status.
        
        Args:
            stripe_status: Stripe payment intent status
            
        Returns:
            PaymentStatus: Internal payment status
        """
        status_mapping = {
            'succeeded': PaymentStatus.SUCCESS,
            'canceled': PaymentStatus.FAILED,
            'requires_payment_method': PaymentStatus.PENDING,
            'requires_confirmation': PaymentStatus.PENDING,
            'requires_action': PaymentStatus.PENDING,
            'processing': PaymentStatus.PENDING,
            'requires_capture': PaymentStatus.PENDING
        }

        return status_mapping.get(stripe_status, PaymentStatus.FAILED)


# Global service instance
stripe_service = StripeService()
