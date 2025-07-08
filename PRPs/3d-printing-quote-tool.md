name: "3D Printing Quote Tool - Complete Web Application"
description: |

## Purpose
A comprehensive web-based quoting tool for instant 3D printing estimates. This customer-facing tool allows users to upload STL files, select materials and quantities, view live quotes, and complete payment via Stripe. Post-payment, the system triggers supplier emails and creates sales orders in Zoho One.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Build a complete 3D printing quote tool that processes STL files, calculates prices, handles payments, and integrates with external systems for order management.

## Why
- **Business Value**: Streamlines customer order process from file upload to payment
- **Integration**: Connects customer-facing tool with internal CRM and supplier workflow
- **Problems Solved**: Eliminates manual quoting process, reduces order processing time, automates supplier notifications

## What
A full-stack web application with:
- STL file upload and processing (volume/bounding box calculation)
- Material selection and quantity management
- Real-time pricing calculation
- Stripe payment processing
- Zoho CRM/Inventory integration
- Supplier email notifications
- Order tracking system

### Success Criteria
- [ ] Users can upload multiple STL files with integrity checks
- [ ] System calculates volume and bounding box automatically
- [ ] Pricing updates in real-time based on material/quantity selection
- [ ] Stripe payment processing works smoothly
- [ ] Orders are automatically created in Zoho CRM/Inventory
- [ ] Supplier emails are sent with order details
- [ ] System handles HP MJF printer constraints (bounding box limits)
- [ ] Minimum order value ($20 USD) is enforced
- [ ] NZ shipping costs calculated based on size

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://docs.stripe.com/api
  why: Payment processing, webhooks, and order management
  critical: Authentication patterns and payment intent creation
  
- url: https://medium.com/@chodvadiyasaurabh/integrating-stripe-payment-gateway-with-fastapi-a-comprehensive-guide-8fe4540b5a4
  why: FastAPI + Stripe integration patterns for 2024
  critical: Modern implementation examples and best practices
  
- url: https://www.zoho.com/developer/rest-api.html
  why: Zoho CRM/Inventory API integration patterns
  critical: OAuth 2.0 authentication and contact/sales order creation
  
- url: https://medium.com/@sherangaofc/ingesting-zoho-crm-data-using-api-in-python-b084bb093e01
  why: Current Python implementation patterns for Zoho CRM API
  critical: Token management and data ingestion approaches
  
- url: https://pypi.org/project/numpy-stl/
  why: STL file processing with volume and bounding box calculations
  critical: get_mass_properties() method for volume calculation
  
- url: https://github.com/mikedh/trimesh
  why: Alternative STL processing library with comprehensive mesh analysis
  critical: Volume calculation and watertightness checking
  
- file: /Users/hackerhall/projects/3d-quotes/CLAUDE.md
  why: Project conventions and architecture patterns
  critical: FastAPI backend, React frontend, testing requirements
  
- file: /Users/hackerhall/projects/3d-quotes/PRPs/templates/prp_base.md
  why: PRP template structure and validation patterns
  critical: Implementation blueprint and validation loops
