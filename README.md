# 3D Printing Quote Tool

A comprehensive web-based application for generating instant quotes for 3D printing services using HP Multi Jet Fusion technology.

## Features

- **STL File Upload**: Drag-and-drop interface for uploading multiple STL files
- **Real-time Quote Generation**: Instant pricing based on volume, material, and quantity
- **Material Selection**: Support for multiple materials (PA12, PA12 Glass Filled)
- **Secure Payments**: Stripe integration for payment processing
- **Order Management**: Complete order tracking and confirmation
- **CRM Integration**: Zoho CRM integration for customer and order management
- **Email Notifications**: Automated notifications for suppliers and customers

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **numpy-stl**: STL file processing and analysis
- **Stripe**: Payment processing
- **Pydantic**: Data validation and serialization
- **HTTPX**: Async HTTP client for external API calls

### Frontend
- **React 18+**: Modern React with hooks
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **Stripe Elements**: Secure payment forms
- **Axios**: HTTP client for API communication

## Project Structure

```
3d-quotes/
├── backend/
│   ├── main.py                    # FastAPI application entry point
│   ├── requirements.txt           # Python dependencies
│   ├── requirements-test.txt      # Testing dependencies
│   ├── .env.example              # Environment variables template
│   ├── models/                   # Pydantic data models
│   │   ├── __init__.py
│   │   ├── stl_file.py
│   │   ├── quote.py
│   │   ├── order.py
│   │   └── customer.py
│   ├── services/                 # Business logic services
│   │   ├── __init__.py
│   │   ├── stl_processor.py      # STL file analysis
│   │   ├── pricing_calculator.py # Pricing logic
│   │   ├── stripe_service.py     # Payment processing
│   │   ├── zoho_service.py       # CRM integration
│   │   └── email_service.py      # Email notifications
│   ├── routers/                  # API endpoints
│   │   ├── __init__.py
│   │   ├── quote.py
│   │   └── payment.py
│   └── tests/                    # Test suite
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_stl_processor.py
│       ├── test_pricing_calculator.py
│       └── test_stripe_service.py
├── frontend/
│   ├── package.json              # Node.js dependencies
│   ├── tsconfig.json             # TypeScript configuration
│   ├── tailwind.config.js        # Tailwind CSS configuration
│   ├── vite.config.ts            # Vite build configuration
│   └── src/
│       ├── App.tsx               # Main application component
│       ├── main.tsx              # Application entry point
│       ├── index.css             # Global styles
│       ├── components/           # React components
│       │   ├── FileUpload.tsx
│       │   ├── MaterialSelector.tsx
│       │   ├── QuoteDisplay.tsx
│       │   ├── PaymentForm.tsx
│       │   └── OrderConfirmation.tsx
│       ├── hooks/                # Custom React hooks
│       │   ├── useFileUpload.ts
│       │   └── useStripe.ts
│       └── utils/                # Utility functions
│           ├── api.ts            # API client
│           └── validators.ts     # Validation functions
├── data/
│   └── temp_uploads/             # Temporary file storage
└── docs/
    └── api.md                    # API documentation
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 18+
- npm or yarn
- Stripe account (for payments)
- Zoho account (for CRM integration)
- SMTP server (for email notifications)

### Backend Setup

1. **Clone the repository and navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt  # For development
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

   Required environment variables:
   ```env
   # Stripe Configuration
   STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
   STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

   # Zoho CRM Configuration
   ZOHO_CLIENT_ID=your_zoho_client_id
   ZOHO_CLIENT_SECRET=your_zoho_client_secret
   ZOHO_REFRESH_TOKEN=your_zoho_refresh_token
   ZOHO_CRM_DOMAIN=crm.zoho.com

   # Email Configuration
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   SUPPLIER_EMAIL=supplier@yourcompany.com

   # Application Settings
   UPLOAD_DIR=../data/temp_uploads
   MAX_FILE_SIZE=52428800
   ```

5. **Create upload directory:**
   ```bash
   mkdir -p ../data/temp_uploads
   ```

6. **Run the development server:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment variables:**
   ```bash
   # Create .env.local file
   echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local
   ```

4. **Run the development server:**
   ```bash
   npm run dev
   ```

5. **Build for production:**
   ```bash
   npm run build
   ```

## API Documentation

### Quote Endpoints

#### Generate Quote
```http
POST /api/quotes/generate
Content-Type: multipart/form-data

files: [File, File, ...]  # STL files
file_0_material: string   # Material type for first file
file_0_quantity: integer  # Quantity for first file
customer_email: string    # Customer email (optional)
```

#### Get Quote
```http
GET /api/quotes/{quote_id}
```

### Payment Endpoints

#### Create Payment Intent
```http
POST /api/payments/create-intent
Content-Type: application/json

{
  "quote_id": "string",
  "customer_email": "string"
}
```

#### Confirm Payment
```http
POST /api/payments/confirm
Content-Type: application/json

{
  "payment_intent_id": "string",
  "order_id": "string"
}
```

#### Stripe Webhook
```http
POST /api/payments/webhook
Content-Type: application/json
Stripe-Signature: [signature]

[Stripe event payload]
```

### Configuration Endpoints

#### Get Material Config
```http
GET /api/quotes/materials
```

#### Get Payment Config
```http
GET /api/payments/config
```

## Testing

### Backend Tests

Run the test suite:
```bash
cd backend
pytest
```

Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

Run specific test files:
```bash
pytest tests/test_stl_processor.py
pytest tests/test_pricing_calculator.py
pytest tests/test_stripe_service.py
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Deployment

### Using Docker

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Deployment

1. **Backend Production Setup:**
   ```bash
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Frontend Production Build:**
   ```bash
   npm run build
   # Serve the dist/ directory with a web server
   ```

## Configuration

### Material Pricing

Configure material rates in `backend/services/pricing_calculator.py`:

```python
MATERIAL_RATES = {
    "pa12": 2.50,      # $2.50 per cm³
    "pa12_gf": 3.75,   # $3.75 per cm³
}
```

### Shipping Costs

Configure shipping rates in `backend/services/pricing_calculator.py`:

```python
SHIPPING_RATES = {
    "small": 15.00,
    "medium": 25.00,
    "large": 35.00,
    "oversized": 50.00,
}
```

### HP Multi Jet Fusion Constraints

Build volume constraints in `backend/services/stl_processor.py`:

```python
# HP MJF Build Volume (mm)
MAX_BUILD_SIZE = {
    "x": 380,  # mm
    "y": 284,  # mm  
    "z": 380   # mm
}
```

## Troubleshooting

### Common Issues

1. **STL File Processing Errors:**
   - Ensure STL files are valid and watertight
   - Check file size limits (50MB max)
   - Verify numpy-stl installation

2. **Payment Processing Issues:**
   - Verify Stripe keys are correct
   - Check webhook endpoint is accessible
   - Ensure HTTPS in production

3. **CRM Integration Problems:**
   - Verify Zoho OAuth tokens are valid
   - Check API rate limits
   - Ensure proper scopes are granted

4. **Email Delivery Issues:**
   - Check SMTP configuration
   - Verify app passwords for Gmail
   - Test firewall/network connectivity

### Development Tips

1. **Enable debug logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Test with curl:**
   ```bash
   curl -X POST "http://localhost:8000/api/quotes/materials"
   ```

3. **Monitor file uploads:**
   ```bash
   ls -la data/temp_uploads/
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Run the test suite
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For support and questions:
- Email: support@yourcompany.com
- Documentation: https://docs.yourcompany.com
- Issues: https://github.com/yourcompany/3d-quotes/issues