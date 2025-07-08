// Frontend validation utilities

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

// File validation
export const validateSTLFile = (file: File): ValidationResult => {
  const errors: string[] = [];
  
  // Check file extension
  if (!file.name.toLowerCase().endsWith('.stl')) {
    errors.push('File must be an STL file (.stl extension)');
  }
  
  // Check file size (50MB max)
  const maxSize = 50 * 1024 * 1024; // 50MB in bytes
  if (file.size > maxSize) {
    errors.push(`File size must be less than 50MB (current: ${formatFileSize(file.size)})`);
  }
  
  // Check if file is empty
  if (file.size === 0) {
    errors.push('File cannot be empty');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};

export const validateMultipleSTLFiles = (files: File[]): ValidationResult => {
  const errors: string[] = [];
  
  // Check number of files
  if (files.length === 0) {
    errors.push('At least one file is required');
  }
  
  if (files.length > 10) {
    errors.push('Maximum 10 files allowed');
  }
  
  // Validate each file
  files.forEach((file, index) => {
    const fileResult = validateSTLFile(file);
    if (!fileResult.isValid) {
      errors.push(`File ${index + 1} (${file.name}): ${fileResult.errors.join(', ')}`);
    }
  });
  
  // Check for duplicate filenames
  const filenames = files.map(f => f.name);
  const duplicates = filenames.filter((name, index) => filenames.indexOf(name) !== index);
  if (duplicates.length > 0) {
    errors.push(`Duplicate filenames: ${duplicates.join(', ')}`);
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};

// Email validation
export const validateEmail = (email: string): ValidationResult => {
  const errors: string[] = [];
  
  if (!email) {
    errors.push('Email is required');
  } else {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      errors.push('Please enter a valid email address');
    }
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};

// Phone validation (basic)
export const validatePhone = (phone: string): ValidationResult => {
  const errors: string[] = [];
  
  if (phone) {
    // Remove all non-digit characters for validation
    const digitsOnly = phone.replace(/\D/g, '');
    if (digitsOnly.length < 7 || digitsOnly.length > 15) {
      errors.push('Phone number must be between 7 and 15 digits');
    }
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};

// Postal code validation (NZ format)
export const validatePostalCode = (postalCode: string, country: string = 'NZ'): ValidationResult => {
  const errors: string[] = [];
  
  if (!postalCode) {
    errors.push('Postal code is required');
  } else if (country === 'NZ') {
    // New Zealand postal codes are 4 digits
    if (!/^\d{4}$/.test(postalCode)) {
      errors.push('New Zealand postal code must be 4 digits');
    }
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};

// Customer information validation
export interface CustomerInfo {
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  company?: string;
  addressLine1: string;
  addressLine2?: string;
  city: string;
  state?: string;
  postalCode: string;
  country: string;
}

export const validateCustomerInfo = (customerInfo: CustomerInfo): ValidationResult => {
  const errors: string[] = [];
  
  // Required fields
  if (!customerInfo.firstName.trim()) {
    errors.push('First name is required');
  }
  
  if (!customerInfo.lastName.trim()) {
    errors.push('Last name is required');
  }
  
  // Email validation
  const emailResult = validateEmail(customerInfo.email);
  if (!emailResult.isValid) {
    errors.push(...emailResult.errors);
  }
  
  // Phone validation (optional)
  if (customerInfo.phone) {
    const phoneResult = validatePhone(customerInfo.phone);
    if (!phoneResult.isValid) {
      errors.push(...phoneResult.errors);
    }
  }
  
  // Address validation
  if (!customerInfo.addressLine1.trim()) {
    errors.push('Address is required');
  }
  
  if (!customerInfo.city.trim()) {
    errors.push('City is required');
  }
  
  if (!customerInfo.postalCode.trim()) {
    errors.push('Postal code is required');
  } else {
    const postalResult = validatePostalCode(customerInfo.postalCode, customerInfo.country);
    if (!postalResult.isValid) {
      errors.push(...postalResult.errors);
    }
  }
  
  if (!customerInfo.country.trim()) {
    errors.push('Country is required');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};

// Quantity validation
export const validateQuantity = (quantity: number): ValidationResult => {
  const errors: string[] = [];
  
  if (!Number.isInteger(quantity) || quantity < 1) {
    errors.push('Quantity must be a positive integer');
  }
  
  if (quantity > 1000) {
    errors.push('Quantity cannot exceed 1000');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};

// Material validation
export const validateMaterial = (material: string): ValidationResult => {
  const validMaterials = ['PA12_GREY', 'PA12_BLACK', 'PA12_GB'];
  const errors: string[] = [];
  
  if (!material) {
    errors.push('Material selection is required');
  } else if (!validMaterials.includes(material)) {
    errors.push('Invalid material selection');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};

// Utility functions
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const formatCurrency = (amount: number, currency: string = 'USD'): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
  }).format(amount);
};

export const formatVolume = (volumeMm3: number): string => {
  const volumeCm3 = volumeMm3 / 1000;
  return `${volumeCm3.toFixed(2)} cm³`;
};

export const formatDimensions = (dimensions: [number, number, number]): string => {
  return `${dimensions[0].toFixed(1)} × ${dimensions[1].toFixed(1)} × ${dimensions[2].toFixed(1)} mm`;
};

// Debounce utility for input validation
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};