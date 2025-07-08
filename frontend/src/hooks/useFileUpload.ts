import { useState, useCallback } from 'react';
import { validateMultipleSTLFiles, ValidationResult } from '@/utils/validators';

export interface FileWithMetadata {
  file: File;
  id: string;
  material: string;
  quantity: number;
  isProcessing?: boolean;
  error?: string;
}

export interface UseFileUploadReturn {
  files: FileWithMetadata[];
  isDragOver: boolean;
  isUploading: boolean;
  uploadProgress: number;
  validationErrors: string[];
  addFiles: (newFiles: File[]) => void;
  removeFile: (fileId: string) => void;
  updateFileMaterial: (fileId: string, material: string) => void;
  updateFileQuantity: (fileId: string, quantity: number) => void;
  clearFiles: () => void;
  handleDragOver: (e: React.DragEvent) => void;
  handleDragLeave: (e: React.DragEvent) => void;
  handleDrop: (e: React.DragEvent) => void;
  resetUploadState: () => void;
}

export const useFileUpload = (): UseFileUploadReturn => {
  const [files, setFiles] = useState<FileWithMetadata[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  // Generate unique ID for files
  const generateFileId = useCallback(() => {
    return `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Add files with validation
  const addFiles = useCallback((newFiles: File[]) => {
    // Validate new files
    const validation = validateMultipleSTLFiles(newFiles);
    
    if (!validation.isValid) {
      setValidationErrors(validation.errors);
      return;
    }

    // Clear previous validation errors
    setValidationErrors([]);

    // Create file metadata
    const newFileMetadata: FileWithMetadata[] = newFiles.map(file => ({
      file,
      id: generateFileId(),
      material: 'PA12_GREY', // Default material
      quantity: 1, // Default quantity
    }));

    // Check for total file limit (including existing files)
    setFiles(prevFiles => {
      const totalFiles = prevFiles.length + newFileMetadata.length;
      
      if (totalFiles > 10) {
        setValidationErrors(['Maximum 10 files allowed']);
        return prevFiles;
      }

      // Check for duplicate filenames
      const existingNames = prevFiles.map(f => f.file.name);
      const duplicates = newFileMetadata.filter(f => 
        existingNames.includes(f.file.name)
      );

      if (duplicates.length > 0) {
        setValidationErrors([
          `Duplicate files: ${duplicates.map(f => f.file.name).join(', ')}`
        ]);
        return prevFiles;
      }

      return [...prevFiles, ...newFileMetadata];
    });
  }, [generateFileId]);

  // Remove file
  const removeFile = useCallback((fileId: string) => {
    setFiles(prevFiles => prevFiles.filter(f => f.id !== fileId));
    setValidationErrors([]);
  }, []);

  // Update file material
  const updateFileMaterial = useCallback((fileId: string, material: string) => {
    setFiles(prevFiles =>
      prevFiles.map(f =>
        f.id === fileId ? { ...f, material } : f
      )
    );
  }, []);

  // Update file quantity
  const updateFileQuantity = useCallback((fileId: string, quantity: number) => {
    setFiles(prevFiles =>
      prevFiles.map(f =>
        f.id === fileId ? { ...f, quantity } : f
      )
    );
  }, []);

  // Clear all files
  const clearFiles = useCallback(() => {
    setFiles([]);
    setValidationErrors([]);
    setUploadProgress(0);
    setIsUploading(false);
  }, []);

  // Drag and drop handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    
    // Filter only STL files
    const stlFiles = droppedFiles.filter(file => 
      file.name.toLowerCase().endsWith('.stl')
    );

    if (stlFiles.length !== droppedFiles.length) {
      setValidationErrors(['Only STL files are allowed']);
      return;
    }

    addFiles(stlFiles);
  }, [addFiles]);

  // Reset upload state
  const resetUploadState = useCallback(() => {
    setIsUploading(false);
    setUploadProgress(0);
  }, []);

  return {
    files,
    isDragOver,
    isUploading,
    uploadProgress,
    validationErrors,
    addFiles,
    removeFile,
    updateFileMaterial,
    updateFileQuantity,
    clearFiles,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    resetUploadState,
  };
};