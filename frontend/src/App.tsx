import React, { useState, useCallback } from 'react';
import { AlertCircle, Package, FileText } from 'lucide-react';
import { FileWithMetadata } from '@/hooks/useFileUpload';
import { QuoteResponse, apiEndpoints, handleApiError } from '@/utils/api';
import FileUpload from '@/components/FileUpload';
import MaterialSelector from '@/components/MaterialSelector';
import QuoteDisplay from '@/components/QuoteDisplay';
import PaymentForm from '@/components/PaymentForm';
import OrderConfirmation from '@/components/OrderConfirmation';

type AppStep = 'upload' | 'materials' | 'quote' | 'payment' | 'confirmation';

interface AppState {
  currentStep: AppStep;
  files: FileWithMetadata[];
  quote: QuoteResponse | null;
  orderId: string | null;
  estimatedTotal: number;
  isLoading: boolean;
  error: string | null;
}

const App: React.FC = () => {
  const [state, setState] = useState<AppState>({
    currentStep: 'upload',
    files: [],
    quote: null,
    orderId: null,
    estimatedTotal: 0,
    isLoading: false,
    error: null,
  });

  const updateState = useCallback((updates: Partial<AppState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  const setError = useCallback((error: string | null) => {
    updateState({ error });
  }, [updateState]);

  const setLoading = useCallback((isLoading: boolean) => {
    updateState({ isLoading });
  }, [updateState]);

  // Handle file uploads
  const handleFilesChange = useCallback((newFiles: FileWithMetadata[]) => {
    updateState({ 
      files: newFiles,
      currentStep: newFiles.length > 0 ? 'materials' : 'upload',
      quote: null,
      error: null 
    });
  }, [updateState]);

  // Handle material/quantity updates
  const handleFileUpdate = useCallback((fileId: string, material: string, quantity: number) => {
    updateState({
      files: state.files.map(file => 
        file.id === fileId 
          ? { ...file, material, quantity }
          : file
      )
    });
  }, [state.files, updateState]);

  // Handle estimate updates from MaterialSelector
  const handleEstimateUpdate = useCallback((estimate: number) => {
    updateState({ estimatedTotal: estimate });
  }, [updateState]);

  // Generate quote
  const generateQuote = useCallback(async () => {
    if (state.files.length === 0) {
      setError('Please upload at least one STL file');
      return;
    }

    // Validate all files have materials and quantities
    const invalidFiles = state.files.filter(file => !file.material || file.quantity < 1);
    if (invalidFiles.length > 0) {
      setError('Please select materials and quantities for all files');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Prepare form data
      const formData = new FormData();
      
      // Add files
      state.files.forEach((fileData) => {
        formData.append('files', fileData.file);
      });
      
      // Add materials array
      state.files.forEach((fileData) => {
        formData.append('materials', fileData.material);
      });
      
      // Add quantities array
      state.files.forEach((fileData) => {
        formData.append('quantities', fileData.quantity.toString());
      });

      // Generate quote
      const response = await apiEndpoints.generateQuote(formData);
      updateState({ 
        quote: response.data,
        currentStep: 'quote',
        error: null 
      });

    } catch (err: any) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [state.files, setLoading, setError, updateState]);

  // Proceed to payment
  const proceedToPayment = useCallback(() => {
    if (!state.quote) {
      setError('No quote available');
      return;
    }

    if (!state.quote.is_valid) {
      setError('Quote is no longer valid. Please generate a new quote.');
      return;
    }

    updateState({ currentStep: 'payment', error: null });
  }, [state.quote, setError, updateState]);

  // Handle payment success
  const handlePaymentSuccess = useCallback((orderId: string) => {
    updateState({ 
      orderId,
      currentStep: 'confirmation',
      error: null 
    });
  }, [updateState]);

  // Handle payment error
  const handlePaymentError = useCallback((error: string) => {
    setError(error);
  }, [setError]);

  // Start new order
  const startNewOrder = useCallback(() => {
    setState({
      currentStep: 'upload',
      files: [],
      quote: null,
      orderId: null,
      estimatedTotal: 0,
      isLoading: false,
      error: null,
    });
  }, []);

  // Edit quote (go back to materials)
  const editQuote = useCallback(() => {
    updateState({ 
      currentStep: 'materials',
      quote: null,
      error: null 
    });
  }, [updateState]);

  // View order details (placeholder - would integrate with order management)
  const viewOrderDetails = useCallback((orderId: string) => {
    console.log('View order details for:', orderId);
    // In a real app, this would navigate to an order details page
  }, []);

  const renderStepIndicator = () => {
    const steps = [
      { key: 'upload', label: 'Upload Files', icon: FileText },
      { key: 'materials', label: 'Select Materials', icon: Package },
      { key: 'quote', label: 'Review Quote', icon: FileText },
      { key: 'payment', label: 'Payment', icon: FileText },
    ];

    const currentStepIndex = steps.findIndex(step => step.key === state.currentStep);

    return (
      <div className="flex items-center justify-center space-x-4 mb-8">
        {steps.map((step, index) => {
          const StepIcon = step.icon;
          const isActive = step.key === state.currentStep;
          const isCompleted = index < currentStepIndex;
          const isAccessible = index <= currentStepIndex;

          return (
            <React.Fragment key={step.key}>
              <div className={`flex items-center space-x-2 ${
                isActive ? 'text-primary' : 
                isCompleted ? 'text-green-600' : 
                'text-muted-foreground'
              }`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  isActive ? 'bg-primary text-primary-foreground' :
                  isCompleted ? 'bg-green-100 text-green-600' :
                  'bg-muted'
                }`}>
                  {isCompleted ? (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <StepIcon className="w-4 h-4" />
                  )}
                </div>
                <span className="text-sm font-medium hidden sm:block">{step.label}</span>
              </div>
              
              {index < steps.length - 1 && (
                <div className={`w-8 h-px ${
                  isCompleted ? 'bg-green-300' : 'bg-border'
                }`} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    );
  };

  const renderMainContent = () => {
    if (state.currentStep === 'confirmation' && state.orderId) {
      return (
        <OrderConfirmation
          orderId={state.orderId}
          onStartNewOrder={startNewOrder}
          onViewOrder={viewOrderDetails}
        />
      );
    }

    return (
      <div className="w-full max-w-4xl mx-auto space-y-6">
        {/* Step Indicator */}
        {state.currentStep !== 'confirmation' && renderStepIndicator()}

        {/* Error Display */}
        {state.error && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
              <div>
                <p className="text-sm font-medium text-destructive">Error</p>
                <p className="text-sm text-destructive/80 mt-1">{state.error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Main Content Based on Current Step */}
        <div className="space-y-6">
          {/* Upload Step */}
          {state.currentStep === 'upload' && (
            <div>
              <div className="text-center mb-8">
                <h1 className="text-3xl font-bold text-foreground mb-4">
                  3D Printing Quote Tool
                </h1>
                <p className="text-lg text-muted-foreground">
                  Upload your STL files to get an instant quote
                </p>
              </div>
              
              <FileUpload
                onFilesChange={handleFilesChange}
                disabled={state.isLoading}
                maxFiles={10}
              />
            </div>
          )}

          {/* Materials Step */}
          {state.currentStep === 'materials' && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-foreground mb-2">
                  Select Materials & Quantities
                </h2>
                <p className="text-muted-foreground">
                  Choose the material and quantity for each file
                </p>
              </div>

              <MaterialSelector
                files={state.files}
                onFileUpdate={handleFileUpdate}
                onEstimateUpdate={handleEstimateUpdate}
                disabled={state.isLoading}
              />

              {state.files.length > 0 && (
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  <button
                    onClick={() => updateState({ currentStep: 'upload' })}
                    disabled={state.isLoading}
                    className="flex-1 sm:flex-none bg-secondary text-secondary-foreground px-6 py-3 rounded-lg font-medium hover:bg-secondary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Back to Upload
                  </button>
                  <button
                    onClick={generateQuote}
                    disabled={state.isLoading || state.files.some(f => !f.material || f.quantity < 1)}
                    className="flex-1 sm:flex-none bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {state.isLoading ? (
                      <>
                        <div className="loading-spinner" />
                        Generating Quote...
                      </>
                    ) : (
                      'Generate Quote'
                    )}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Quote Step */}
          {state.currentStep === 'quote' && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-foreground mb-2">
                  Your Quote
                </h2>
                <p className="text-muted-foreground">
                  Review your quote details before proceeding to payment
                </p>
              </div>

              <QuoteDisplay
                quote={state.quote}
                isLoading={state.isLoading}
                error={state.error}
                showDetailedBreakdown={true}
                onProceedToPayment={proceedToPayment}
                onEditQuote={editQuote}
                disabled={state.isLoading}
              />
            </div>
          )}

          {/* Payment Step */}
          {state.currentStep === 'payment' && state.quote && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-foreground mb-2">
                  Complete Your Order
                </h2>
                <p className="text-muted-foreground">
                  Enter your details and payment information
                </p>
              </div>

              {/* Quote Summary */}
              <QuoteDisplay
                quote={state.quote}
                showDetailedBreakdown={false}
                disabled={true}
              />

              <PaymentForm
                quote={state.quote}
                onPaymentSuccess={handlePaymentSuccess}
                onPaymentError={handlePaymentError}
                disabled={state.isLoading}
              />

              <div className="flex justify-center">
                <button
                  onClick={() => updateState({ currentStep: 'quote' })}
                  disabled={state.isLoading}
                  className="bg-secondary text-secondary-foreground px-6 py-3 rounded-lg font-medium hover:bg-secondary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Back to Quote
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        {renderMainContent()}
      </div>
    </div>
  );
};

export default App;