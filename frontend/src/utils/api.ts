import axios, { AxiosResponse, AxiosError } from 'axios';

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const apiEndpoints = {
  // Configuration
  getConfig: () => api.get('/api/config'),
  
  // Quote endpoints
  uploadFiles: (formData: FormData) => 
    api.post('/api/quote/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000, // 60 seconds for file upload
    }),
  generateQuote: (formData: FormData) => 
    api.post('/api/quote/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000, // 60 seconds for file upload
    }),
  getQuote: (quoteId: string) => api.get(`/api/quote/${quoteId}`),
  updateQuote: (quoteId: string, data: any) => api.post(`/api/quote/${quoteId}/update`, data),
  getQuoteBreakdown: (quoteId: string) => api.get(`/api/quote/${quoteId}/breakdown`),
  listQuotes: (params?: any) => api.get('/api/quote/', { params }),
  deleteQuote: (quoteId: string) => api.delete(`/api/quote/${quoteId}`),
  getMaterialConfig: () => api.get('/api/quote/config/materials'),
  
  // Payment endpoints
  createPaymentIntent: (data: any) => api.post('/api/payment/create-intent', data),
  createOrder: (data: any) => api.post('/api/payment/create-order', data),
  confirmPayment: (data: any) => api.post('/api/payment/confirm', data),
  getPaymentIntent: (paymentIntentId: string) => api.get(`/api/payment/intent/${paymentIntentId}`),
  cancelPaymentIntent: (paymentIntentId: string) => api.post(`/api/payment/cancel/${paymentIntentId}`),
  getPaymentConfig: () => api.get('/api/payment/config'),
  
  // Order endpoints
  getOrder: (orderId: string) => api.get(`/api/order/${orderId}`),
  listOrders: (params?: any) => api.get('/api/order/', { params }),
  updateOrder: (orderId: string, data: any) => api.put(`/api/order/${orderId}`, data),
  getOrderStats: () => api.get('/api/order/stats/summary'),
};

// Error handling utility
export const handleApiError = (error: AxiosError): string => {
  if (error.response?.data) {
    const errorData = error.response.data as any;
    return errorData.message || errorData.detail || 'An error occurred';
  }
  
  if (error.request) {
    return 'Network error - please check your connection';
  }
  
  return error.message || 'An unexpected error occurred';
};

// File upload utility
export const uploadSTLFiles = async (
  files: File[],
  materials: string[],
  quantities: number[],
  customerEmail?: string,
  onProgress?: (progress: number) => void
) => {
  const formData = new FormData();
  
  // Add files
  files.forEach((file) => {
    formData.append('files', file);
  });
  
  // Add materials
  materials.forEach((material) => {
    formData.append('materials', material);
  });
  
  // Add quantities
  quantities.forEach((quantity) => {
    formData.append('quantities', quantity.toString());
  });
  
  // Add customer email if provided
  if (customerEmail) {
    formData.append('customer_email', customerEmail);
  }
  
  return api.post('/api/quote/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000, // 60 seconds
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
  });
};

// Types for API responses
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
}

export interface ApiError {
  error: string;
  message: string;
  details?: any;
}

export interface QuoteResponse {
  quote_id: string;
  files: STLFileResponse[];
  subtotal: number;
  shipping_cost: number;
  total: number;
  shipping_size: string;
  estimated_shipping_days: number;
  created_at: string;
  expires_at?: string;
  is_valid: boolean;
  customer_email?: string;
}

export interface STLFileResponse {
  filename: string;
  file_size: number;
  volume: number;
  bounding_box: BoundingBox;
  is_watertight: boolean;
  material: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  processed_at: string;
}

export interface BoundingBox {
  min_x: number;
  min_y: number;
  min_z: number;
  max_x: number;
  max_y: number;
  max_z: number;
}

export interface PaymentIntentResponse {
  client_secret: string;
  payment_intent_id: string;
  amount: number;
  currency: string;
}

export interface OrderResponse {
  order_id: string;
  quote: QuoteResponse;
  customer: CustomerResponse;
  payment_intent_id: string;
  payment_status: string;
  amount_paid: number;
  status: string;
  order_notes?: string;
  zoho_sales_order_id?: string;
  zoho_contact_id?: string;
  created_at: string;
  paid_at?: string;
  supplier_notified_at?: string;
  shipped_at?: string;
  delivered_at?: string;
}

export interface CustomerResponse {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  company?: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  state?: string;
  postal_code: string;
  country: string;
  zoho_contact_id?: string;
}