import React, { useState, useEffect } from 'react';
import { 
  CheckCircle, 
  Download, 
  Mail, 
  MapPin, 
  Calendar,
  Package,
  Truck,
  DollarSign,
  FileText,
  ExternalLink,
  Copy,
  Check,
  AlertCircle
} from 'lucide-react';
import { QuoteResponse, OrderResponse, apiEndpoints, handleApiError } from '@/utils/api';
import { formatCurrency, formatDimensions } from '@/utils/validators';

interface OrderConfirmationProps {
  orderId: string;
  onStartNewOrder?: () => void;
  onViewOrder?: (orderId: string) => void;
}

const OrderConfirmation: React.FC<OrderConfirmationProps> = ({
  orderId,
  onStartNewOrder,
  onViewOrder,
}) => {
  const [order, setOrder] = useState<OrderResponse | null>(null);
  const [quote, setQuote] = useState<QuoteResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  useEffect(() => {
    const loadOrderDetails = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Load order details
        const orderResponse = await apiEndpoints.getOrder(orderId);
        setOrder(orderResponse.data);

        // Load associated quote details
        if (orderResponse.data.quote_id) {
          const quoteResponse = await apiEndpoints.getQuote(orderResponse.data.quote_id);
          setQuote(quoteResponse.data);
        }
      } catch (err: any) {
        const errorMessage = handleApiError(err);
        setError(errorMessage);
        console.error('Failed to load order details:', err);
      } finally {
        setIsLoading(false);
      }
    };

    if (orderId) {
      loadOrderDetails();
    }
  }, [orderId]);

  const copyToClipboard = async (text: string, fieldName: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(fieldName);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  const getEstimatedDeliveryDate = () => {
    if (!order?.created_at || !quote?.estimated_shipping_days) {
      return null;
    }

    const createdDate = new Date(order.created_at);
    const deliveryDate = new Date(createdDate);
    deliveryDate.setDate(createdDate.getDate() + quote.estimated_shipping_days);
    
    return deliveryDate;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
        <div className="w-full max-w-2xl">
          <div className="quote-card animate-pulse">
            <div className="text-center space-y-4">
              <div className="w-16 h-16 bg-muted rounded-full mx-auto" />
              <div className="h-8 bg-muted rounded w-1/2 mx-auto" />
              <div className="space-y-2">
                <div className="h-4 bg-muted rounded w-3/4 mx-auto" />
                <div className="h-4 bg-muted rounded w-1/2 mx-auto" />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
        <div className="w-full max-w-2xl">
          <div className="quote-card border-destructive/20 bg-destructive/5">
            <div className="text-center space-y-4">
              <AlertCircle className="w-16 h-16 text-destructive mx-auto" />
              <h1 className="text-2xl font-bold text-destructive">Order Not Found</h1>
              <p className="text-destructive/80">{error}</p>
              {onStartNewOrder && (
                <button
                  onClick={onStartNewOrder}
                  className="bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors"
                >
                  Start New Order
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!order || !quote) {
    return null;
  }

  const estimatedDelivery = getEstimatedDeliveryDate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 p-4">
      <div className="w-full max-w-4xl mx-auto space-y-6">
        {/* Success Header */}
        <div className="text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-12 h-12 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Order Confirmed!
          </h1>
          <p className="text-lg text-muted-foreground">
            Thank you for your order. We'll start processing it right away.
          </p>
        </div>

        {/* Order Summary */}
        <div className="quote-card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold">Order Summary</h2>
            <div className="text-right">
              <div className="text-sm text-muted-foreground">Order ID</div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm">{order.order_id}</span>
                <button
                  onClick={() => copyToClipboard(order.order_id, 'orderId')}
                  className="p-1 hover:bg-muted rounded transition-colors"
                  title="Copy order ID"
                >
                  {copiedField === 'orderId' ? (
                    <Check className="w-4 h-4 text-green-600" />
                  ) : (
                    <Copy className="w-4 h-4 text-muted-foreground" />
                  )}
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Payment Details */}
            <div className="space-y-3">
              <h3 className="font-medium flex items-center gap-2">
                <DollarSign className="w-4 h-4" />
                Payment
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Subtotal:</span>
                  <span>{formatCurrency(quote.subtotal)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Shipping:</span>
                  <span>{formatCurrency(quote.shipping_cost)}</span>
                </div>
                <div className="border-t pt-2">
                  <div className="flex justify-between font-medium">
                    <span>Total Paid:</span>
                    <span className="text-green-600">{formatCurrency(quote.total)}</span>
                  </div>
                </div>
                <div className="text-xs text-muted-foreground">
                  Payment Method: {order.payment_method || 'Credit Card'}
                </div>
              </div>
            </div>

            {/* Shipping Details */}
            <div className="space-y-3">
              <h3 className="font-medium flex items-center gap-2">
                <Truck className="w-4 h-4" />
                Shipping
              </h3>
              <div className="space-y-2 text-sm">
                {order.customer_info && (
                  <div>
                    <div className="font-medium">
                      {order.customer_info.firstName} {order.customer_info.lastName}
                    </div>
                    {order.customer_info.company && (
                      <div className="text-muted-foreground">{order.customer_info.company}</div>
                    )}
                    <div className="text-muted-foreground">
                      {order.customer_info.addressLine1}
                      {order.customer_info.addressLine2 && (
                        <><br />{order.customer_info.addressLine2}</>
                      )}
                      <br />
                      {order.customer_info.city}, {order.customer_info.state} {order.customer_info.postalCode}
                      <br />
                      {order.customer_info.country}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Delivery Timeline */}
            <div className="space-y-3">
              <h3 className="font-medium flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                Timeline
              </h3>
              <div className="space-y-2 text-sm">
                <div>
                  <div className="text-muted-foreground">Order Placed:</div>
                  <div>{new Date(order.created_at).toLocaleDateString()}</div>
                </div>
                {estimatedDelivery && (
                  <div>
                    <div className="text-muted-foreground">Est. Delivery:</div>
                    <div className="font-medium text-blue-600">
                      {estimatedDelivery.toLocaleDateString()}
                    </div>
                  </div>
                )}
                <div className="text-xs text-muted-foreground">
                  {quote.estimated_shipping_days} business days
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Order Items */}
        <div className="quote-card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Package className="w-5 h-5" />
            Items Ordered ({quote.files.length})
          </h3>
          
          <div className="space-y-3">
            {quote.files.map((file, index) => {
              const dimensions = file.bounding_box 
                ? [
                    file.bounding_box.max_x - file.bounding_box.min_x,
                    file.bounding_box.max_y - file.bounding_box.min_y,
                    file.bounding_box.max_z - file.bounding_box.min_z
                  ] as [number, number, number]
                : [0, 0, 0] as [number, number, number];

              return (
                <div key={index} className="border border-border rounded-lg p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-muted-foreground" />
                      <div>
                        <div className="font-medium">{file.filename}</div>
                        <div className="text-sm text-muted-foreground">
                          {file.quantity} × {file.material.replace('_', ' ')}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">{formatCurrency(file.total_price)}</div>
                      <div className="text-sm text-muted-foreground">
                        {formatCurrency(file.unit_price)} each
                      </div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs text-muted-foreground">
                    <div>
                      <span>Volume: </span>
                      <span className="font-medium">{file.volume.toFixed(2)} cm³</span>
                    </div>
                    <div>
                      <span>Dimensions: </span>
                      <span className="font-medium">{formatDimensions(dimensions)}</span>
                    </div>
                    <div>
                      <span>Quality: </span>
                      <span className={`font-medium ${file.is_watertight ? 'text-green-600' : 'text-yellow-600'}`}>
                        {file.is_watertight ? 'Verified' : 'Check needed'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Next Steps */}
        <div className="quote-card">
          <h3 className="text-lg font-semibold mb-4">What Happens Next?</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex gap-3">
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-bold text-blue-600">1</span>
                </div>
                <div>
                  <div className="font-medium">Order Processing</div>
                  <div className="text-sm text-muted-foreground">
                    We'll review your files and prepare them for 3D printing.
                  </div>
                </div>
              </div>
              
              <div className="flex gap-3">
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-bold text-blue-600">2</span>
                </div>
                <div>
                  <div className="font-medium">3D Printing</div>
                  <div className="text-sm text-muted-foreground">
                    Your parts will be printed using our HP Multi Jet Fusion technology.
                  </div>
                </div>
              </div>
              
              <div className="flex gap-3">
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-bold text-blue-600">3</span>
                </div>
                <div>
                  <div className="font-medium">Quality Check & Shipping</div>
                  <div className="text-sm text-muted-foreground">
                    We'll inspect your parts and ship them to your address.
                  </div>
                </div>
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Mail className="w-4 h-4 text-blue-600" />
                  <span className="font-medium text-blue-800">Email Updates</span>
                </div>
                <p className="text-sm text-blue-700">
                  You'll receive email updates at each stage of the process.
                  {order.customer_info?.email && (
                    <span className="block mt-1 font-medium">
                      {order.customer_info.email}
                    </span>
                  )}
                </p>
              </div>
              
              {order.tracking_number && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Truck className="w-4 h-4 text-green-600" />
                    <span className="font-medium text-green-800">Tracking Available</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-green-700 font-mono">
                      {order.tracking_number}
                    </span>
                    <button
                      onClick={() => copyToClipboard(order.tracking_number!, 'tracking')}
                      className="p-1 hover:bg-green-100 rounded transition-colors"
                    >
                      {copiedField === 'tracking' ? (
                        <Check className="w-3 h-3 text-green-600" />
                      ) : (
                        <Copy className="w-3 h-3 text-green-600" />
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          {onViewOrder && (
            <button
              onClick={() => onViewOrder(order.order_id)}
              className="bg-secondary text-secondary-foreground px-6 py-3 rounded-lg font-medium hover:bg-secondary/90 transition-colors flex items-center gap-2"
            >
              <ExternalLink className="w-4 h-4" />
              View Order Details
            </button>
          )}
          
          {onStartNewOrder && (
            <button
              onClick={onStartNewOrder}
              className="bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors"
            >
              Place Another Order
            </button>
          )}
        </div>

        {/* Contact Information */}
        <div className="quote-card bg-muted/30">
          <div className="text-center space-y-2">
            <h3 className="font-medium">Need Help?</h3>
            <p className="text-sm text-muted-foreground">
              If you have any questions about your order, please contact us:
            </p>
            <div className="flex items-center justify-center gap-4 text-sm">
              <a 
                href="mailto:support@example.com" 
                className="text-primary hover:underline flex items-center gap-1"
              >
                <Mail className="w-3 h-3" />
                support@example.com
              </a>
              <span className="text-muted-foreground">•</span>
              <span>+64 123 456 789</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderConfirmation;