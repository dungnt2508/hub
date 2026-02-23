'use client';

import { useState, useEffect } from 'react';
import FileUpload from './FileUpload';
import artifactService from '@/services/artifact.service';
import workflowService from '@/services/workflow.service';
import { ArtifactType } from '@gsnake/shared-types';
import { AlertCircle, Check, Loader2 } from 'lucide-react';

interface WorkflowUploadSectionProps {
  productId: string;
  onFilesUploaded?: (files: { workflow?: string; readme?: string; envExample?: string }) => void;
}

export default function WorkflowUploadSection({
  productId,
  onFilesUploaded,
}: WorkflowUploadSectionProps) {
  const [uploading, setUploading] = useState(false);
  const [workflowFile, setWorkflowFile] = useState<string | null>(null);
  const [readmeFile, setReadmeFile] = useState<string | null>(null);
  const [envExampleFile, setEnvExampleFile] = useState<string | null>(null);
  const [n8nVersion, setN8nVersion] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Load existing artifacts
  useEffect(() => {
    loadArtifacts();
  }, [productId]);

  const loadArtifacts = async () => {
    try {
      const artifacts = await artifactService.getArtifacts(productId);
      const workflow = artifacts.find(a => a.artifactType === 'workflow_json');
      const readme = artifacts.find(a => a.artifactType === 'readme');
      const envExample = artifacts.find(a => a.artifactType === 'env_example');

      const wfUrl = workflow ? (workflow as any).fileUrl || (workflow as any).file_url : null;
      const readmeUrl = readme ? (readme as any).fileUrl || (readme as any).file_url : null;
      const envUrl = envExample ? (envExample as any).fileUrl || (envExample as any).file_url : null;

      if (wfUrl) setWorkflowFile(wfUrl);
      if (readmeUrl) setReadmeFile(readmeUrl);
      if (envUrl) setEnvExampleFile(envUrl);

      // Đẩy lên parent để cập nhật form state nếu sản phẩm đã có artifact sẵn
      if (onFilesUploaded) {
        onFilesUploaded({
          workflow: wfUrl || undefined,
          readme: readmeUrl || undefined,
          envExample: envUrl || undefined,
        });
      }
    } catch (err) {
      console.error('Failed to load artifacts:', err);
    }
  };

  const handleUpload = async (file: File, artifactType: ArtifactType) => {
    setUploading(true);
    setError(null);

    try {
      const artifact = await artifactService.uploadArtifact(productId, file, artifactType);
      const fileUrl = (artifact as any).fileUrl || (artifact as any).file_url;

      // Update state based on artifact type
      if (artifactType === 'workflow_json') {
        setWorkflowFile(fileUrl);
        
        // Auto-save workflow details if n8n version is set
        if (n8nVersion) {
          await workflowService.createOrUpdateWorkflowDetails(productId, {
            workflowJsonUrl: fileUrl,
            n8nVersion: n8nVersion,
          });
        }
      } else if (artifactType === 'readme') {
        setReadmeFile(fileUrl);
      } else if (artifactType === 'env_example') {
        setEnvExampleFile(fileUrl);
      }

      // Notify parent
      if (onFilesUploaded) {
        onFilesUploaded({
          workflow: artifactType === 'workflow_json' ? fileUrl : workflowFile || undefined,
          readme: artifactType === 'readme' ? fileUrl : readmeFile || undefined,
          envExample: artifactType === 'env_example' ? fileUrl : envExampleFile || undefined,
        });
      }
    } catch (err: any) {
      setError(err.message || 'Upload failed');
      throw err;
    } finally {
      setUploading(false);
    }
  };

  const handleN8nVersionChange = async (version: string) => {
    setN8nVersion(version);
    
    // Auto-save if workflow file exists
    if (workflowFile && version) {
      try {
        await workflowService.createOrUpdateWorkflowDetails(productId, {
          workflowJsonUrl: workflowFile,
          n8nVersion: version,
        });
      } catch (err) {
        console.error('Failed to save n8n version:', err);
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Workflow Files
        </h3>

        <div className="space-y-4">
          {/* n8n Version */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">
              n8n Version <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={n8nVersion}
              onChange={(e) => handleN8nVersionChange(e.target.value)}
              placeholder="Ví dụ: 1.0.0"
              className="w-full rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
            />
          </div>

          {/* Workflow JSON */}
          <FileUpload
            onUpload={handleUpload}
            artifactType="workflow_json"
            accept=".json,application/json"
            maxSize={10}
            label="Workflow JSON File"
            required
            disabled={uploading}
          />
          {workflowFile && (
            <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
              <Check className="h-4 w-4" />
              <span>Workflow file đã được upload</span>
            </div>
          )}

          {/* README */}
          <FileUpload
            onUpload={handleUpload}
            artifactType="readme"
            accept=".md,.txt,text/markdown,text/plain"
            maxSize={5}
            label="README.md (Optional)"
            disabled={uploading}
          />
          {readmeFile && (
            <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
              <Check className="h-4 w-4" />
              <span>README file đã được upload</span>
            </div>
          )}

          {/* .env.example */}
          <FileUpload
            onUpload={handleUpload}
            artifactType="env_example"
            accept=".env,.txt,text/plain"
            maxSize={1}
            label=".env.example (Optional)"
            disabled={uploading}
          />
          {envExampleFile && (
            <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
              <Check className="h-4 w-4" />
              <span>.env.example file đã được upload</span>
            </div>
          )}
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2 text-sm text-red-800 dark:text-red-200">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}
      </div>
    </div>
  );
}

