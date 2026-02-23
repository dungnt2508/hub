'use client';

import { useState, useRef } from 'react';
import { Upload, X, File, Loader2 } from 'lucide-react';
import { ArtifactType } from '@gsnake/shared-types';

interface FileUploadProps {
  onUpload: (file: File, artifactType: ArtifactType) => Promise<void>;
  artifactType: ArtifactType;
  accept?: string;
  maxSize?: number; // in MB
  disabled?: boolean;
  label?: string;
  required?: boolean;
}

export default function FileUpload({
  onUpload,
  artifactType,
  accept,
  maxSize = 100,
  disabled = false,
  label,
  required = false,
}: FileUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    // Validate file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxSize) {
      setError(`File size must be less than ${maxSize}MB`);
      return;
    }

    setError(null);
    setUploadedFile(file);
    setUploading(true);

    try {
      await onUpload(file, artifactType);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
      setUploadedFile(null);
    } finally {
      setUploading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (disabled || uploading) return;

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled || uploading) return;

    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleRemove = () => {
    setUploadedFile(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleClick = () => {
    if (!disabled && !uploading) {
      fileInputRef.current?.click();
    }
  };

  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">
          {label}
          {required && <span className="text-red-400 ml-1">*</span>}
        </label>
      )}

      <div
        className={`
          relative border-2 border-dashed rounded-lg p-6 transition-colors
          ${dragActive ? 'border-primary bg-primary/5' : 'border-gray-300 dark:border-slate-700'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-primary/50'}
          ${error ? 'border-red-500 dark:border-red-500' : ''}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleChange}
          disabled={disabled || uploading}
          className="hidden"
        />

        {uploading ? (
          <div className="flex flex-col items-center justify-center gap-2">
            <Loader2 className="h-8 w-8 text-primary animate-spin" />
            <p className="text-sm text-gray-600 dark:text-slate-400">Đang upload...</p>
          </div>
        ) : uploadedFile ? (
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <File className="h-5 w-5 text-gray-400 dark:text-slate-500 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {uploadedFile.name}
                </p>
                <p className="text-xs text-gray-500 dark:text-slate-400">
                  {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            {!disabled && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemove();
                }}
                className="p-1 text-gray-400 hover:text-red-500 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center gap-2">
            <Upload className="h-8 w-8 text-gray-400 dark:text-slate-500" />
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-slate-400">
                <span className="font-medium text-primary">Click để chọn file</span> hoặc kéo thả vào đây
              </p>
              <p className="text-xs text-gray-500 dark:text-slate-500 mt-1">
                Tối đa {maxSize}MB
              </p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <p className="mt-2 text-sm text-red-400 flex items-center gap-1">
          <X className="h-3 w-3" />
          {error}
        </p>
      )}
    </div>
  );
}

