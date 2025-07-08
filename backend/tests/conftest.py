"""
Pytest configuration and shared fixtures.
"""
import os
import tempfile
from unittest.mock import Mock

import pytest

from models.quote import BoundingBox, STLFile


@pytest.fixture
def sample_stl_info():
    """Create a sample STL file info for testing."""
    return STLFile(
        filename="test_cube.stl",
        file_size=1024,
        volume=27.0,  # 3x3x3 cube
        bounding_box=BoundingBox(
            min_x=0.0, max_x=3.0,
            min_y=0.0, max_y=3.0,
            min_z=0.0, max_z=3.0
        ),
        is_watertight=True
    )


@pytest.fixture
def sample_large_stl_info():
    """Create a sample large STL file info for testing."""
    return STLFile(
        filename="large_part.stl",
        file_size=5120,
        volume=125.0,  # 5x5x5 cube
        bounding_box=BoundingBox(
            min_x=0.0, max_x=5.0,
            min_y=0.0, max_y=5.0,
            min_z=0.0, max_z=5.0
        ),
        is_watertight=True
    )


@pytest.fixture
def sample_invalid_stl_info():
    """Create a sample invalid STL file info for testing."""
    return STLFile(
        filename="invalid_part.stl",
        file_size=512,
        volume=0.1,  # Too small
        bounding_box=BoundingBox(
            min_x=0.0, max_x=0.1,
            min_y=0.0, max_y=0.1,
            min_z=0.0, max_z=0.1
        ),
        is_watertight=False  # Not watertight
    )


@pytest.fixture
def temp_stl_file():
    """Create a temporary STL file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp_file:
        # Write minimal STL content
        stl_content = b'''solid test
facet normal 0 0 1
  outer loop
    vertex 0 0 0
    vertex 1 0 0
    vertex 0 1 0
  endloop
endfacet
endsolid test
'''
        tmp_file.write(stl_content)
        tmp_file.flush()
        yield tmp_file.name

    # Cleanup
    try:
        os.unlink(tmp_file.name)
    except FileNotFoundError:
        pass


@pytest.fixture
def mock_stripe_payment_intent():
    """Create a mock Stripe payment intent."""
    mock_intent = Mock()
    mock_intent.id = "pi_test_12345"
    mock_intent.client_secret = "pi_test_12345_secret_abc123"
    mock_intent.amount = 5000  # $50.00 in cents
    mock_intent.currency = "usd"
    mock_intent.status = "requires_payment_method"
    mock_intent.metadata = {"quote_id": "quote_123", "customer_email": "test@example.com"}
    return mock_intent


@pytest.fixture
def mock_stripe_payment_intent_succeeded():
    """Create a mock successful Stripe payment intent."""
    mock_intent = Mock()
    mock_intent.id = "pi_test_12345"
    mock_intent.client_secret = "pi_test_12345_secret_abc123"
    mock_intent.amount = 5000  # $50.00 in cents
    mock_intent.currency = "usd"
    mock_intent.status = "succeeded"
    mock_intent.metadata = {"quote_id": "quote_123", "order_id": "order_456"}
    return mock_intent


@pytest.fixture
def sample_customer_info():
    """Create sample customer information."""
    return {
        "firstName": "John",
        "lastName": "Doe",
        "email": "john.doe@example.com",
        "phone": "+64 21 123 4567",
        "company": "Test Company Ltd",
        "addressLine1": "123 Test Street",
        "addressLine2": "Unit 1",
        "city": "Auckland",
        "state": "Auckland",
        "postalCode": "1010",
        "country": "NZ"
    }


@pytest.fixture
def sample_quote_data():
    """Create sample quote data."""
    return {
        "quote_id": "quote_123456",
        "customer_email": "test@example.com",
        "files": [
            {
                "filename": "cube.stl",
                "file_size": 1024,
                "volume": 27.0,
                "material": "pa12",
                "quantity": 2,
                "unit_price": 15.50,
                "total_price": 31.00,
                "bounding_box": {
                    "min_x": 0.0, "max_x": 3.0,
                    "min_y": 0.0, "max_y": 3.0,
                    "min_z": 0.0, "max_z": 3.0
                },
                "is_watertight": True
            }
        ],
        "subtotal": 31.00,
        "shipping_cost": 15.00,
        "shipping_size": "small",
        "total": 46.00,
        "estimated_shipping_days": 5,
        "currency": "USD",
        "is_valid": True,
        "expires_at": "2024-12-31T23:59:59Z",
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables."""
    # Mock environment variables
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake_key")
    monkeypatch.setenv("STRIPE_PUBLISHABLE_KEY", "pk_test_fake_key")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test_fake_secret")
    monkeypatch.setenv("ZOHO_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("ZOHO_CLIENT_SECRET", "test_client_secret")
    monkeypatch.setenv("ZOHO_REFRESH_TOKEN", "test_refresh_token")
    monkeypatch.setenv("EMAIL_HOST", "smtp.test.com")
    monkeypatch.setenv("EMAIL_PORT", "587")
    monkeypatch.setenv("EMAIL_USER", "test@test.com")
    monkeypatch.setenv("EMAIL_PASSWORD", "test_password")
    monkeypatch.setenv("SUPPLIER_EMAIL", "supplier@test.com")


@pytest.fixture
def cleanup_test_files():
    """Fixture to track and cleanup test files."""
    test_files = []

    def add_file(filepath):
        test_files.append(filepath)
        return filepath

    yield add_file

    # Cleanup
    for filepath in test_files:
        try:
            if os.path.exists(filepath):
                os.unlink(filepath)
        except Exception:
            pass  # Ignore cleanup errors