```

### Current Codebase tree
```bash
/Users/hackerhall/projects/3d-quotes/
├── CLAUDE.md
├── INITIAL.md
├── LICENSE
├── PLANNING.md (empty)
├── PRPs/
│   ├── EXAMPLE_multi_agent_prp.md
│   └── templates/
│       └── prp_base.md
├── README-template.md
├── README.md (empty)
├── TASK.md (empty)
├── backend/
│   └── __init__.py
├── examples/
├── frontend/
│   └── index.html (empty)
```

### Desired Codebase tree with files to be added and responsibility of file
```bash
/Users/hackerhall/projects/3d-quotes/
├── backend/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry point
│   ├── requirements.txt             # Python dependencies
│   ├── .env.example                 # Environment variables template
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py              # Application configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── quote.py                 # Quote data models
│   │   ├── order.py                 # Order data models
│   │   └── customer.py              # Customer data models
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── quote.py                 # Pydantic schemas for API
│   │   ├── order.py                 # Order request/response schemas
│   │   └── customer.py              # Customer data schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── stl_processor.py         # STL file processing and validation
│   │   ├── pricing_calculator.py    # Pricing logic and calculations
│   │   ├── stripe_service.py        # Stripe payment integration
│   │   ├── zoho_service.py          # Zoho CRM/Inventory integration
│   │   └── email_service.py         # Supplier email notifications
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── quote.py                 # Quote endpoints
│   │   ├── payment.py               # Payment processing endpoints
│   │   └── order.py                 # Order management endpoints
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py            # Input validation utilities
│   │   └── helpers.py               # Common helper functions
│   └── tests/
│       ├── __init__.py
│       ├── test_stl_processor.py    # STL processing tests
│       ├── test_pricing.py          # Pricing calculation tests
│       ├── test_stripe.py           # Stripe integration tests
│       └── test_zoho.py             # Zoho integration tests
├── frontend/
│   ├── package.json                 # Node.js dependencies
│   ├── src/
│   │   ├── App.jsx                  # Main React application
│   │   ├── components/
│   │   │   ├── FileUpload.jsx       # STL file upload component
│   │   │   ├── MaterialSelector.jsx # Material selection component
│   │   │   ├── QuoteDisplay.jsx     # Quote display component
│   │   │   ├── PaymentForm.jsx      # Stripe payment form
│   │   │   └── OrderConfirmation.jsx # Order confirmation page
│   │   ├── hooks/
│   │   │   ├── useFileUpload.js     # File upload logic
│   │   │   └── useStripe.js         # Stripe payment logic
│   │   ├── utils/
│   │   │   ├── api.js               # API client utilities
│   │   │   └── validators.js        # Frontend validation
│   │   └── styles/
│   │       └── globals.css          # Global styles (shadcn/ui)
│   └── public/
│       └── index.html               # HTML template
├── data/                            # Local data storage
│   └── temp_uploads/                # Temporary STL file storage
├── docker-compose.yml               # Container orchestration
├── Dockerfile                       # Container definition
└── README.md                        # Setup and usage instructions
```

### Known Gotchas of our codebase & Library Quirks
```python
# CRITICAL: STL file processing
# numpy-stl: Use get_mass_properties() for volume calculation
# trimesh: Check mesh.is_watertight before volume calculation
# Both libraries require proper file validation before processing

# CRITICAL: Stripe payments
# Use payment intents, not charges (deprecated)
# Webhook verification is essential for security
# Test mode requires different API keys

# CRITICAL: Zoho API
# Access tokens expire every hour - implement refresh token logic
# Rate limiting: Be careful with API call frequency
# OAuth 2.0 setup required before any API calls

# CRITICAL: FastAPI + async
# Use async/await for all I/O operations
# File upload requires proper streaming handling
# CORS setup needed for frontend integration

# CRITICAL: File handling
# STL files should be deleted after processing
# Implement proper file size limits
# Validate file format before processing
```

## Implementation Blueprint

### Data models and structure

Create the core data models to ensure type safety and consistency.
```python
# Pydantic models for API validation
class STLFile(BaseModel):
    filename: str
    volume: float
    bounding_box: BoundingBox
    material: MaterialType
    quantity: int

class Quote(BaseModel):
    files: List[STLFile]
    subtotal: float
    shipping_cost: float
    total: float
    order_id: str

class Order(BaseModel):
    quote: Quote
    customer: CustomerInfo
    payment_intent_id: str
    status: OrderStatus
    created_at: datetime
```

### List of tasks to be completed to fulfill the PRP in the order they should be completed

```yaml
Task 1: Setup Project Structure and Dependencies
CREATE backend/requirements.txt:
  - FastAPI framework and async support
  - numpy-stl for STL processing
  - stripe for payment processing
  - requests for Zoho API calls
  - pydantic for data validation
  - python-dotenv for environment variables

CREATE backend/.env.example:
  - STRIPE_SECRET_KEY=sk_test_...
  - STRIPE_PUBLISHABLE_KEY=pk_test_...
  - ZOHO_CLIENT_ID=your_client_id
  - ZOHO_CLIENT_SECRET=your_client_secret
  - ZOHO_REFRESH_TOKEN=your_refresh_token
  - SMTP_HOST=smtp.gmail.com
  - SMTP_PORT=587
  - SMTP_USERNAME=your_email
  - SMTP_PASSWORD=your_password

CREATE frontend/package.json:
  - React 18+ with TypeScript
  - @stripe/stripe-js for payments
  - axios for API calls
  - tailwindcss and shadcn/ui for styling

Task 2: STL File Processing Service
CREATE backend/services/stl_processor.py:
  - IMPLEMENT file validation and integrity checks
  - IMPLEMENT volume calculation using numpy-stl
  - IMPLEMENT bounding box calculation
  - IMPLEMENT HP MJF printer constraint validation
  - HANDLE file cleanup after processing

Task 3: Pricing Calculator Service
CREATE backend/services/pricing_calculator.py:
  - IMPLEMENT material rate calculations (PA12 Grey, PA12 Black, PA12 GB)
  - IMPLEMENT quantity-based pricing
  - IMPLEMENT shipping cost calculation (S/M/L based on size)
  - IMPLEMENT minimum order validation ($20 USD)
  - IMPLEMENT markup calculations

Task 4: FastAPI Backend Core
CREATE backend/main.py:
  - SETUP FastAPI application with CORS
  - INCLUDE routers for quote, payment, and order endpoints
  - CONFIGURE middleware for file uploads
  - SETUP error handling and logging

CREATE backend/routers/quote.py:
  - IMPLEMENT file upload endpoint with validation
  - IMPLEMENT quote calculation endpoint
  - IMPLEMENT quote retrieval endpoint
  - HANDLE multiple file uploads simultaneously

Task 5: Stripe Payment Integration
CREATE backend/services/stripe_service.py:
  - IMPLEMENT payment intent creation
  - IMPLEMENT payment confirmation handling
  - IMPLEMENT webhook endpoint for payment status
  - HANDLE payment errors and edge cases

CREATE backend/routers/payment.py:
  - IMPLEMENT payment intent endpoint
  - IMPLEMENT payment confirmation endpoint
  - IMPLEMENT webhook handling endpoint
  - VALIDATE payment amounts match quotes

Task 6: Zoho CRM/Inventory Integration
CREATE backend/services/zoho_service.py:
  - IMPLEMENT OAuth 2.0 authentication flow
  - IMPLEMENT contact creation/update in CRM
  - IMPLEMENT sales order creation in Inventory
  - IMPLEMENT contact tagging ("Instant Quote Customer")
  - HANDLE token refresh automatically

Task 7: Email Service for Supplier Notifications
CREATE backend/services/email_service.py:
  - IMPLEMENT email composition with order details
  - IMPLEMENT STL file attachment handling
  - IMPLEMENT SMTP configuration and sending
  - HANDLE email delivery failures gracefully

Task 8: React Frontend Development
CREATE frontend/src/components/FileUpload.jsx:
  - IMPLEMENT drag-and-drop STL file upload
  - IMPLEMENT file validation on frontend
  - IMPLEMENT upload progress indicators
  - HANDLE multiple file selection

CREATE frontend/src/components/MaterialSelector.jsx:
  - IMPLEMENT material dropdown per file
  - IMPLEMENT quantity input per file
  - IMPLEMENT real-time price updates
  - VALIDATE user input constraints

CREATE frontend/src/components/QuoteDisplay.jsx:
  - IMPLEMENT quote summary display
  - IMPLEMENT itemized pricing breakdown
  - IMPLEMENT shipping cost display
  - IMPLEMENT minimum order warnings

CREATE frontend/src/components/PaymentForm.jsx:
  - IMPLEMENT Stripe Elements integration
  - IMPLEMENT customer information collection
  - IMPLEMENT payment processing flow
  - HANDLE payment errors and success states

Task 9: Testing Implementation
CREATE backend/tests/test_stl_processor.py:
  - TEST volume calculation accuracy
  - TEST bounding box validation
  - TEST file integrity checks
  - TEST error handling for invalid files

CREATE backend/tests/test_pricing.py:
  - TEST material rate calculations
  - TEST quantity-based pricing
  - TEST shipping cost calculations
  - TEST minimum order validation

CREATE backend/tests/test_stripe.py:
  - TEST payment intent creation
  - TEST webhook handling
  - TEST payment confirmation
  - TEST error scenarios

CREATE backend/tests/test_zoho.py:
  - TEST contact creation
  - TEST sales order creation
  - TEST token refresh handling
  - TEST API error handling

Task 10: Documentation and Deployment Setup
CREATE README.md:
  - INCLUDE setup instructions
  - INCLUDE API documentation
  - INCLUDE environment configuration
  - INCLUDE testing procedures

CREATE docker-compose.yml:
  - CONFIGURE backend and frontend containers
  - SETUP volume mounts for temp files
  - CONFIGURE environment variables
  - SETUP database if needed

Task 11: Final Integration and Testing
INTEGRATE all components:
  - TEST end-to-end workflow
  - TEST payment processing
  - TEST Zoho integration
  - TEST email notifications
  - VALIDATE all business rules
```

### Per task pseudocode as needed added to each task

```python
# Task 2: STL File Processing Service
async def process_stl_file(file_path: str) -> STLFileData:
    # PATTERN: Always validate file format first
    if not file_path.endswith('.stl'):
        raise ValidationError("Invalid file format")
    
    # CRITICAL: numpy-stl requires proper mesh loading
    try:
        mesh = stl.mesh.Mesh.from_file(file_path)
        volume, center_of_gravity, inertia = mesh.get_mass_properties()
    except Exception as e:
        raise ProcessingError(f"STL processing failed: {e}")
    
    # GOTCHA: Volume calculation can be negative for inverted meshes
    volume = abs(volume)
    
    # PATTERN: Calculate bounding box from mesh vectors
    bounding_box = {
        'min': mesh.min_,
        'max': mesh.max_,
        'dimensions': mesh.max_ - mesh.min_
    }
    
    # CRITICAL: Validate HP MJF printer constraints
    if any(dim > HP_MJF_MAX_DIMENSION for dim in bounding_box['dimensions']):
        raise ValidationError("File exceeds printer build volume")
    
    return STLFileData(
        volume=volume,
        bounding_box=bounding_box,
        is_valid=True
    )

# Task 5: Stripe Payment Integration
async def create_payment_intent(amount: int, currency: str = "usd") -> PaymentIntent:
    # PATTERN: Use payment intents, not charges
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,  # Amount in cents
            currency=currency,
            metadata={'order_id': generate_order_id()}
        )
        return intent
    except stripe.error.StripeError as e:
        # PATTERN: Handle Stripe errors gracefully
        raise PaymentError(f"Payment processing failed: {e}")

# Task 6: Zoho CRM Integration
async def create_zoho_contact(customer_data: CustomerInfo) -> str:
    # CRITICAL: Token refresh logic
    if is_token_expired():
        await refresh_zoho_token()
    
    # PATTERN: Zoho API requires specific data format
    contact_data = {
        'First_Name': customer_data.first_name,
        'Last_Name': customer_data.last_name,
        'Email': customer_data.email,
        'Tag': ['Instant Quote Customer']
    }
    
    # GOTCHA: Zoho API has rate limiting
    async with rate_limiter.acquire():
        response = await zoho_api_call('POST', '/contacts', contact_data)
    
    return response['data'][0]['details']['id']
```

### Integration Points
```yaml
FILE_STORAGE:
  - path: "data/temp_uploads/"
  - cleanup: "Delete files after processing"
  - validation: "File size limits and format checking"
  
