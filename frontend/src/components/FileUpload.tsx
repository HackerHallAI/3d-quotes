import React, { useRef } from 'react';
import { Upload, X, FileText, AlertCircle } from 'lucide-react';
import { useFileUpload, FileWithMetadata } from '@/hooks/useFileUpload';
import { formatFileSize } from '@/utils/validators';

interface FileUploadProps {
  onFilesChange: (files: FileWithMetadata[]) => void;
  disabled?: boolean;
  maxFiles?: number;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onFilesChange,
  disabled = false,
  maxFiles = 10,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const {
    files,
    isDragOver,
    validationErrors,
    addFiles,
    removeFile,
    clearFiles,
    handleDragOver,
    handleDragLeave,
    handleDrop,
  } = useFileUpload();

  // Notify parent component when files change
  React.useEffect(() => {
    onFilesChange(files);
  }, [files, onFilesChange]);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    if (selectedFiles.length > 0) {
      addFiles(selectedFiles);
    }
    // Reset input value to allow selecting the same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUploadClick = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div className="w-full space-y-4">
      {/* Upload Area */}
      <div
        className={`
          file-upload-area
          ${isDragOver ? 'dragover' : ''}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleUploadClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".stl"
          onChange={handleFileInputChange}
          className="hidden"
          disabled={disabled}
        />
        
        <div className="space-y-4">
          <div className="flex justify-center">
            <Upload className="h-12 w-12 text-muted-foreground" />
          </div>
          
          <div className="text-center">
            <p className="text-lg font-medium text-foreground">
              Drop STL files here or click to browse
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              Supports multiple .stl files (max {maxFiles} files, 50MB each)
            </p>
          </div>
          
          <div className="text-xs text-muted-foreground text-center">
            <p>Supported format: STL</p>
            <p>Maximum file size: 50MB per file</p>
          </div>
        </div>
      </div>

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-destructive">
                Upload Error
              </p>
              <ul className="text-sm text-destructive space-y-1">
                {validationErrors.map((error, index) => (
                  <li key={index}>• {error}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium">
              Uploaded Files ({files.length})
            </h3>
            <button
              onClick={clearFiles}
              className="text-sm text-muted-foreground hover:text-destructive transition-colors"
              disabled={disabled}
            >
              Clear All
            </button>
          </div>

          <div className="space-y-2">
            {files.map((fileMetadata) => (
              <FileItem
                key={fileMetadata.id}
                fileMetadata={fileMetadata}
                onRemove={removeFile}
                disabled={disabled}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

interface FileItemProps {
  fileMetadata: FileWithMetadata;
  onRemove: (fileId: string) => void;
  disabled?: boolean;
}

const FileItem: React.FC<FileItemProps> = ({
  fileMetadata,
  onRemove,
  disabled = false,
}) => {
  const { file, id, isProcessing, error } = fileMetadata;

  return (
    <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg border">
      <div className="flex-shrink-0">
        <FileText className="h-5 w-5 text-muted-foreground" />
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium truncate">{file.name}</p>
          {isProcessing && (
            <div className="loading-spinner" />
          )}
        </div>
        
        <div className="flex items-center gap-4 mt-1">
          <p className="text-xs text-muted-foreground">
            {formatFileSize(file.size)}
          </p>
          <p className="text-xs text-muted-foreground">
            {file.type || 'STL File'}
          </p>
        </div>
        
        {error && (
          <p className="text-xs text-destructive mt-1">
            {error}
          </p>
        )}
      </div>
      
      <button
        onClick={() => onRemove(id)}
        className="flex-shrink-0 p-1 hover:bg-destructive/10 rounded transition-colors"
        disabled={disabled || isProcessing}
        title="Remove file"
      >
        <X className="h-4 w-4 text-muted-foreground hover:text-destructive" />
      </button>
    </div>
  );
};

export default FileUpload;