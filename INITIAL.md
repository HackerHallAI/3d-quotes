## FEATURE:

Description:
3D Hub Limited is looking for an experienced full-stack developer to build a web-based quoting tool for instant 3D printing estimates. This customer-facing tool will allow users to upload .STL files, select material and quantity, view a live quote, and complete payment via Stripe. After payment, the order data should trigger emails to our supplier and create a sales order in Zoho One (CRM & Inventory).

The ideal developer is fluent in React/Node.js or Python, has experience with 3D file processing (STL), and is familiar with Zoho REST APIs and Stripe integration.

💼 Scope of Work
Core Features:

STL Upload Interface

Multiple file uploads with integrity checks

Volume and bounding box auto-calculation

Bounding box limits based on HP MJF printer

Files deleted after processing

Material & Quantity Selection

Drop-down per file: PA12 Grey, PA12 Black, PA12 GB

Quantity input per part

Instant quote per part and total order

Pricing Logic

Volume × Material Rate × Quantity + shipping & markup

Minimum order: USD $20

NZ local courier shipping based on size (S/M/L)

Checkout & Stripe Payment

Full upfront payment

Order confirmation screen with unique Order ID

Supplier Notification

Email sent post-payment with STL, material, quantity & Order ID

Zoho One Integration

Sales Order in Zoho Inventory

Create/update contact in Zoho CRM

Tag contact as "Instant Quote Customer"

Order status tracking: Quote → Paid → Supplier Sent → Delivered → Shipped

Customer Details Collection

Before payment: collect name, email, shipping address

🛠️ Optional Features (Phase 2 / Upsell)
Admin Dashboard (view/edit orders, change pricing/materials)

Packaging/labeling upgrades

Certificate of Conformance option

Priority customer signup (with 5% discount)

📦 Deliverables
Hosted application with a shareable URL (for embedding in website/emails/ads)

Stripe-integrated, mobile-friendly quote and checkout flow

Automated supplier email + Zoho CRM/Inventory sync

Internal-use documentation

🔧 Suggested Tech Stack
Frontend: React / HTML/CSS/JS

Backend: Node.js or Python (Flask/Django)

3D File Processing: trimesh, meshio, or similar

Payment: Stripe API

CRM/Inventory: Zoho One via REST API

Storage: Temporary/auto-delete setup for uploaded files

✅ You’ll Succeed If You:
Have built quoting or file-processing tools before

Know how to work with 3D file formats (STL)

Are confident with API integrations (especially Zoho and Stripe)

Deliver clean, user-friendly interfaces and reliable backend logic

Timeline:
We are ready to start immediately. Please include an estimated timeline in your proposal.

Budget:
Open to fixed-price or milestone-based offers. Please include examples of past relevant work.

🔗 To Apply:
Please include:

A short description of your experience with file uploads or quoting tools

Any prior Zoho or Stripe integration examples

Suggested tech stack

Estimated timeframe and cost

Looking forward to working with a talented developer who can help us streamline how our customers place 3D printing orders online!

## DOCUMENTATION:

- Stripe API (https://docs.stripe.com/api)
- ZOHO API (https://www.zoho.com/commerce/api/introduction.html)
    - backup (https://www.zoho.com/developer/rest-api.html)

## OTHER CONSIDERATIONS:
- Include a .env.example, README with instructions for setup including how to configure Gmail and Brave.
- Include the project structure in the README.
- Instead of NextJS make sure to follow requirements and create with react. 
    - Should use schadui if possible.


