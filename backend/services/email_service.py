"""
Email service for the 3D Quotes application.

This module handles email composition, SMTP configuration, and sending
supplier notifications with order details and STL file attachments.
"""
import logging
import os
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import aiosmtplib

from config.settings import settings
from models.order import Order

logger = logging.getLogger(__name__)


class EmailError(Exception):
    """
    Custom error for email operations.
    """
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class EmailService:
    """
    Service for handling email operations.
    """

    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.smtp_tls = settings.smtp_tls
        self.supplier_email = settings.supplier_email
        self.from_email = settings.smtp_username

    async def send_supplier_notification(
        self,
        order: Order,
        stl_file_paths: List[str],
        special_instructions: Optional[str] = None
    ) -> bool:
        """
        Send supplier notification email with order details and STL files.
        
        Args:
            order: Order information
            stl_file_paths: List of STL file paths to attach
            special_instructions: Optional special instructions
            
        Returns:
            bool: True if email sent successfully
            
        Raises:
            EmailError: If email sending fails
        """
        try:
            # Create email message
            message = await self._create_supplier_notification_message(
                order, stl_file_paths, special_instructions
            )

            # Send email
            await self._send_email(message)

            logger.info(f"Sent supplier notification for order {order.order_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send supplier notification: {e}")
            raise EmailError(f"Failed to send supplier notification: {str(e)}", e)

    async def send_customer_confirmation(self, order: Order) -> bool:
        """
        Send customer order confirmation email.
        
        Args:
            order: Order information
            
        Returns:
            bool: True if email sent successfully
            
        Raises:
            EmailError: If email sending fails
        """
        try:
            # Create email message
            message = await self._create_customer_confirmation_message(order)

            # Send email
            await self._send_email(message)

            logger.info(f"Sent customer confirmation for order {order.order_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send customer confirmation: {e}")
            raise EmailError(f"Failed to send customer confirmation: {str(e)}", e)

    async def _create_supplier_notification_message(
        self,
        order: Order,
        stl_file_paths: List[str],
        special_instructions: Optional[str] = None
    ) -> MIMEMultipart:
        """
        Create supplier notification email message.
        
        Args:
            order: Order information
            stl_file_paths: List of STL file paths to attach
            special_instructions: Optional special instructions
            
        Returns:
            MIMEMultipart: Email message
        """
        # Create multipart message
        message = MIMEMultipart()
        message['From'] = self.from_email
        message['To'] = self.supplier_email
        message['Subject'] = f"New 3D Print Order - {order.order_id}"

        # Create email body
        body = self._create_supplier_email_body(order, special_instructions)
        message.attach(MIMEText(body, 'html'))

        # Attach STL files
        for file_path in stl_file_paths:
            if os.path.exists(file_path):
                await self._attach_file(message, file_path)
            else:
                logger.warning(f"STL file not found for attachment: {file_path}")

        return message

    async def _create_customer_confirmation_message(self, order: Order) -> MIMEMultipart:
        """
        Create customer confirmation email message.
        
        Args:
            order: Order information
            
        Returns:
            MIMEMultipart: Email message
        """
        # Create multipart message
        message = MIMEMultipart()
        message['From'] = self.from_email
        message['To'] = order.customer.email
        message['Subject'] = f"Order Confirmation - {order.order_id}"

        # Create email body
        body = self._create_customer_email_body(order)
        message.attach(MIMEText(body, 'html'))

        return message

    def _create_supplier_email_body(
        self,
        order: Order,
        special_instructions: Optional[str] = None
    ) -> str:
        """
        Create supplier email body content.
        
        Args:
            order: Order information
            special_instructions: Optional special instructions
            
        Returns:
            str: HTML email body
        """
        customer = order.customer
        quote = order.quote

        # Format file details
        file_details = ""
        for file in quote.files:
            file_details += f"""
            <tr>
                <td>{file.filename}</td>
                <td>{file.material.value}</td>
                <td>{file.quantity}</td>
                <td>{file.volume / 1000:.2f} cm³</td>
                <td>${file.unit_price:.2f}</td>
                <td>${file.total_price:.2f}</td>
            </tr>
            """

        special_instructions_html = ""
        if special_instructions:
            special_instructions_html = f"""
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #856404; margin-top: 0;">Special Instructions</h3>
                <p style="margin-bottom: 0;">{special_instructions}</p>
            </div>
            """

        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .order-details {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f8f9fa; }}
                .total {{ font-weight: bold; background-color: #e9ecef; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New 3D Print Order</h1>
                    <p>Order ID: {order.order_id}</p>
                </div>
                
                <div class="content">
                    <h2>Order Details</h2>
                    <div class="order-details">
                        <p><strong>Order Date:</strong> {order.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                        <p><strong>Payment Status:</strong> {order.payment_status.value}</p>
                        <p><strong>Total Amount:</strong> ${order.amount_paid:.2f}</p>
                    </div>
                    
                    <h2>Customer Information</h2>
                    <div class="order-details">
                        <p><strong>Name:</strong> {customer.first_name} {customer.last_name}</p>
                        <p><strong>Email:</strong> {customer.email}</p>
                        <p><strong>Phone:</strong> {customer.phone or 'Not provided'}</p>
                        <p><strong>Company:</strong> {customer.company or 'Not provided'}</p>
                    </div>
                    
                    <h2>Shipping Address</h2>
                    <div class="order-details">
                        <p>
                            {customer.address_line1}<br>
                            {customer.address_line2 + '<br>' if customer.address_line2 else ''}
                            {customer.city}, {customer.state or ''} {customer.postal_code}<br>
                            {customer.country}
                        </p>
                    </div>
                    
                    {special_instructions_html}
                    
                    <h2>File Details</h2>
                    <table>
                        <tr>
                            <th>Filename</th>
                            <th>Material</th>
                            <th>Quantity</th>
                            <th>Volume</th>
                            <th>Unit Price</th>
                            <th>Total Price</th>
                        </tr>
                        {file_details}
                        <tr class="total">
                            <td colspan="5">Subtotal</td>
                            <td>${quote.subtotal:.2f}</td>
                        </tr>
                        <tr class="total">
                            <td colspan="5">Shipping ({quote.shipping_size.value})</td>
                            <td>${quote.shipping_cost:.2f}</td>
                        </tr>
                        <tr class="total">
                            <td colspan="5">Total</td>
                            <td>${quote.total:.2f}</td>
                        </tr>
                    </table>
                    
                    <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="color: #155724; margin-top: 0;">Next Steps</h3>
                        <ul>
                            <li>STL files are attached to this email</li>
                            <li>Customer has paid in full via Stripe</li>
                            <li>Expected delivery: {quote.estimated_shipping_days} business days</li>
                            <li>Please confirm receipt and estimated completion time</li>
                        </ul>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        return body

    def _create_customer_email_body(self, order: Order) -> str:
        """
        Create customer confirmation email body content.
        
        Args:
            order: Order information
            
        Returns:
            str: HTML email body
        """
        customer = order.customer
        quote = order.quote

        # Format file details
        file_details = ""
        for file in quote.files:
            file_details += f"""
            <tr>
                <td>{file.filename}</td>
                <td>{file.material.value}</td>
                <td>{file.quantity}</td>
                <td>${file.total_price:.2f}</td>
            </tr>
            """

        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .order-details {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f8f9fa; }}
                .total {{ font-weight: bold; background-color: #e9ecef; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Order Confirmation</h1>
                    <p>Thank you for your order!</p>
                </div>
                
                <div class="content">
                    <p>Dear {customer.first_name},</p>
                    
                    <p>Your order has been successfully placed and payment has been processed. Here are the details:</p>
                    
                    <div class="order-details">
                        <p><strong>Order ID:</strong> {order.order_id}</p>
                        <p><strong>Order Date:</strong> {order.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                        <p><strong>Total Amount:</strong> ${order.amount_paid:.2f}</p>
                        <p><strong>Payment Status:</strong> Paid</p>
                    </div>
                    
                    <h2>Order Summary</h2>
                    <table>
                        <tr>
                            <th>File</th>
                            <th>Material</th>
                            <th>Quantity</th>
                            <th>Total</th>
                        </tr>
                        {file_details}
                        <tr class="total">
                            <td colspan="3">Subtotal</td>
                            <td>${quote.subtotal:.2f}</td>
                        </tr>
                        <tr class="total">
                            <td colspan="3">Shipping</td>
                            <td>${quote.shipping_cost:.2f}</td>
                        </tr>
                        <tr class="total">
                            <td colspan="3">Total</td>
                            <td>${quote.total:.2f}</td>
                        </tr>
                    </table>
                    
                    <div style="background-color: #d1ecf1; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="color: #0c5460; margin-top: 0;">What's Next?</h3>
                        <ul>
                            <li>Your order has been forwarded to our production team</li>
                            <li>Estimated delivery: {quote.estimated_shipping_days} business days</li>
                            <li>You will receive tracking information once your order ships</li>
                            <li>For questions, please contact us with your order ID: {order.order_id}</li>
                        </ul>
                    </div>
                    
                    <p>Thank you for choosing our 3D printing service!</p>
                    
                    <p>Best regards,<br>
                    The 3D Printing Team</p>
                </div>
            </div>
        </body>
        </html>
        """

        return body

    async def _attach_file(self, message: MIMEMultipart, file_path: str) -> None:
        """
        Attach a file to the email message.
        
        Args:
            message: Email message
            file_path: Path to file to attach
        """
        try:
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())

            encoders.encode_base64(part)

            filename = os.path.basename(file_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )

            message.attach(part)

        except Exception as e:
            logger.error(f"Failed to attach file {file_path}: {e}")
            raise EmailError(f"Failed to attach file: {str(e)}", e)

    async def _send_email(self, message: MIMEMultipart) -> None:
        """
        Send email using SMTP.
        
        Args:
            message: Email message to send
            
        Raises:
            EmailError: If email sending fails
        """
        try:
            # Create SMTP client
            smtp_client = aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=self.smtp_tls
            )

            # Connect and send
            await smtp_client.connect()
            await smtp_client.login(self.smtp_username, self.smtp_password)
            await smtp_client.send_message(message)
            await smtp_client.quit()

        except Exception as e:
            logger.error(f"SMTP error sending email: {e}")
            raise EmailError(f"SMTP error: {str(e)}", e)

    async def test_email_configuration(self) -> Dict[str, Any]:
        """
        Test email configuration by sending a test email.
        
        Returns:
            dict: Test result
        """
        try:
            # Create test message
            message = MIMEMultipart()
            message['From'] = self.from_email
            message['To'] = self.from_email  # Send to self
            message['Subject'] = "3D Quotes Email Configuration Test"

            body = f"""
            <html>
            <body>
                <h2>Email Configuration Test</h2>
                <p>This is a test email to verify the email configuration is working correctly.</p>
                <p>If you receive this email, the configuration is successful.</p>
                <p>Timestamp: {datetime.utcnow().isoformat()}</p>
            </body>
            </html>
            """

            message.attach(MIMEText(body, 'html'))

            # Send test email
            await self._send_email(message)

            return {
                "status": "success",
                "message": "Test email sent successfully",
                "timestamp": datetime.utcnow().isoformat()
            }

        except EmailError as e:
            return {
                "status": "error",
                "message": e.message,
                "timestamp": datetime.utcnow().isoformat()
            }

    def get_email_configuration(self) -> Dict[str, Any]:
        """
        Get email configuration (without sensitive data).
        
        Returns:
            dict: Email configuration
        """
        return {
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "smtp_tls": self.smtp_tls,
            "from_email": self.from_email,
            "supplier_email": self.supplier_email,
            "smtp_username_configured": bool(self.smtp_username),
            "smtp_password_configured": bool(self.smtp_password)
        }


# Global service instance
email_service = EmailService()
