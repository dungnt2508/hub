'use client';

import { FileText, Save, X, AlertCircle } from 'lucide-react';
import { useState } from 'react';

interface QueryStep {
  stepNumber: number;
  purpose: string;
  description?: string;
  readOnly: boolean;
  query: string;
}

interface QueryEditorProps {
  steps: QueryStep[];
  queryOverrides: Record<string, string>;
  onQueryOverridesChange: (overrides: Record<string, string>) => void;
}

export function QueryEditor({
  steps,
  queryOverrides,
  onQueryOverridesChange,
}: QueryEditorProps) {
  const [editingStep, setEditingStep] = useState<number | null>(null);
  const [editValue, setEditValue] = useState<string>('');

  const handleEdit = (step: QueryStep) => {
    if (step.readOnly) return;
    
    const stepKey = `step_${step.stepNumber}`;
    setEditValue(queryOverrides[stepKey] || step.query);
    setEditingStep(step.stepNumber);
  };

  const handleSave = (stepNumber: number) => {
    const stepKey = `step_${stepNumber}`;
    const step = steps.find((s) => s.stepNumber === stepNumber);
    
    if (!step) return;
    
    // If edit value equals original, remove override
    if (editValue.trim() === step.query.trim()) {
      const newOverrides = { ...queryOverrides };
      delete newOverrides[stepKey];
      onQueryOverridesChange(newOverrides);
    } else {
      onQueryOverridesChange({
        ...queryOverrides,
        [stepKey]: editValue.trim(),
      });
    }
    
    setEditingStep(null);
    setEditValue('');
  };

  const handleCancel = () => {
    setEditingStep(null);
    setEditValue('');
  };

  const handleReset = (stepNumber: number) => {
    const stepKey = `step_${stepNumber}`;
    const newOverrides = { ...queryOverrides };
    delete newOverrides[stepKey];
    onQueryOverridesChange(newOverrides);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileText className="h-5 w-5 text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Query Editor
          </h3>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Click on a query to edit (read-only queries cannot be edited)
        </p>
      </div>

      <div className="space-y-3">
        {steps.map((step) => {
          const stepKey = `step_${step.stepNumber}`;
          const isOverridden = stepKey in queryOverrides;
          const isEditing = editingStep === step.stepNumber;
          const displayQuery = isOverridden ? queryOverrides[stepKey] : step.query;

          return (
            <div
              key={step.stepNumber}
              className={`border rounded-lg ${
                isOverridden
                  ? 'border-yellow-300 dark:border-yellow-700 bg-yellow-50/50 dark:bg-yellow-900/10'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
              }`}
            >
              {/* Header */}
              <div className="p-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-gray-900 dark:text-white">
                        Step {step.stepNumber}
                      </span>
                      {step.readOnly && (
                        <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 rounded">
                          Read-only
                        </span>
                      )}
                      {isOverridden && (
                        <span className="text-xs px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400 rounded">
                          Modified
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {step.purpose}
                    </p>
                    {step.description && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {step.description}
                      </p>
                    )}
                  </div>
                  {!step.readOnly && (
                    <div className="flex items-center space-x-2 ml-4">
                      {isOverridden && !isEditing && (
                        <button
                          onClick={() => handleReset(step.stepNumber)}
                          className="text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-600 rounded"
                        >
                          Reset
                        </button>
                      )}
                      {!isEditing && (
                        <button
                          onClick={() => handleEdit(step)}
                          className="text-xs text-primary-600 hover:text-primary-700 px-2 py-1 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded"
                        >
                          Edit
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Query Display/Editor */}
              <div className="p-4">
                {isEditing ? (
                  <div className="space-y-3">
                    <textarea
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      rows={12}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="Enter SQL query..."
                    />
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        onClick={handleCancel}
                        className="flex items-center space-x-1 px-3 py-1.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                      >
                        <X className="h-4 w-4" />
                        <span>Cancel</span>
                      </button>
                      <button
                        onClick={() => handleSave(step.stepNumber)}
                        className="flex items-center space-x-1 px-3 py-1.5 text-sm bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
                      >
                        <Save className="h-4 w-4" />
                        <span>Save</span>
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="bg-gray-900 dark:bg-gray-950 rounded-lg p-4 overflow-x-auto">
                      <pre className="text-sm font-mono text-gray-100 whitespace-pre-wrap">
                        {displayQuery || <span className="text-gray-500">No query available</span>}
                      </pre>
                    </div>
                    {step.readOnly && (
                      <div className="flex items-start space-x-2 text-xs text-gray-500 dark:text-gray-400">
                        <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                        <span>This query is read-only and cannot be modified</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

