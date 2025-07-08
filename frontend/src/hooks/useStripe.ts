import { useState, useEffect } from 'react';
import { loadStripe, Stripe, StripeElements } from '@stripe/stripe-js';
import { apiEndpoints, handleApiError } from '@/utils/api';

export interface UseStripeReturn {
  stripe: Stripe | null;
  isLoading: boolean;
  error: string | null;
  createPaymentIntent: (quoteId: string, customerEmail: string) => Promise<any>;
  confirmPayment: (paymentIntentId: string, orderId: string) => Promise<any>;
}

let stripePromise: Promise<Stripe | null> | null = null;

export const useStripe = (): UseStripeReturn => {
  const [stripe, setStripe] = useState<Stripe | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initializeStripe = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Get Stripe publishable key from backend
        const configResponse = await apiEndpoints.getPaymentConfig();
        const { stripe_publishable_key } = configResponse.data;

        if (!stripe_publishable_key) {
          throw new Error('Stripe publishable key not configured');
        }

        // Initialize Stripe only once
        if (!stripePromise) {
          stripePromise = loadStripe(stripe_publishable_key);
        }

        const stripeInstance = await stripePromise;
        
        if (!stripeInstance) {
          throw new Error('Failed to load Stripe');
        }

        setStripe(stripeInstance);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to initialize Stripe';
        setError(errorMessage);
        console.error('Stripe initialization error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    initializeStripe();
  }, []);

  const createPaymentIntent = async (quoteId: string, customerEmail: string) => {
    try {
      setError(null);
      
      const response = await apiEndpoints.createPaymentIntent({
        quote_id: quoteId,
        customer_email: customerEmail,
      });

      return response.data;
    } catch (err: any) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  const confirmPayment = async (paymentIntentId: string, orderId: string) => {
    try {
      setError(null);
      
      const response = await apiEndpoints.confirmPayment({
        payment_intent_id: paymentIntentId,
        order_id: orderId,
      });

      return response.data;
    } catch (err: any) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  return {
    stripe,
    isLoading,
    error,
    createPaymentIntent,
    confirmPayment,
  };
};