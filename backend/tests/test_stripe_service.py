"""
Tests for Stripe payment service.
"""
from unittest.mock import Mock, patch
import pytest

from services.stripe_service import StripeService, PaymentError
from models.order import PaymentStatus


class TestStripeService:
    """Test cases for Stripe service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = StripeService()

    @patch('services.stripe_service.stripe.PaymentIntent.create')
    @pytest.mark.asyncio
    async def test_create_payment_intent_success(self, mock_create):
        """Test successful payment intent creation."""
        # Mock Stripe response
        mock_intent = Mock()
        mock_intent.id = "pi_test_123"
        mock_intent.client_secret = "pi_test_123_secret"
        mock_intent.amount = 5000
        mock_intent.currency = "usd"
        mock_intent.status = "requires_payment_method"
        mock_create.return_value = mock_intent

        result = await self.service.create_payment_intent(
            amount=50.00,
            quote_id="quote_123",
            customer_email="test@example.com"
        )

        assert result["id"] == "pi_test_123"
        assert result["client_secret"] == "pi_test_123_secret"
        assert result["amount"] == 5000
        assert result["currency"] == "usd"
        mock_create.assert_called_once()

    @patch('services.stripe_service.stripe.PaymentIntent.create')
    @pytest.mark.asyncio
    async def test_create_payment_intent_stripe_error(self, mock_create):
        """Test payment intent creation with Stripe error."""
        # Mock Stripe error
        mock_create.side_effect = Exception("Stripe API error")

        with pytest.raises(PaymentError, match="Failed to create payment intent"):
            await self.service.create_payment_intent(
                amount=50.00,
                quote_id="quote_123",
                customer_email="test@example.com"
            )

    @patch('backend.services.stripe_service.stripe.PaymentIntent.retrieve')
    @pytest.mark.asyncio
    async def test_retrieve_payment_intent_success(self, mock_retrieve):
        """Test successful payment intent retrieval."""
        mock_intent = Mock()
        mock_intent.id = "pi_test_123"
        mock_intent.status = "succeeded"
        mock_retrieve.return_value = mock_intent

        result = await self.service.retrieve_payment_intent("pi_test_123")

        assert result["id"] == "pi_test_123"
        assert result["status"] == "succeeded"
        mock_retrieve.assert_called_once_with("pi_test_123")

    @patch('backend.services.stripe_service.stripe.PaymentIntent.confirm')
    @pytest.mark.asyncio
    async def test_confirm_payment_intent_success(self, mock_confirm):
        """Test successful payment confirmation."""
        mock_intent = Mock()
        mock_intent.id = "pi_test_123"
        mock_intent.status = "succeeded"
        mock_confirm.return_value = mock_intent

        result = await self.service.confirm_payment_intent("pi_test_123")

        assert result["id"] == "pi_test_123"
        assert result["status"] == "succeeded"
        mock_confirm.assert_called_once_with("pi_test_123")

    @patch('backend.services.stripe_service.stripe.Refund.create')
    @pytest.mark.asyncio
    async def test_create_refund_success(self, mock_create):
        """Test successful refund creation."""
        mock_refund = Mock()
        mock_refund.id = "re_test_123"
        mock_refund.amount = 5000
        mock_refund.status = "succeeded"
        mock_create.return_value = mock_refund

        result = await self.service.create_refund(
            payment_intent_id="pi_test_123",
            amount=50.00,
            reason="requested_by_customer"
        )

        assert result["id"] == "re_test_123"
        assert result["amount"] == 5000
        assert result["status"] == "succeeded"

    @patch('backend.services.stripe_service.stripe.Webhook.construct_event')
    def test_verify_webhook_signature_success(self, mock_construct):
        """Test successful webhook signature verification."""
        mock_construct.return_value = {"type": "payment_intent.succeeded"}
        
        payload = b'{"test": "data"}'
        sig_header = "test_signature"
        
        result = self.service.verify_webhook_signature(payload, sig_header)
        assert result is True

    @patch('backend.services.stripe_service.stripe.Webhook.construct_event')
    def test_verify_webhook_signature_invalid(self, mock_construct):
        """Test webhook signature verification with invalid signature."""
        mock_construct.side_effect = Exception("Invalid signature")
        
        payload = b'{"test": "data"}'
        sig_header = "invalid_signature"
        
        result = self.service.verify_webhook_signature(payload, sig_header)
        assert result is False

    def test_get_payment_status_mapping(self):
        """Test payment status mapping from Stripe statuses."""
        assert self.service.get_payment_status("succeeded") == PaymentStatus.COMPLETED
        assert self.service.get_payment_status("requires_payment_method") == PaymentStatus.PENDING
        assert self.service.get_payment_status("canceled") == PaymentStatus.CANCELLED
        assert self.service.get_payment_status("processing") == PaymentStatus.PROCESSING
        assert self.service.get_payment_status("unknown_status") == PaymentStatus.PENDING

    @pytest.mark.asyncio
    async def test_process_webhook_event_payment_succeeded(self):
        """Test processing payment succeeded webhook event."""
        event = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_123",
                    "status": "succeeded",
                    "amount": 5000,
                    "metadata": {"quote_id": "quote_123"}
                }
            }
        }

        result = await self.service.process_webhook_event(event)
        
        assert result["event_type"] == "payment_intent.succeeded"
        assert result["payment_intent_id"] == "pi_test_123"
        assert result["status"] == "succeeded"

    @pytest.mark.asyncio
    async def test_process_webhook_event_unsupported_type(self):
        """Test processing unsupported webhook event type."""
        event = {
            "type": "unsupported.event",
            "data": {"object": {}}
        }

        result = await self.service.process_webhook_event(event)
        
        assert result["event_type"] == "unsupported.event"
        assert result["handled"] is False


if __name__ == "__main__":
    pytest.main([__file__])