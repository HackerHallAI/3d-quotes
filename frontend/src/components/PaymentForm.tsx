import React, { useState, useEffect } from 'react';
import { 
  Elements, 
  CardElement, 
  useElements, 
  useStripe 
} from '@stripe/react-stripe-js';
import { 
  CreditCard, 
  User, 
  MapPin, 
  Mail, 
  Phone, 
  Building, 
  Lock,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { useStripe as useStripeService } from '@/hooks/useStripe';
import { QuoteResponse, apiEndpoints, handleApiError } from '@/utils/api';
import { validateCustomerInfo, CustomerInfo } from '@/utils/validators';

interface PaymentFormProps {
  quote: QuoteResponse;
  onPaymentSuccess: (orderId: string) => void;
  onPaymentError: (error: string) => void;
  disabled?: boolean;
}

const PaymentForm: React.FC<PaymentFormProps> = ({
  quote,
  onPaymentSuccess,
  onPaymentError,
  disabled = false,
}) => {
  const { stripe: stripeService } = useStripeService();

  if (!stripeService) {
    return (
      <div className="quote-card">
        <div className="text-center py-8">
          <div className="loading-spinner mx-auto mb-4" />
          <p className="text-muted-foreground">Loading payment system...</p>
        </div>
      </div>
    );
  }

  return (
    <Elements stripe={stripeService}>
      <PaymentFormContent
        quote={quote}
        onPaymentSuccess={onPaymentSuccess}
        onPaymentError={onPaymentError}
        disabled={disabled}
      />
    </Elements>
  );
};

interface PaymentFormContentProps extends PaymentFormProps {}

const PaymentFormContent: React.FC<PaymentFormContentProps> = ({
  quote,
  onPaymentSuccess,
  onPaymentError,
  disabled = false,
}) => {
  const stripe = useStripe();
  const elements = useElements();
  
  const [isProcessing, setIsProcessing] = useState(false);
  const [customerInfo, setCustomerInfo] = useState<CustomerInfo>({
    firstName: '',
    lastName: '',
    email: quote.customer_email || '',
    phone: '',
    company: '',
    addressLine1: '',
    addressLine2: '',
    city: '',
    state: '',
    postalCode: '',
    country: 'NZ',
  });
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<'customer' | 'payment'>('customer');

  const handleCustomerInfoChange = (field: keyof CustomerInfo, value: string) => {
    setCustomerInfo(prev => ({ ...prev, [field]: value }));
    setValidationErrors([]);
  };

  const validateAndProceedToPayment = () => {
    const validation = validateCustomerInfo(customerInfo);
    
    if (!validation.isValid) {
      setValidationErrors(validation.errors);
      return;
    }

    setValidationErrors([]);
    setCurrentStep('payment');
  };

  const handlePayment = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!stripe || !elements || isProcessing) {
      return;
    }

    setIsProcessing(true);
    setPaymentError(null);

    try {
      // Create order with payment intent
      const orderResponse = await apiEndpoints.createOrder({
        quote_id: quote.quote_id,
        customer_info: customerInfo,
      });

      const { order_id, payment_intent_client_secret } = orderResponse.data;

      // Get the card element
      const cardElement = elements.getElement(CardElement);
      if (!cardElement) {
        throw new Error('Card element not found');
      }

      // Confirm payment with Stripe
      const { error, paymentIntent } = await stripe.confirmCardPayment(
        payment_intent_client_secret,
        {
          payment_method: {
            card: cardElement,
            billing_details: {
              name: `${customerInfo.firstName} ${customerInfo.lastName}`,
              email: customerInfo.email,
              phone: customerInfo.phone || undefined,
              address: {
                line1: customerInfo.addressLine1,
                line2: customerInfo.addressLine2 || undefined,
                city: customerInfo.city,
                state: customerInfo.state || undefined,
                postal_code: customerInfo.postalCode,
                country: customerInfo.country,
              },
            },
          },
        }
      );

      if (error) {
        throw new Error(error.message || 'Payment failed');
      }

      if (paymentIntent?.status === 'succeeded') {
        // Confirm payment with backend
        await apiEndpoints.confirmPayment({
          payment_intent_id: paymentIntent.id,
          order_id: order_id,
        });

        onPaymentSuccess(order_id);
      } else {
        throw new Error('Payment was not successful');
      }

    } catch (err: any) {
      const errorMessage = handleApiError(err);
      setPaymentError(errorMessage);
      onPaymentError(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  const cardElementOptions = {
    style: {
      base: {
        fontSize: '16px',
        color: '#424770',
        '::placeholder': {
          color: '#aab7c4',
        },
      },
      invalid: {
        color: '#9e2146',
      },
    },
    hidePostalCode: true, // We collect this separately
  };

  return (
    <div className="space-y-6">
      {/* Step Indicator */}
      <div className="flex items-center justify-center space-x-4">
        <div className={`flex items-center space-x-2 ${
          currentStep === 'customer' ? 'text-primary' : 'text-muted-foreground'
        }`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            currentStep === 'customer' ? 'bg-primary text-primary-foreground' : 'bg-muted'
          }`}>
            {currentStep === 'payment' ? <CheckCircle className="w-4 h-4" /> : '1'}
          </div>
          <span className="text-sm font-medium">Customer Info</span>
        </div>
        
        <div className="w-8 h-px bg-border" />
        
        <div className={`flex items-center space-x-2 ${
          currentStep === 'payment' ? 'text-primary' : 'text-muted-foreground'
        }`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            currentStep === 'payment' ? 'bg-primary text-primary-foreground' : 'bg-muted'
          }`}>
            2
          </div>
          <span className="text-sm font-medium">Payment</span>
        </div>
      </div>

      {/* Customer Information Step */}
      {currentStep === 'customer' && (
        <div className="quote-card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <User className="h-5 w-5" />
            Customer Information
          </h3>

          <div className="space-y-4">
            {/* Name Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  First Name *
                </label>
                <input
                  type="text"
                  value={customerInfo.firstName}
                  onChange={(e) => handleCustomerInfoChange('firstName', e.target.value)}
                  disabled={disabled}
                  className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">
                  Last Name *
                </label>
                <input
                  type="text"
                  value={customerInfo.lastName}
                  onChange={(e) => handleCustomerInfoChange('lastName', e.target.value)}
                  disabled={disabled}
                  className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50"
                  required
                />
              </div>
            </div>

            {/* Contact Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2 flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  Email *
                </label>
                <input
                  type="email"
                  value={customerInfo.email}
                  onChange={(e) => handleCustomerInfoChange('email', e.target.value)}
                  disabled={disabled}
                  className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  Phone
                </label>
                <input
                  type="tel"
                  value={customerInfo.phone}
                  onChange={(e) => handleCustomerInfoChange('phone', e.target.value)}
                  disabled={disabled}
                  className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50"
                />
              </div>
            </div>

            {/* Company */}
            <div>
              <label className="block text-sm font-medium mb-2 flex items-center gap-2">
                <Building className="h-4 w-4" />
                Company
              </label>
              <input
                type="text"
                value={customerInfo.company}
                onChange={(e) => handleCustomerInfoChange('company', e.target.value)}
                disabled={disabled}
                className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50"
              />
            </div>

            {/* Address */}
            <div className="space-y-4">
              <h4 className="font-medium flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                Shipping Address
              </h4>
              
              <div>
                <label className="block text-sm font-medium mb-2">
                  Address Line 1 *
                </label>
                <input
                  type="text"
                  value={customerInfo.addressLine1}
                  onChange={(e) => handleCustomerInfoChange('addressLine1', e.target.value)}
                  disabled={disabled}
                  className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Address Line 2
                </label>
                <input
                  type="text"
                  value={customerInfo.addressLine2}
                  onChange={(e) => handleCustomerInfoChange('addressLine2', e.target.value)}
                  disabled={disabled}
                  className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    City *
                  </label>
                  <input
                    type="text"
                    value={customerInfo.city}
                    onChange={(e) => handleCustomerInfoChange('city', e.target.value)}
                    disabled={disabled}
                    className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    State/Region
                  </label>
                  <input
                    type="text"
                    value={customerInfo.state}
                    onChange={(e) => handleCustomerInfoChange('state', e.target.value)}
                    disabled={disabled}
                    className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Postal Code *
                  </label>
                  <input
                    type="text"
                    value={customerInfo.postalCode}
                    onChange={(e) => handleCustomerInfoChange('postalCode', e.target.value)}
                    disabled={disabled}
                    className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Country *
                </label>
                <select
                  value={customerInfo.country}
                  onChange={(e) => handleCustomerInfoChange('country', e.target.value)}
                  disabled={disabled}
                  className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50"
                  required
                >
                  <option value="NZ">New Zealand</option>
                  <option value="AU">Australia</option>
                  <option value="US">United States</option>
                  <option value="GB">United Kingdom</option>
                  <option value="CA">Canada</option>
                </select>
              </div>
            </div>

            {/* Validation Errors */}
            {validationErrors.length > 0 && (
              <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-destructive">
                      Please fix the following errors:
                    </p>
                    <ul className="text-sm text-destructive mt-1 space-y-1">
                      {validationErrors.map((error, index) => (
                        <li key={index}>• {error}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Continue Button */}
            <button
              onClick={validateAndProceedToPayment}
              disabled={disabled}
              className="w-full bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Continue to Payment
            </button>
          </div>
        </div>
      )}

      {/* Payment Step */}
      {currentStep === 'payment' && (
        <form onSubmit={handlePayment} className="space-y-6">
          <div className="quote-card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              Payment Information
            </h3>

            <div className="space-y-4">
              {/* Card Element */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Card Information
                </label>
                <div className="p-3 border border-border rounded-md">
                  <CardElement options={cardElementOptions} />
                </div>
              </div>

              {/* Security Note */}
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Lock className="h-4 w-4" />
                  <span>Your payment information is encrypted and secure</span>
                </div>
              </div>

              {/* Payment Error */}
              {paymentError && (
                <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-destructive">
                        Payment Error
                      </p>
                      <p className="text-sm text-destructive mt-1">{paymentError}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Back and Pay Buttons */}
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  type="button"
                  onClick={() => setCurrentStep('customer')}
                  disabled={disabled || isProcessing}
                  className="flex-1 bg-secondary text-secondary-foreground px-6 py-3 rounded-lg font-medium hover:bg-secondary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={disabled || isProcessing || !stripe || !elements}
                  className="flex-1 bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isProcessing ? (
                    <>
                      <div className="loading-spinner" />
                      Processing...
                    </>
                  ) : (
                    `Pay ${quote.total.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}`
                  )}
                </button>
              </div>
            </div>
          </div>
        </form>
      )}
    </div>
  );
};

export default PaymentForm;