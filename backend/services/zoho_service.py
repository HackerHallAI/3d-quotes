"""
Zoho CRM/Inventory service for the 3D Quotes application.

This module handles OAuth 2.0 authentication, contact creation/update,
and sales order creation in Zoho CRM and Inventory systems.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import aiohttp

from config.settings import settings
from models.customer import CustomerInfo
from models.order import Order

logger = logging.getLogger(__name__)


class ZohoError(Exception):
    """
    Custom error for Zoho API operations.
    """
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class RateLimiter:
    """
    Simple rate limiter for API calls.
    """
    def __init__(self, max_calls: int = 100, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self.lock = asyncio.Lock()

    async def acquire(self):
        """
        Acquire permission to make an API call.
        """
        async with self.lock:
            now = datetime.utcnow()

            # Remove old calls outside time window
            self.calls = [call_time for call_time in self.calls
                         if now - call_time < timedelta(seconds=self.time_window)]

            # If we're at the limit, wait
            if len(self.calls) >= self.max_calls:
                oldest_call = min(self.calls)
                wait_time = (oldest_call + timedelta(seconds=self.time_window) - now).total_seconds()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

            # Record this call
            self.calls.append(now)


class ZohoService:
    """
    Service for handling Zoho CRM and Inventory operations.
    """

    def __init__(self):
        self.client_id = settings.zoho_client_id
        self.client_secret = settings.zoho_client_secret
        self.refresh_token = settings.zoho_refresh_token
        self.accounts_url = settings.zoho_accounts_url
        self.crm_url = settings.zoho_crm_url
        self.inventory_url = settings.zoho_inventory_url

        # Token management
        self.access_token = None
        self.token_expires_at = None

        # Rate limiter
        self.rate_limiter = RateLimiter(max_calls=100, time_window=60)

    async def _refresh_access_token(self) -> str:
        """
        Refresh the access token using refresh token.
        
        Returns:
            str: New access token
            
        Raises:
            ZohoError: If token refresh fails
        """
        try:
            url = f"{self.accounts_url}/oauth/v2/token"

            data = {
                'refresh_token': self.refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()

                        self.access_token = token_data['access_token']
                        expires_in = token_data.get('expires_in', 3600)  # Default 1 hour
                        self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 300)  # 5 min buffer

                        logger.info("Successfully refreshed Zoho access token")
                        return self.access_token
                    else:
                        error_data = await response.json()
                        raise ZohoError(f"Token refresh failed: {error_data.get('error', 'Unknown error')}", response.status)

        except Exception as e:
            logger.error(f"Error refreshing Zoho token: {e}")
            raise ZohoError(f"Token refresh failed: {str(e)}")

    async def _get_valid_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            str: Valid access token
        """
        # CRITICAL: Token refresh logic
        if (self.access_token is None or
            self.token_expires_at is None or
            datetime.utcnow() >= self.token_expires_at):
            await self._refresh_access_token()

        return self.access_token

    async def _make_api_call(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated API call to Zoho.
        
        Args:
            method: HTTP method
            url: API endpoint URL
            data: Request data
            headers: Additional headers
            
        Returns:
            dict: API response data
            
        Raises:
            ZohoError: If API call fails
        """
        # GOTCHA: Zoho API has rate limiting
        await self.rate_limiter.acquire()

        # Get valid token
        token = await self._get_valid_token()

        # Prepare headers
        api_headers = {
            'Authorization': f'Zoho-oauthtoken {token}',
            'Content-Type': 'application/json'
        }

        if headers:
            api_headers.update(headers)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    json=data,
                    headers=api_headers
                ) as response:
                    response_data = await response.json()

                    if response.status == 200:
                        return response_data
                    elif response.status == 401:
                        # Token might be expired, try refreshing once
                        await self._refresh_access_token()
                        api_headers['Authorization'] = f'Zoho-oauthtoken {self.access_token}'

                        # Retry the request
                        async with session.request(
                            method,
                            url,
                            json=data,
                            headers=api_headers
                        ) as retry_response:
                            retry_data = await retry_response.json()

                            if retry_response.status == 200:
                                return retry_data
                            else:
                                raise ZohoError(f"API call failed after retry: {retry_data}", retry_response.status)
                    else:
                        raise ZohoError(f"API call failed: {response_data}", response.status)

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error making Zoho API call: {e}")
            raise ZohoError(f"HTTP error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error making Zoho API call: {e}")
            raise ZohoError(f"Unexpected error: {str(e)}")

    async def create_contact(self, customer_info: CustomerInfo) -> str:
        """
        Create a contact in Zoho CRM.
        
        Args:
            customer_info: Customer information
            
        Returns:
            str: Created contact ID
            
        Raises:
            ZohoError: If contact creation fails
        """
        # PATTERN: Zoho API requires specific data format
        contact_data = {
            'data': [
                {
                    'First_Name': customer_info.first_name,
                    'Last_Name': customer_info.last_name,
                    'Email': customer_info.email,
                    'Phone': customer_info.phone,
                    'Account_Name': customer_info.company,
                    'Mailing_Street': customer_info.address_line1,
                    'Mailing_City': customer_info.city,
                    'Mailing_State': customer_info.state,
                    'Mailing_Code': customer_info.postal_code,
                    'Mailing_Country': customer_info.country,
                    'Tag': [{'name': 'Instant Quote Customer'}],
                    'Lead_Source': '3D Quotes Tool'
                }
            ]
        }

        # Remove None values
        contact_record = {k: v for k, v in contact_data['data'][0].items() if v is not None}
        contact_data['data'][0] = contact_record

        url = f"{self.crm_url}/Contacts"

        try:
            response = await self._make_api_call('POST', url, contact_data)

            if response.get('data') and len(response['data']) > 0:
                contact_id = response['data'][0]['details']['id']
                logger.info(f"Created Zoho contact: {contact_id} for {customer_info.email}")
                return contact_id
            else:
                raise ZohoError(f"Unexpected response format: {response}")

        except ZohoError:
            raise
        except Exception as e:
            logger.error(f"Error creating Zoho contact: {e}")
            raise ZohoError(f"Contact creation failed: {str(e)}")

    async def update_contact(self, contact_id: str, customer_info: CustomerInfo) -> bool:
        """
        Update a contact in Zoho CRM.
        
        Args:
            contact_id: Contact ID to update
            customer_info: Updated customer information
            
        Returns:
            bool: True if update successful
            
        Raises:
            ZohoError: If contact update fails
        """
        contact_data = {
            'data': [
                {
                    'id': contact_id,
                    'First_Name': customer_info.first_name,
                    'Last_Name': customer_info.last_name,
                    'Email': customer_info.email,
                    'Phone': customer_info.phone,
                    'Account_Name': customer_info.company,
                    'Mailing_Street': customer_info.address_line1,
                    'Mailing_City': customer_info.city,
                    'Mailing_State': customer_info.state,
                    'Mailing_Code': customer_info.postal_code,
                    'Mailing_Country': customer_info.country
                }
            ]
        }

        # Remove None values
        contact_record = {k: v for k, v in contact_data['data'][0].items() if v is not None}
        contact_data['data'][0] = contact_record

        url = f"{self.crm_url}/Contacts"

        try:
            response = await self._make_api_call('PUT', url, contact_data)

            if response.get('data') and len(response['data']) > 0:
                logger.info(f"Updated Zoho contact: {contact_id}")
                return True
            else:
                raise ZohoError(f"Unexpected response format: {response}")

        except ZohoError:
            raise
        except Exception as e:
            logger.error(f"Error updating Zoho contact: {e}")
            raise ZohoError(f"Contact update failed: {str(e)}")

    async def search_contact_by_email(self, email: str) -> Optional[str]:
        """
        Search for a contact by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            Optional[str]: Contact ID if found, None otherwise
        """
        try:
            url = f"{self.crm_url}/Contacts/search"
            params = {'criteria': f'Email:equals:{email}'}

            # Add params to URL
            full_url = f"{url}?criteria={params['criteria']}"

            response = await self._make_api_call('GET', full_url)

            if response.get('data') and len(response['data']) > 0:
                contact_id = response['data'][0]['id']
                logger.info(f"Found existing contact: {contact_id} for {email}")
                return contact_id
            else:
                return None

        except ZohoError as e:
            # If it's a "no data found" error, return None
            if 'no data found' in e.message.lower():
                return None
            raise
        except Exception as e:
            logger.error(f"Error searching Zoho contact: {e}")
            return None

    async def create_sales_order(self, order: Order) -> str:
        """
        Create a sales order in Zoho Inventory.
        
        Args:
            order: Order information
            
        Returns:
            str: Created sales order ID
            
        Raises:
            ZohoError: If sales order creation fails
        """
        # Prepare line items
        line_items = []
        for file in order.quote.files:
            line_items.append({
                'name': file.filename,
                'description': f'{file.material.value} - {file.quantity} units',
                'quantity': file.quantity,
                'rate': file.unit_price,
                'unit': 'pcs'
            })

        # Add shipping as a line item
        if order.quote.shipping_cost > 0:
            line_items.append({
                'name': 'Shipping',
                'description': f'Shipping ({order.quote.shipping_size.value})',
                'quantity': 1,
                'rate': order.quote.shipping_cost,
                'unit': 'pcs'
            })

        sales_order_data = {
            'customer_name': f"{order.customer.first_name} {order.customer.last_name}",
            'customer_email': order.customer.email,
            'date': order.created_at.strftime('%Y-%m-%d'),
            'shipment_date': (order.created_at + timedelta(days=order.quote.estimated_shipping_days)).strftime('%Y-%m-%d'),
            'line_items': line_items,
            'notes': f'Order from 3D Quotes Tool - Order ID: {order.order_id}',
            'terms': 'Payment completed via Stripe',
            'billing_address': {
                'address': order.customer.address_line1,
                'city': order.customer.city,
                'state': order.customer.state,
                'zip': order.customer.postal_code,
                'country': order.customer.country
            },
            'shipping_address': {
                'address': order.customer.address_line1,
                'city': order.customer.city,
                'state': order.customer.state,
                'zip': order.customer.postal_code,
                'country': order.customer.country
            }
        }

        url = f"{self.inventory_url}/salesorders"

        try:
            response = await self._make_api_call('POST', url, sales_order_data)

            if response.get('salesorder'):
                sales_order_id = response['salesorder']['salesorder_id']
                logger.info(f"Created Zoho sales order: {sales_order_id} for order {order.order_id}")
                return sales_order_id
            else:
                raise ZohoError(f"Unexpected response format: {response}")

        except ZohoError:
            raise
        except Exception as e:
            logger.error(f"Error creating Zoho sales order: {e}")
            raise ZohoError(f"Sales order creation failed: {str(e)}")

    async def process_order(self, order: Order) -> Dict[str, str]:
        """
        Process an order by creating/updating contact and creating sales order.
        
        Args:
            order: Order to process
            
        Returns:
            dict: Created/updated contact ID and sales order ID
            
        Raises:
            ZohoError: If processing fails
        """
        try:
            # Search for existing contact
            contact_id = await self.search_contact_by_email(order.customer.email)

            if contact_id:
                # Update existing contact
                await self.update_contact(contact_id, order.customer)
            else:
                # Create new contact
                contact_id = await self.create_contact(order.customer)

            # Create sales order
            sales_order_id = await self.create_sales_order(order)

            logger.info(f"Processed order {order.order_id} in Zoho: Contact {contact_id}, Sales Order {sales_order_id}")

            return {
                'contact_id': contact_id,
                'sales_order_id': sales_order_id
            }

        except ZohoError:
            raise
        except Exception as e:
            logger.error(f"Error processing order in Zoho: {e}")
            raise ZohoError(f"Order processing failed: {str(e)}")

    async def get_contact_details(self, contact_id: str) -> Dict[str, Any]:
        """
        Get contact details by ID.
        
        Args:
            contact_id: Contact ID
            
        Returns:
            dict: Contact details
        """
        url = f"{self.crm_url}/Contacts/{contact_id}"

        try:
            response = await self._make_api_call('GET', url)

            if response.get('data') and len(response['data']) > 0:
                return response['data'][0]
            else:
                raise ZohoError(f"Contact not found: {contact_id}")

        except ZohoError:
            raise
        except Exception as e:
            logger.error(f"Error getting contact details: {e}")
            raise ZohoError(f"Failed to get contact details: {str(e)}")

    async def get_sales_order_details(self, sales_order_id: str) -> Dict[str, Any]:
        """
        Get sales order details by ID.
        
        Args:
            sales_order_id: Sales order ID
            
        Returns:
            dict: Sales order details
        """
        url = f"{self.inventory_url}/salesorders/{sales_order_id}"

        try:
            response = await self._make_api_call('GET', url)

            if response.get('salesorder'):
                return response['salesorder']
            else:
                raise ZohoError(f"Sales order not found: {sales_order_id}")

        except ZohoError:
            raise
        except Exception as e:
            logger.error(f"Error getting sales order details: {e}")
            raise ZohoError(f"Failed to get sales order details: {str(e)}")


# Global service instance
zoho_service = ZohoService()
