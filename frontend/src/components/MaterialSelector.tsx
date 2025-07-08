import React, { useState, useEffect } from 'react';
import { ChevronDown, Package, Hash, DollarSign } from 'lucide-react';
import { FileWithMetadata } from '@/hooks/useFileUpload';
import { validateQuantity, validateMaterial, formatCurrency } from '@/utils/validators';
import { apiEndpoints, handleApiError } from '@/utils/api';

interface Material {
  type: string;
  name: string;
  rate_per_cm3: number;
  description: string;
}

interface MaterialConfig {
  materials: Material[];
  currency: string;
  minimum_order: number;
}

interface MaterialSelectorProps {
  files: FileWithMetadata[];
  onFileUpdate: (fileId: string, material: string, quantity: number) => void;
  onEstimateUpdate?: (estimate: number) => void;
  disabled?: boolean;
}

const MaterialSelector: React.FC<MaterialSelectorProps> = ({
  files,
  onFileUpdate,
  onEstimateUpdate,
  disabled = false,
}) => {
  const [materialConfig, setMaterialConfig] = useState<MaterialConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load material configuration
  useEffect(() => {
    const loadMaterialConfig = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const response = await apiEndpoints.getMaterialConfig();
        setMaterialConfig(response.data);
      } catch (err: any) {
        const errorMessage = handleApiError(err);
        setError(errorMessage);
        console.error('Failed to load material config:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadMaterialConfig();
  }, []);

  // Calculate estimated total (rough estimate based on material rates)
  useEffect(() => {
    if (!materialConfig || !onEstimateUpdate) return;

    let totalEstimate = 0;
    
    files.forEach(file => {
      const material = materialConfig.materials.find(m => m.type === file.material);
      if (material) {
        // Rough estimate: assume 10cm³ volume per file for estimation
        const estimatedVolume = 10; // cm³
        const materialCost = estimatedVolume * material.rate_per_cm3;
        const withMarkup = materialCost * 1.15; // 15% markup
        totalEstimate += withMarkup * file.quantity;
      }
    });

    // Add estimated shipping
    totalEstimate += 10; // Estimated shipping

    onEstimateUpdate(Math.max(totalEstimate, materialConfig.minimum_order));
  }, [files, materialConfig, onEstimateUpdate]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Material & Quantity Selection</h3>
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-20 bg-muted rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Material & Quantity Selection</h3>
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
          <p className="text-sm text-destructive">
            Failed to load material options: {error}
          </p>
        </div>
      </div>
    );
  }

  if (!materialConfig || files.length === 0) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Material & Quantity Selection</h3>
        <p className="text-sm text-muted-foreground">
          Upload STL files to select materials and quantities.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Material & Quantity Selection</h3>
        <div className="text-sm text-muted-foreground">
          Minimum order: {formatCurrency(materialConfig.minimum_order, materialConfig.currency)}
        </div>
      </div>

      {/* Material Information */}
      <div className="bg-muted/50 rounded-lg p-4">
        <h4 className="text-sm font-medium mb-3">Available Materials</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {materialConfig.materials.map(material => (
            <div key={material.type} className="text-xs">
              <div className="font-medium">{material.name}</div>
              <div className="text-muted-foreground">
                {formatCurrency(material.rate_per_cm3, materialConfig.currency)}/cm³
              </div>
              <div className="text-muted-foreground mt-1">
                {material.description}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* File Material Selectors */}
      <div className="space-y-3">
        {files.map(file => (
          <FileMaterialSelector
            key={file.id}
            file={file}
            materials={materialConfig.materials}
            currency={materialConfig.currency}
            onUpdate={onFileUpdate}
            disabled={disabled}
          />
        ))}
      </div>
    </div>
  );
};

interface FileMaterialSelectorProps {
  file: FileWithMetadata;
  materials: Material[];
  currency: string;
  onUpdate: (fileId: string, material: string, quantity: number) => void;
  disabled?: boolean;
}

const FileMaterialSelector: React.FC<FileMaterialSelectorProps> = ({
  file,
  materials,
  currency,
  onUpdate,
  disabled = false,
}) => {
  const [quantity, setQuantity] = useState(file.quantity);
  const [material, setMaterial] = useState(file.material);
  const [quantityError, setQuantityError] = useState<string | null>(null);

  // Update parent when values change
  useEffect(() => {
    const quantityValidation = validateQuantity(quantity);
    const materialValidation = validateMaterial(material);
    
    if (quantityValidation.isValid && materialValidation.isValid) {
      onUpdate(file.id, material, quantity);
      setQuantityError(null);
    } else {
      setQuantityError(quantityValidation.errors[0] || materialValidation.errors[0]);
    }
  }, [quantity, material, file.id, onUpdate]);

  const handleQuantityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value) || 1;
    setQuantity(value);
  };

  const handleMaterialChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setMaterial(e.target.value);
  };

  const selectedMaterial = materials.find(m => m.type === material);

  return (
    <div className="quote-card">
      <div className="space-y-4">
        {/* File Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Package className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="font-medium text-sm">{file.file.name}</p>
              <p className="text-xs text-muted-foreground">
                {(file.file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>
        </div>

        {/* Material and Quantity Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Material Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <Package className="h-3 w-3" />
              Material
            </label>
            <div className="relative">
              <select
                value={material}
                onChange={handleMaterialChange}
                disabled={disabled}
                className="w-full appearance-none bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {materials.map(mat => (
                  <option key={mat.type} value={mat.type}>
                    {mat.name} - {formatCurrency(mat.rate_per_cm3, currency)}/cm³
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none" />
            </div>
            {selectedMaterial && (
              <p className="text-xs text-muted-foreground">
                {selectedMaterial.description}
              </p>
            )}
          </div>

          {/* Quantity Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <Hash className="h-3 w-3" />
              Quantity
            </label>
            <input
              type="number"
              min="1"
              max="1000"
              value={quantity}
              onChange={handleQuantityChange}
              disabled={disabled}
              className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
              placeholder="Enter quantity"
            />
            {quantityError && (
              <p className="text-xs text-destructive">{quantityError}</p>
            )}
          </div>
        </div>

        {/* Estimated Cost Preview */}
        {selectedMaterial && quantity > 0 && (
          <div className="bg-muted/50 rounded-md p-3">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <DollarSign className="h-3 w-3" />
              <span>Estimated cost will be calculated after upload</span>
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Base rate: {formatCurrency(selectedMaterial.rate_per_cm3, currency)}/cm³ × {quantity} units
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MaterialSelector;