import React, { useState } from 'react';
import { 
  FileText, 
  Package, 
  Truck, 
  DollarSign, 
  Clock, 
  AlertTriangle,
  Eye,
  EyeOff,
  Download,
  Printer
} from 'lucide-react';
import { QuoteResponse, STLFileResponse } from '@/utils/api';
import { formatCurrency, formatVolume, formatDimensions } from '@/utils/validators';

interface QuoteDisplayProps {
  quote: QuoteResponse | null;
  isLoading?: boolean;
  error?: string | null;
  showDetailedBreakdown?: boolean;
  onProceedToPayment?: () => void;
  onEditQuote?: () => void;
  disabled?: boolean;
}

const QuoteDisplay: React.FC<QuoteDisplayProps> = ({
  quote,
  isLoading = false,
  error = null,
  showDetailedBreakdown = true,
  onProceedToPayment,
  onEditQuote,
  disabled = false,
}) => {
  const [showFileDetails, setShowFileDetails] = useState(false);
  const [showBreakdown, setShowBreakdown] = useState(false);

  if (isLoading) {
    return (
      <div className="quote-card">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-muted rounded w-1/3" />
          <div className="space-y-3">
            <div className="h-4 bg-muted rounded w-full" />
            <div className="h-4 bg-muted rounded w-3/4" />
            <div className="h-4 bg-muted rounded w-1/2" />
          </div>
          <div className="h-10 bg-muted rounded" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="quote-card border-destructive/20 bg-destructive/5">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-destructive mt-0.5" />
          <div>
            <p className="font-medium text-destructive">Quote Error</p>
            <p className="text-sm text-destructive/80 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!quote) {
    return (
      <div className="quote-card border-dashed">
        <div className="text-center text-muted-foreground py-8">
          <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg font-medium">No Quote Generated</p>
          <p className="text-sm mt-2">Upload STL files to generate a quote</p>
        </div>
      </div>
    );
  }

  const isExpired = quote.expires_at && new Date(quote.expires_at) < new Date();
  const isValidQuote = quote.is_valid && !isExpired;

  return (
    <div className="space-y-4">
      {/* Quote Header */}
      <div className="quote-card">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="text-xl font-semibold">Quote Summary</h3>
            <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
              <span>Quote ID: {quote.quote_id.slice(0, 8)}</span>
              <span>•</span>
              <span>{quote.files.length} file{quote.files.length !== 1 ? 's' : ''}</span>
              {quote.created_at && (
                <>
                  <span>•</span>
                  <span>Created {new Date(quote.created_at).toLocaleDateString()}</span>
                </>
              )}
            </div>
          </div>
          
          {/* Status Indicator */}
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${
            isValidQuote 
              ? 'bg-green-100 text-green-800' 
              : 'bg-yellow-100 text-yellow-800'
          }`}>
            {isValidQuote ? 'Valid' : 'Expired'}
          </div>
        </div>

        {/* Warning for expired quotes */}
        {isExpired && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <span className="text-sm font-medium text-yellow-800">
                Quote Expired
              </span>
            </div>
            <p className="text-sm text-yellow-700 mt-1">
              This quote expired on {new Date(quote.expires_at!).toLocaleDateString()}. 
              Please generate a new quote to proceed.
            </p>
          </div>
        )}

        {/* Quote Totals */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="text-center p-4 bg-muted/50 rounded-lg">
            <div className="text-2xl font-bold text-foreground">
              {formatCurrency(quote.subtotal)}
            </div>
            <div className="text-sm text-muted-foreground">Subtotal</div>
          </div>
          
          <div className="text-center p-4 bg-muted/50 rounded-lg">
            <div className="text-2xl font-bold text-foreground">
              {formatCurrency(quote.shipping_cost)}
            </div>
            <div className="text-sm text-muted-foreground">
              Shipping ({quote.shipping_size})
            </div>
          </div>
          
          <div className="text-center p-4 bg-primary/10 rounded-lg border border-primary/20">
            <div className="text-3xl font-bold text-primary">
              {formatCurrency(quote.total)}
            </div>
            <div className="text-sm text-primary/80 font-medium">Total</div>
          </div>
        </div>

        {/* Delivery Information */}
        <div className="flex items-center justify-center gap-6 text-sm text-muted-foreground mb-6">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            <span>Est. {quote.estimated_shipping_days} business days</span>
          </div>
          <div className="flex items-center gap-2">
            <Truck className="h-4 w-4" />
            <span>{quote.shipping_size} package</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          {isValidQuote && onProceedToPayment && (
            <button
              onClick={onProceedToPayment}
              disabled={disabled}
              className="flex-1 bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Proceed to Payment
            </button>
          )}
          
          {onEditQuote && (
            <button
              onClick={onEditQuote}
              disabled={disabled}
              className="flex-1 bg-secondary text-secondary-foreground px-6 py-3 rounded-lg font-medium hover:bg-secondary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Edit Quote
            </button>
          )}
        </div>
      </div>

      {/* File Details Toggle */}
      <div className="quote-card">
        <button
          onClick={() => setShowFileDetails(!showFileDetails)}
          className="w-full flex items-center justify-between p-2 hover:bg-muted/50 rounded-lg transition-colors"
        >
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            <span className="font-medium">File Details ({quote.files.length})</span>
          </div>
          {showFileDetails ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>

        {showFileDetails && (
          <div className="mt-4 space-y-3">
            {quote.files.map((file, index) => (
              <FileDetailItem key={index} file={file} />
            ))}
          </div>
        )}
      </div>

      {/* Detailed Breakdown Toggle */}
      {showDetailedBreakdown && (
        <div className="quote-card">
          <button
            onClick={() => setShowBreakdown(!showBreakdown)}
            className="w-full flex items-center justify-between p-2 hover:bg-muted/50 rounded-lg transition-colors"
          >
            <div className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              <span className="font-medium">Price Breakdown</span>
            </div>
            {showBreakdown ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>

          {showBreakdown && <PriceBreakdown quote={quote} />}
        </div>
      )}
    </div>
  );
};

interface FileDetailItemProps {
  file: STLFileResponse;
}

const FileDetailItem: React.FC<FileDetailItemProps> = ({ file }) => {
  const dimensions = file.bounding_box 
    ? [
        file.bounding_box.max_x - file.bounding_box.min_x,
        file.bounding_box.max_y - file.bounding_box.min_y,
        file.bounding_box.max_z - file.bounding_box.min_z
      ] as [number, number, number]
    : [0, 0, 0] as [number, number, number];

  return (
    <div className="border border-border rounded-lg p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="font-medium text-sm">{file.filename}</p>
            <p className="text-xs text-muted-foreground">
              {(file.file_size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
        </div>
        
        <div className="text-right">
          <p className="font-medium">{formatCurrency(file.total_price)}</p>
          <p className="text-xs text-muted-foreground">
            {file.quantity} × {formatCurrency(file.unit_price)}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        <div>
          <span className="text-muted-foreground">Material:</span>
          <p className="font-medium">{file.material.replace('_', ' ')}</p>
        </div>
        <div>
          <span className="text-muted-foreground">Volume:</span>
          <p className="font-medium">{formatVolume(file.volume)}</p>
        </div>
        <div>
          <span className="text-muted-foreground">Dimensions:</span>
          <p className="font-medium">{formatDimensions(dimensions)}</p>
        </div>
        <div>
          <span className="text-muted-foreground">Quality:</span>
          <p className={`font-medium ${file.is_watertight ? 'text-green-600' : 'text-yellow-600'}`}>
            {file.is_watertight ? 'Good' : 'Check needed'}
          </p>
        </div>
      </div>
    </div>
  );
};

interface PriceBreakdownProps {
  quote: QuoteResponse;
}

const PriceBreakdown: React.FC<PriceBreakdownProps> = ({ quote }) => {
  const materialCost = quote.files.reduce((total, file) => {
    // Estimate material cost (this would come from detailed breakdown API in real implementation)
    return total + (file.total_price * 0.7); // Rough estimate
  }, 0);

  const markup = quote.subtotal - materialCost;

  return (
    <div className="mt-4 space-y-3">
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Material Costs:</span>
          <span>{formatCurrency(materialCost)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Processing & Markup:</span>
          <span>{formatCurrency(markup)}</span>
        </div>
        <div className="border-t pt-2">
          <div className="flex justify-between text-sm font-medium">
            <span>Subtotal:</span>
            <span>{formatCurrency(quote.subtotal)}</span>
          </div>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">
            Shipping ({quote.shipping_size}):
          </span>
          <span>{formatCurrency(quote.shipping_cost)}</span>
        </div>
        <div className="border-t pt-2">
          <div className="flex justify-between font-semibold">
            <span>Total:</span>
            <span className="text-primary">{formatCurrency(quote.total)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuoteDisplay;