// agno-zendesk/frontend__backup2/protocol/uiInstructionRegistry.tsx

import React, { useState, useRef, useEffect, FormEvent, ChangeEvent } from "react";
import type { UIInstruction, UIInstructionType } from "./uiInstruction";
import { uiInstructionStateManager, UIInstructionState, queueInstruction } from "./uiInstructionState";

// --- Bug Report Schema TypeScript Interfaces ---

export interface BugReport {
  reporterName: string;
  reporterEmail: string;
  appVersion: string;
  deviceOS: string;
  stepsToReproduce: string;
  expectedResult: string;
  actualResult: string;
  severity: "Critical" | "High" | "Medium" | "Low";
  hasAttachments?: "yes" | "no";
  attachments?: string[];
  gdprConsent: boolean;
}

// --- Parameter Type Definitions ---

// Common response handler type
export type InstructionResponseHandler = (data: any) => void;

// Component parameter interface with progress tracking
interface ComponentProps {
  params: any;
  onResponse?: InstructionResponseHandler;
  progress?: string;
}

// File Upload Parameters
export interface FileUploadParams {
  max_files: number;
  max_size_mb: number;
  accepted_types: string[];
  upload_url: string;
  field_name?: string;
  progress?: string;
}

// Email Request Parameters
export interface EmailRequestParams {
  prompt: string;
  validation_regex?: string;
  placeholder?: string;
  field_name?: string;
  progress?: string;
}

// Form Field Parameters
export interface FormField {
  name: string;
  label: string;
  type: string;
  required?: boolean;
  placeholder?: string;
  options?: { label: string; value: string }[];
}

// Form Display Parameters
export interface FormParams {
  fields: FormField[];
  submit_label?: string;
  title?: string;
  description?: string;
  progress?: string;
}

// Auth Prompt Parameters
export interface AuthPromptParams {
  prompt: string;
  auth_type: "password" | "pin" | "otp";
  title?: string;
  description?: string;
  field_name?: string;
  progress?: string;
}

// Selection Menu Parameters
export interface SelectionMenuParams {
  prompt: string;
  options: { label: string; value: string }[];
  title?: string;
  multi_select?: boolean;
  field_name?: string;
  progress?: string;
}

// Progress Indicator Parameters
export interface ProgressIndicatorParams {
  message: string;
  progress_percent?: number;
  is_indeterminate?: boolean;
  field_name?: string;
}

// Confirmation Dialog Parameters
export interface ConfirmationDialogParams {
  title: string;
  message: string;
  confirm_label?: string;
  cancel_label?: string;
  field_name?: string;
  progress?: string;
}

// --- UI Component Handlers ---

// File Upload Widget - Supports file attachment flow
export const FileUploadWidget: React.FC<ComponentProps> = ({ params, onResponse, progress }) => {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [uploaded, setUploaded] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    setError(null);
    if (!e.target.files?.length) return;
    
    const selectedFiles = Array.from(e.target.files);
    
    // Validate file count
    if (selectedFiles.length > params.max_files) {
      setError(`Maximum ${params.max_files} file(s) allowed`);
      return;
    }
    
    // Validate file sizes
    const oversizedFiles = selectedFiles.filter(
      file => file.size > params.max_size_mb * 1024 * 1024
    );
    if (oversizedFiles.length > 0) {
      setError(`Some files exceed the maximum size of ${params.max_size_mb}MB`);
      return;
    }
    
    setFiles(selectedFiles);
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;
    
    setUploading(true);
    setUploadProgress(0);
    setError(null);
    
    const uploadedUrls: string[] = [];
    
    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // Create form data for the file
        const formData = new FormData();
        formData.append('file', file);
        
        // Upload to the provided URL
        const uploadResponse = await fetch(params.upload_url, {
          method: 'POST',
          body: formData
        });
        
        if (!uploadResponse.ok) {
          throw new Error(`Failed to upload ${file.name}: ${uploadResponse.statusText}`);
        }
        
        const result = await uploadResponse.json();
        uploadedUrls.push(result.file_url);
        
        // Update progress after each file
        setUploadProgress(Math.round((i + 1) / files.length * 100));
      }
      
      setUploaded(uploadedUrls);
      
      // Call response handler if provided
      if (onResponse) {
        onResponse({
          field: params.field_name || "attachments",
          value: uploadedUrls,
          files_uploaded: files.length,
          urls: uploadedUrls
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const reset = () => {
    setFiles([]);
    setUploadProgress(0);
    setError(null);
    setUploaded([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="p-4 border rounded bg-[#181c2a] text-white">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-bold">Upload Files</h3>
        {progress && (
          <span className="text-sm bg-[#3d3d5c] px-2 py-1 rounded">Progress: {progress}</span>
        )}
      </div>
      
      <p>
        Max files: {params.max_files}, Max size: {params.max_size_mb}MB
        <br />
        Accepted types: {Array.isArray(params.accepted_types) ? params.accepted_types.join(", ") : "All files"}
      </p>
      
      {error && (
        <div className="mt-2 p-2 bg-red-700 rounded text-white">
          {error}
        </div>
      )}
      
      {uploaded.length > 0 ? (
        <div className="mt-2">
          <p className="font-semibold text-green-400">
            {uploaded.length} file(s) uploaded successfully!
          </p>
          <div className="mt-2">
            <ul className="text-sm space-y-1">
              {uploaded.map((url, idx) => (
                <li key={idx} className="flex items-center">
                  <span className="inline-block w-4 h-4 mr-2">✓</span>
                  {url.split('/').pop()}
                </li>
              ))}
            </ul>
          </div>
          <button 
            className="mt-3 bg-[#2c2c44] hover:bg-[#3d3d5c] transition-colors text-white px-4 py-2 rounded"
            onClick={reset}
          >
            Upload More Files
          </button>
        </div>
      ) : (
        <div className="mt-4">
          <input
            type="file"
            multiple
            onChange={handleFileChange}
            ref={fileInputRef}
            className="block w-full text-white file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-[#3d3d5c] file:text-white hover:file:bg-[#4d4d6c]"
            accept={params.accepted_types?.join(',')}
          />
          
          {files.length > 0 && (
            <div className="mt-2">
              <p>{files.length} file(s) selected</p>
              <ul className="text-sm mt-1">
                {files.map((file, idx) => (
                  <li key={idx}>{file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)</li>
                ))}
              </ul>
              <button
                className="mt-3 bg-[#6d4aff] hover:bg-[#5d3aef] transition-colors text-white px-4 py-2 rounded disabled:opacity-50"
                onClick={uploadFiles}
                disabled={uploading}
              >
                {uploading ? `Uploading... ${uploadProgress}%` : 'Upload Files'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Email Request Widget
export const EmailRequestWidget: React.FC<ComponentProps> = ({ params, onResponse, progress }) => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    
    setError(null);
    
    // Validate email if regex provided
    if (params.validation_regex) {
      const regex = new RegExp(params.validation_regex);
      if (!regex.test(email)) {
        setError('Please enter a valid email address');
        return;
      }
    }
    
    if (onResponse) {
      onResponse({
        field: params.field_name || "email",
        value: email
      });
      setSubmitted(true);
    }
  };

  if (submitted) {
    return (
      <div className="p-4 border rounded bg-[#181c2a] text-white">
        <p className="font-semibold text-green-400">
          Email address submitted successfully: {email}
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 border rounded bg-[#181c2a] text-white">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-bold">Email Verification</h3>
        {progress && (
          <span className="text-sm bg-[#3d3d5c] px-2 py-1 rounded">Progress: {progress}</span>
        )}
      </div>
      
      <p className="mb-4">{params.prompt || "Please enter your email address:"}</p>
      
      {error && (
        <div className="mb-4 p-2 bg-red-700 rounded text-white">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder={params.placeholder || "Email address"}
          className="w-full p-2 rounded bg-[#121833] border border-[#1e2642] text-white focus:outline-none focus:ring-2 focus:ring-[#6d4aff]"
          required
        />
        <button
          type="submit"
          className="mt-3 bg-[#6d4aff] hover:bg-[#5d3aef] transition-colors text-white px-4 py-2 rounded disabled:opacity-50"
          disabled={!email.trim()}
        >
          Submit
        </button>
      </form>
    </div>
  );
};

// Form Display Widget
export const FormDisplayWidget: React.FC<ComponentProps> = ({ params, onResponse, progress }) => {
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);
  
  const handleInputChange = (name: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error for this field if any
    if (errors[name]) {
      setErrors(prev => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }
  };
  
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    
    // Validate required fields
    const newErrors: Record<string, string> = {};
    params.fields.forEach(field => {
      if (field.required && !formData[field.name]) {
        newErrors[field.name] = `${field.label} is required`;
      }
    });
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    if (onResponse) {
      onResponse({
        formData
      });
      setSubmitted(true);
    }
  };
  
  const renderField = (field: FormField) => {
    const { name, label, type, required, placeholder } = field;
    
    switch (type.toLowerCase()) {
      case 'text':
      case 'email':
      case 'tel':
      case 'url':
      case 'number':
      case 'password':
        return (
          <div key={name} className="mb-4">
            <label className="block mb-1 font-medium">{label}{required && ' *'}</label>
            <input
              type={type.toLowerCase()}
              name={name}
              value={formData[name] || ''}
              onChange={(e) => handleInputChange(name, e.target.value)}
              placeholder={placeholder}
              className="w-full p-2 rounded bg-[#121833] border border-[#1e2642] text-white focus:outline-none focus:ring-2 focus:ring-[#6d4aff]"
              required={required}
            />
            {errors[name] && <p className="mt-1 text-red-400 text-sm">{errors[name]}</p>}
          </div>
        );
      
      case 'textarea':
        return (
          <div key={name} className="mb-4">
            <label className="block mb-1 font-medium">{label}{required && ' *'}</label>
            <textarea
              name={name}
              value={formData[name] || ''}
              onChange={(e) => handleInputChange(name, e.target.value)}
              placeholder={placeholder}
              className="w-full p-2 rounded bg-[#121833] border border-[#1e2642] text-white focus:outline-none focus:ring-2 focus:ring-[#6d4aff] min-h-[100px]"
              required={required}
            />
            {errors[name] && <p className="mt-1 text-red-400 text-sm">{errors[name]}</p>}
          </div>
        );
      
      case 'select':
        return (
          <div key={name} className="mb-4">
            <label className="block mb-1 font-medium">{label}{required && ' *'}</label>
            <select
              name={name}
              value={formData[name] || ''}
              onChange={(e) => handleInputChange(name, e.target.value)}
              className="w-full p-2 rounded bg-[#121833] border border-[#1e2642] text-white focus:outline-none focus:ring-2 focus:ring-[#6d4aff]"
              required={required}
            >
              <option value="">Select an option</option>
              {field.options?.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {errors[name] && <p className="mt-1 text-red-400 text-sm">{errors[name]}</p>}
          </div>
        );
      
      case 'checkbox':
        return (
          <div key={name} className="mb-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                name={name}
                checked={formData[name] || false}
                onChange={(e) => handleInputChange(name, e.target.checked)}
                className="mr-2 rounded bg-[#121833] border border-[#1e2642] text-[#6d4aff] focus:ring-[#6d4aff]"
                required={required}
              />
              <span>{label}{required && ' *'}</span>
            </label>
            {errors[name] && <p className="mt-1 text-red-400 text-sm">{errors[name]}</p>}
          </div>
        );
      
      case 'radio':
        return (
          <div key={name} className="mb-4">
            <p className="block mb-1 font-medium">{label}{required && ' *'}</p>
            <div className="space-y-1">
              {field.options?.map(option => (
                <label key={option.value} className="flex items-center">
                  <input
                    type="radio"
                    name={name}
                    value={option.value}
                    checked={formData[name] === option.value}
                    onChange={(e) => handleInputChange(name, e.target.value)}
                    className="mr-2"
                    required={required}
                  />
                  <span>{option.label}</span>
                </label>
              ))}
            </div>
            {errors[name] && <p className="mt-1 text-red-400 text-sm">{errors[name]}</p>}
          </div>
        );
      
      default:
        return null;
    }
  };
  
  if (submitted) {
    return (
      <div className="p-4 border rounded bg-[#181c2a] text-white">
        <p className="font-semibold text-green-400">Form submitted successfully!</p>
      </div>
    );
  }
  
  return (
    <div className="p-4 border rounded bg-[#181c2a] text-white">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-bold">{params.title || "Form"}</h3>
        {progress && (
          <span className="text-sm bg-[#3d3d5c] px-2 py-1 rounded">Progress: {progress}</span>
        )}
      </div>
      
      {params.description && <p className="mb-4">{params.description}</p>}
      
      <form onSubmit={handleSubmit}>
        {params.fields.map(renderField)}
        
        <button
          type="submit"
          className="mt-3 bg-[#6d4aff] hover:bg-[#5d3aef] transition-colors text-white px-4 py-2 rounded disabled:opacity-50"
        >
          {params.submit_label || "Submit"}
        </button>
      </form>
    </div>
  );
};

// Auth Prompt Widget
export const AuthPromptWidget: React.FC<ComponentProps> = ({ params, onResponse, progress }) => {
  const [value, setValue] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    
    setError(null);
    
    if (!value.trim()) {
      setError('This field is required');
      return;
    }
    
    if (onResponse) {
      onResponse({
        field: params.field_name || "auth_value",
        value: value
      });
      setSubmitted(true);
    }
  };

  const getInputType = () => {
    switch (params.auth_type) {
      case 'password': return 'password';
      case 'pin': return 'number';
      case 'otp': return 'text';
      default: return 'text';
    }
  };

  if (submitted) {
    return (
      <div className="p-4 border rounded bg-[#181c2a] text-white">
        <p className="font-semibold text-green-400">
          Authentication submitted successfully
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 border rounded bg-[#181c2a] text-white">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-bold">{params.title || "Authentication Required"}</h3>
        {progress && (
          <span className="text-sm bg-[#3d3d5c] px-2 py-1 rounded">Progress: {progress}</span>
        )}
      </div>
      
      {params.description && <p className="mb-4">{params.description}</p>}
      
      <p className="mb-4">{params.prompt || "Please enter your authentication credentials:"}</p>
      
      {error && (
        <div className="mb-4 p-2 bg-red-700 rounded text-white">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <input
          type={getInputType()}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="w-full p-2 rounded bg-[#121833] border border-[#1e2642] text-white focus:outline-none focus:ring-2 focus:ring-[#6d4aff]"
          required
          pattern={params.auth_type === 'pin' ? '[0-9]*' : undefined}
          autoComplete={params.auth_type === 'password' ? 'current-password' : 'one-time-code'}
        />
        <button
          type="submit"
          className="mt-3 bg-[#6d4aff] hover:bg-[#5d3aef] transition-colors text-white px-4 py-2 rounded disabled:opacity-50"
          disabled={!value.trim()}
        >
          Submit
        </button>
      </form>
    </div>
  );
};

// Selection Menu Widget
export const SelectionMenuWidget: React.FC<ComponentProps> = ({ params, onResponse, progress }) => {
  const [selected, setSelected] = useState<string[]>([]);
  const [submitted, setSubmitted] = useState(false);

  const handleSelect = (value: string) => {
    if (params.multi_select) {
      // Toggle selection for multi-select
      if (selected.includes(value)) {
        setSelected(selected.filter(v => v !== value));
      } else {
        setSelected([...selected, value]);
      }
    } else {
      // Single select
      setSelected([value]);
    }
  };

  const handleSubmit = () => {
    if (selected.length === 0) return;
    
    if (onResponse) {
      onResponse({
        field: params.field_name || "selection",
        value: params.multi_select ? selected : selected[0]
      });
      setSubmitted(true);
    }
  };

  if (submitted) {
    return (
      <div className="p-4 border rounded bg-[#181c2a] text-white">
        <p className="font-semibold text-green-400">
          Selection submitted successfully
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 border rounded bg-[#181c2a] text-white">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-bold">{params.title || "Make a Selection"}</h3>
        {progress && (
          <span className="text-sm bg-[#3d3d5c] px-2 py-1 rounded">Progress: {progress}</span>
        )}
      </div>
      
      <p className="mb-4">{params.prompt || "Please select an option:"}</p>
      
      <div className="space-y-2">
        {params.options.map((option, idx) => (
          <div 
            key={idx}
            className={`p-3 rounded cursor-pointer transition-colors ${
              selected.includes(option.value) 
                ? 'bg-[#6d4aff] text-white' 
                : 'bg-[#121833] border border-[#1e2642] hover:bg-[#1a243b]'
            }`}
            onClick={() => handleSelect(option.value)}
          >
            {option.label}
          </div>
        ))}
      </div>
      
      <button
        className="mt-4 bg-[#6d4aff] hover:bg-[#5d3aef] transition-colors text-white px-4 py-2 rounded disabled:opacity-50"
        onClick={handleSubmit}
        disabled={selected.length === 0}
      >
        Submit
      </button>
    </div>
  );
};

// Progress Indicator Widget
export const ProgressIndicatorWidget: React.FC<ComponentProps> = ({ params }) => {
  return (
    <div className="p-4 border rounded bg-[#181c2a] text-white">
      <p className="mb-2">{params.message || "Processing..."}</p>
      
      <div className="w-full h-2 bg-[#121833] rounded-full overflow-hidden">
        {params.is_indeterminate ? (
          <div className="h-full bg-[#6d4aff] animate-pulse" style={{ width: '100%' }}></div>
        ) : (
          <div 
            className="h-full bg-[#6d4aff]" 
            style={{ width: `${params.progress_percent || 0}%` }}
          ></div>
        )}
      </div>
    </div>
  );
};

// Confirmation Dialog Widget
export const ConfirmationDialogWidget: React.FC<ComponentProps> = ({ params, onResponse, progress }) => {
  const [submitted, setSubmitted] = useState(false);
  const [confirmed, setConfirmed] = useState<boolean | null>(null);

  const handleConfirm = () => {
    setConfirmed(true);
    if (onResponse) {
      onResponse({
        field: params.field_name || "confirmation",
        value: true
      });
    }
    setSubmitted(true);
  };

  const handleCancel = () => {
    setConfirmed(false);
    if (onResponse) {
      onResponse({
        field: params.field_name || "confirmation",
        value: false
      });
    }
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="p-4 border rounded bg-[#181c2a] text-white">
        <p className="font-semibold text-green-400">
          {confirmed ? "Confirmed" : "Cancelled"}
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 border rounded bg-[#181c2a] text-white">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-bold">{params.title}</h3>
        {progress && (
          <span className="text-sm bg-[#3d3d5c] px-2 py-1 rounded">Progress: {progress}</span>
        )}
      </div>
      
      <p className="mb-4">{params.message}</p>
      
      <div className="flex gap-3 justify-end">
        <button
          className="px-4 py-2 bg-[#242d4f] hover:bg-[#343e60] rounded text-white transition-colors"
          onClick={handleCancel}
        >
          {params.cancel_label || "Cancel"}
        </button>
        <button
          className="px-4 py-2 bg-[#6d4aff] hover:bg-[#5d3aef] rounded text-white transition-colors"
          onClick={handleConfirm}
        >
          {params.confirm_label || "Confirm"}
        </button>
      </div>
    </div>
  );
};

// --- UI Component Registry ---

// Define the component registry - maps instruction types to React components
type ComponentRegistry = {
  [key in UIInstructionType]?: React.ComponentType<ComponentProps>;
};

export const uiComponentRegistry: ComponentRegistry = {
  "show_file_upload": FileUploadWidget,
  "request_email": EmailRequestWidget,
  "display_form": FormDisplayWidget,
  "show_auth_prompt": AuthPromptWidget,
  "show_selection_menu": SelectionMenuWidget,
  "show_progress_indicator": ProgressIndicatorWidget,
  "show_confirmation_dialog": ConfirmationDialogWidget
};

// UI Instruction Handler - renders the appropriate component based on the instruction type
export const InstructionRenderer: React.FC<{
  instruction: UIInstruction;
  onResponse: InstructionResponseHandler;
  progress?: string;
}> = ({ instruction, onResponse, progress }) => {
  const Component = uiComponentRegistry[instruction.instruction_type];
  
  if (!Component) {
    console.error(`No component registered for instruction type: ${instruction.instruction_type}`);
    return (
      <div className="p-4 border rounded bg-red-800 text-white">
        Error: Unknown instruction type "{instruction.instruction_type}"
      </div>
    );
  }
  
  return (
    <Component 
      params={instruction.parameters} 
      onResponse={(data) => {
        onResponse(data);
        // Mark the instruction as completed in the state manager
        uiInstructionStateManager.completeActive();
      }}
      progress={progress} 
    />
  );
};

// UI Instructions Container - manages the active instruction
export const UIInstructionsContainer: React.FC = () => {
  const [activeState, setActiveState] = useState<UIInstructionState | null>(null);
  const [queuedInstructions, setQueuedInstructions] = useState<UIInstructionState[]>([]);
  const [debug, setDebug] = useState<boolean>(false);
  
  // Subscribe to state manager to get updates about active instructions
  useEffect(() => {
    const unsubscribeActive = uiInstructionStateManager.subscribe((state) => {
      setActiveState(state);
    });
    
    const unsubscribeQueue = uiInstructionStateManager.subscribeToQueue((queue) => {
      setQueuedInstructions(queue);
    });
    
    // Initial state
    setActiveState(uiInstructionStateManager.getActive());
    setQueuedInstructions(uiInstructionStateManager.getQueue());
    
    // Check for debug mode from localStorage or URL param
    const debugParam = typeof window !== 'undefined' && 
      (localStorage.getItem('ui_debug') === 'true' || 
       window.location.search.includes('ui_debug=true'));
    
    setDebug(!!debugParam);
    
    return () => {
      unsubscribeActive();
      unsubscribeQueue();
    };
  }, []);
  
  // Handler for retrying a failed instruction
  const handleRetry = (id: string) => {
    uiInstructionStateManager.retryInstruction(id);
  };
  
  // Handler for resuming a deferred instruction
  const handleResume = (id: string) => {
    uiInstructionStateManager.resumeInstruction(id);
  };
  
  // Handler for cancelling an instruction
  const handleCancel = (id: string) => {
    const instruction = uiInstructionStateManager.getInstructionById(id);
    if (instruction && instruction.status === 'active') {
      uiInstructionStateManager.cancelActive('Cancelled by user');
    }
  };
  
  if (!activeState && queuedInstructions.length === 0) {
    return debug ? (
      <div className="ui-instruction-container m-4 p-4 border rounded bg-[#121833] text-white">
        <p className="text-gray-400">No active UI instructions</p>
      </div>
    ) : null;
  }
  
  return (
    <div className="ui-instruction-container m-4">
      {activeState && (
        <div className="mb-4">
          {debug && (
            <div className="mb-2 p-2 bg-[#121833] text-xs">
              <span className="px-2 py-1 rounded bg-blue-500 text-white text-xs uppercase mr-2">
                Active
              </span>
              <span className="text-gray-300">
                {activeState.instruction.instruction_type} (ID: {activeState.id})
              </span>
              <button 
                className="float-right text-red-400 hover:text-red-300"
                onClick={() => handleCancel(activeState.id)}
              >
                Cancel
              </button>
            </div>
          )}
          
          <InstructionRenderer
            instruction={activeState.instruction}
            onResponse={(data) => {
              // Dispatch event with response data
              const event = new CustomEvent('ui-instruction-response', { 
                detail: { 
                  instruction_type: activeState.instruction.instruction_type,
                  instruction_id: activeState.id,
                  response: data 
                } 
              });
              window.dispatchEvent(event);
              
              // Mark the instruction as completed
              uiInstructionStateManager.completeActive(data);
            }}
            progress={debug ? `${queuedInstructions.filter(i => i.status === 'pending').length + 1} remaining` : undefined}
          />
        </div>
      )}
      
      {debug && queuedInstructions.length > 0 && (
        <div className="p-3 border rounded bg-[#121833] mt-4">
          <h3 className="text-sm font-bold mb-2 text-gray-300">Instruction Queue</h3>
          <div className="space-y-1 max-h-40 overflow-y-auto">
            {queuedInstructions.map((instruction) => (
              <div 
                key={instruction.id} 
                className="flex items-center justify-between p-2 text-xs border-b border-gray-800"
              >
                <div>
                  <span className={`px-1.5 py-0.5 rounded text-white mr-2 ${
                    instruction.status === 'pending' ? 'bg-yellow-600' :
                    instruction.status === 'deferred' ? 'bg-purple-600' : 
                    instruction.status === 'error' ? 'bg-red-600' :
                    instruction.status === 'timeout' ? 'bg-orange-600' :
                    'bg-gray-600'
                  }`}>
                    {instruction.status}
                  </span>
                  <span className="text-gray-300">
                    {instruction.instruction.instruction_type.replace(/_/g, ' ')}
                  </span>
                </div>
                
                <div>
                  {instruction.status === 'error' || instruction.status === 'timeout' ? (
                    <button 
                      className="text-blue-400 hover:text-blue-300 ml-2"
                      onClick={() => handleRetry(instruction.id)}
                    >
                      Retry
                    </button>
                  ) : null}
                  
                  {instruction.status === 'deferred' && (
                    <button 
                      className="text-green-400 hover:text-green-300 ml-2"
                      onClick={() => handleResume(instruction.id)}
                    >
                      Resume
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
          
          {queuedInstructions.length > 0 && (
            <button 
              className="mt-2 text-xs text-gray-400 hover:text-white"
              onClick={() => uiInstructionStateManager.cleanup()}
            >
              Clean up completed
            </button>
          )}
        </div>
      )}
    </div>
  );
};

// Helper function to queue a new UI instruction
export function queueUIInstruction(instruction: UIInstruction, timeoutMs?: number): string | null {
  return queueInstruction(instruction, timeoutMs);
}

// Helper function to register a response handler for specific instruction types
export function registerInstructionResponseHandler(
  instructionType: UIInstructionType,
  handler: (response: any) => void
) {
  const handleEvent = (event: Event) => {
    const customEvent = event as CustomEvent;
    if (customEvent.detail?.instruction_type === instructionType) {
      handler(customEvent.detail.response);
    }
  };
  
  window.addEventListener('ui-instruction-response', handleEvent);
  
  // Return a function to remove the event listener
  return () => {
    window.removeEventListener('ui-instruction-response', handleEvent);
  };
}

// --- Exports ---
export default {
  uiComponentRegistry,
  InstructionRenderer,
  UIInstructionsContainer,
  queueUIInstruction,
  registerInstructionResponseHandler,
  // Export state management functions
  getActiveInstruction: uiInstructionStateManager.getActive.bind(uiInstructionStateManager),
  getInstructionQueue: uiInstructionStateManager.getQueue.bind(uiInstructionStateManager),
  cancelInstruction: uiInstructionStateManager.cancelActive.bind(uiInstructionStateManager),
  retryInstruction: uiInstructionStateManager.retryInstruction.bind(uiInstructionStateManager),
  resumeInstruction: uiInstructionStateManager.resumeInstruction.bind(uiInstructionStateManager),
  clearInstructions: uiInstructionStateManager.clear.bind(uiInstructionStateManager),
  cleanupInstructions: uiInstructionStateManager.cleanup.bind(uiInstructionStateManager)
};