ENVIRONMENT_VARS:
  - add to: backend/.env
  - pattern: "STRIPE_SECRET_KEY=sk_test_..."
  - pattern: "ZOHO_CLIENT_ID=your_client_id"
  - pattern: "SMTP_HOST=smtp.gmail.com"
  
CORS_SETUP:
  - add to: backend/main.py
  - pattern: "app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:3000'])"
  
ROUTING:
  - add to: backend/main.py
  - pattern: "app.include_router(quote_router, prefix='/api/quote')"
  - pattern: "app.include_router(payment_router, prefix='/api/payment')"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
cd backend && uv run ruff check . --fix
cd backend && uv run mypy .
cd frontend && npm run lint

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests
```python
# CREATE comprehensive test suite
def test_stl_volume_calculation():
    """Test STL file volume calculation accuracy"""
    test_file = "tests/fixtures/test_cube.stl"
    result = process_stl_file(test_file)
    assert abs(result.volume - 1000.0) < 0.1  # 10x10x10 cube

def test_pricing_calculation():
    """Test pricing logic with different materials"""
    quote_data = QuoteData(
        files=[STLFile(volume=1000, material="PA12_GREY", quantity=2)],
        shipping_size="M"
    )
    price = calculate_total_price(quote_data)
    assert price.total >= 20.0  # Minimum order

def test_stripe_payment_intent():
    """Test payment intent creation"""
    intent = create_payment_intent(2000)  # $20.00
    assert intent.amount == 2000
    assert intent.currency == "usd"

def test_zoho_contact_creation():
    """Test Zoho contact creation"""
    customer = CustomerInfo(
        first_name="John",
        last_name="Doe",
        email="john@example.com"
    )
    contact_id = create_zoho_contact(customer)
    assert contact_id is not None
```

```bash
# Run and iterate until passing:
cd backend && uv run pytest tests/ -v
cd frontend && npm test

# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Test
```bash
# Start the backend service
cd backend && uv run python -m main

# Start the frontend service
cd frontend && npm start

# Test file upload and quote generation
curl -X POST http://localhost:8000/api/quote/upload \
  -F "files=@test_cube.stl" \
  -F "material=PA12_GREY" \
  -F "quantity=1"

# Expected: {"quote_id": "...", "total": 20.00, "files": [...]}

# Test payment intent creation
curl -X POST http://localhost:8000/api/payment/create-intent \
  -H "Content-Type: application/json" \
  -d '{"quote_id": "...", "customer": {...}}'

# Expected: {"client_secret": "pi_...", "amount": 2000}
```

## Final validation Checklist
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `uv run ruff check backend/`
- [ ] No type errors: `uv run mypy backend/`
- [ ] Frontend builds successfully: `npm run build`
- [ ] STL file upload and processing works
- [ ] Pricing calculations are accurate
- [ ] Stripe payment processing works
- [ ] Zoho CRM integration creates contacts
- [ ] Zoho Inventory integration creates sales orders
- [ ] Supplier emails are sent correctly
- [ ] File cleanup happens after processing
- [ ] Error cases handled gracefully
- [ ] Documentation is complete and accurate

---

## Anti-Patterns to Avoid
- ❌ Don't process STL files synchronously - use async processing
- ❌ Don't store payment details locally - use Stripe's secure vault
- ❌ Don't hardcode pricing - make it configurable
- ❌ Don't ignore file size limits - validate before processing
- ❌ Don't skip Zoho token refresh - implement automatic refresh
- ❌ Don't forget to clean up uploaded files - implement automatic cleanup
- ❌ Don't use deprecated Stripe Charges API - use Payment Intents
- ❌ Don't skip webhook signature validation - critical for security

## PRP Quality Score: 9/10

This PRP provides comprehensive context, detailed implementation steps, and executable validation patterns. The high score reflects:
- Complete API documentation references
- Detailed library usage patterns with gotchas
- Step-by-step implementation blueprint
- Comprehensive testing strategy
- Clear validation loops with executable commands
- Real-world integration patterns

The minor point deduction is due to the complexity of the multi-system integration (Stripe + Zoho + STL processing), which may require some iterative refinement during implementation.