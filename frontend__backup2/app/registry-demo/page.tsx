'use client';

import React, { useState } from 'react';
import { UIInstruction } from '@/protocol/uiInstruction';
import { 
  UIInstructionsContainer, 
  queueUIInstruction 
} from '@/protocol/uiInstructionRegistry';

export default function RegistryDemoPage() {
  const [activeDemo, setActiveDemo] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  // Sample instructions
  const instructions = {
    fileUpload: {
      instruction_type: 'show_file_upload',
      parameters: {
        max_files: 3,
        max_size_mb: 10,
        accepted_types: ['image/png', 'image/jpeg', 'application/pdf'],
        upload_url: '/api/upload',
        field_name: 'attachments'
      },
      metadata: {
        priority: 'normal',
        version: '1.0.0',
        agent_id: 'test_agent'
      }
    } as UIInstruction,

    emailRequest: {
      instruction_type: 'request_email',
      parameters: {
        prompt: 'Please enter your email address:',
        validation_regex: '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$',
        placeholder: 'your.email@example.com',
        field_name: 'user_email'
      },
      metadata: {
        priority: 'high',
        version: '1.0.0',
        agent_id: 'test_agent'
      }
    } as UIInstruction,

    formDisplay: {
      instruction_type: 'display_form',
      parameters: {
        title: 'Bug Report Form',
        description: 'Please fill out this form with details about the bug you encountered.',
        fields: [
          {
            name: 'title',
            label: 'Bug Title',
            type: 'text',
            required: true,
            placeholder: 'Brief description of the issue'
          },
          {
            name: 'description',
            label: 'Bug Description',
            type: 'textarea',
            required: true,
            placeholder: 'Please provide details about what happened...'
          },
          {
            name: 'severity',
            label: 'Severity',
            type: 'select',
            required: true,
            options: [
              { label: 'Low', value: 'low' },
              { label: 'Medium', value: 'medium' },
              { label: 'High', value: 'high' },
              { label: 'Critical', value: 'critical' }
            ]
          },
          {
            name: 'reproducible',
            label: 'Is this bug consistently reproducible?',
            type: 'checkbox',
            required: false
          }
        ],
        submit_label: 'Submit Bug Report'
      },
      metadata: {
        priority: 'normal',
        version: '1.0.0',
        agent_id: 'test_agent'
      }
    } as UIInstruction,

    authPrompt: {
      instruction_type: 'show_auth_prompt',
      parameters: {
        title: 'Authentication Required',
        prompt: 'Please enter your password to continue:',
        auth_type: 'password',
        field_name: 'user_password'
      },
      metadata: {
        priority: 'high',
        version: '1.0.0',
        agent_id: 'test_agent'
      }
    } as UIInstruction,

    selectionMenu: {
      instruction_type: 'show_selection_menu',
      parameters: {
        title: 'Choose Your Operating System',
        prompt: 'Please select your current operating system:',
        options: [
          { label: 'Windows', value: 'windows' },
          { label: 'macOS', value: 'macos' },
          { label: 'Linux', value: 'linux' },
          { label: 'Other', value: 'other' }
        ],
        multi_select: false,
        field_name: 'operating_system'
      },
      metadata: {
        priority: 'normal',
        version: '1.0.0',
        agent_id: 'test_agent'
      }
    } as UIInstruction,

    progressIndicator: {
      instruction_type: 'show_progress_indicator',
      parameters: {
        message: 'Processing your request, please wait...',
        progress_percent: 65,
        is_indeterminate: false
      },
      metadata: {
        priority: 'low',
        version: '1.0.0',
        agent_id: 'test_agent'
      }
    } as UIInstruction,

    confirmationDialog: {
      instruction_type: 'show_confirmation_dialog',
      parameters: {
        title: 'Confirm Action',
        message: 'Are you sure you want to submit this bug report? This action cannot be undone.',
        confirm_label: 'Yes, Submit Report',
        cancel_label: 'Cancel',
        field_name: 'submit_confirmation'
      },
      metadata: {
        priority: 'high',
        version: '1.0.0',
        agent_id: 'test_agent'
      }
    } as UIInstruction
  };

  // Setup event listeners for UI instruction responses
  React.useEffect(() => {
    const handleResponse = (event: Event) => {
      const customEvent = event as CustomEvent;
      setResult({
        instructionType: customEvent.detail?.instruction_type,
        response: customEvent.detail?.response
      });
    };

    window.addEventListener('ui-instruction-response', handleResponse);
    return () => {
      window.removeEventListener('ui-instruction-response', handleResponse);
    };
  }, []);

  // Function to run a demo
  const runDemo = (demoKey: string) => {
    // Clear previous result
    setResult(null);
    setActiveDemo(demoKey);
    
    // Queue the instruction
    const instruction = instructions[demoKey as keyof typeof instructions];
    if (instruction) {
      queueUIInstruction(instruction);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b1021] text-white p-6">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-center text-[#6d4aff]">UI Component Registry Demo</h1>
        <p className="mb-6 text-center opacity-80">This page demonstrates the UI Component Registry implementation (Task 20.3).</p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-[#121833] p-5 rounded-lg">
            <h2 className="text-xl font-semibold mb-4 text-[#8c5eff]">UI Instructions</h2>
            <div className="space-y-2">
              <button 
                onClick={() => runDemo('fileUpload')}
                className={`w-full text-left px-4 py-2 rounded ${activeDemo === 'fileUpload' ? 'bg-[#6d4aff]' : 'bg-[#1a243b] hover:bg-[#242d4f]'}`}
              >
                File Upload
              </button>
              <button 
                onClick={() => runDemo('emailRequest')}
                className={`w-full text-left px-4 py-2 rounded ${activeDemo === 'emailRequest' ? 'bg-[#6d4aff]' : 'bg-[#1a243b] hover:bg-[#242d4f]'}`}
              >
                Email Request
              </button>
              <button 
                onClick={() => runDemo('formDisplay')}
                className={`w-full text-left px-4 py-2 rounded ${activeDemo === 'formDisplay' ? 'bg-[#6d4aff]' : 'bg-[#1a243b] hover:bg-[#242d4f]'}`}
              >
                Form Display
              </button>
              <button 
                onClick={() => runDemo('authPrompt')}
                className={`w-full text-left px-4 py-2 rounded ${activeDemo === 'authPrompt' ? 'bg-[#6d4aff]' : 'bg-[#1a243b] hover:bg-[#242d4f]'}`}
              >
                Auth Prompt
              </button>
              <button 
                onClick={() => runDemo('selectionMenu')}
                className={`w-full text-left px-4 py-2 rounded ${activeDemo === 'selectionMenu' ? 'bg-[#6d4aff]' : 'bg-[#1a243b] hover:bg-[#242d4f]'}`}
              >
                Selection Menu
              </button>
              <button 
                onClick={() => runDemo('progressIndicator')}
                className={`w-full text-left px-4 py-2 rounded ${activeDemo === 'progressIndicator' ? 'bg-[#6d4aff]' : 'bg-[#1a243b] hover:bg-[#242d4f]'}`}
              >
                Progress Indicator
              </button>
              <button 
                onClick={() => runDemo('confirmationDialog')}
                className={`w-full text-left px-4 py-2 rounded ${activeDemo === 'confirmationDialog' ? 'bg-[#6d4aff]' : 'bg-[#1a243b] hover:bg-[#242d4f]'}`}
              >
                Confirmation Dialog
              </button>
            </div>
          </div>
          
          <div className="md:col-span-2">
            <div className="bg-[#121833] p-5 rounded-lg mb-6">
              <h2 className="text-xl font-semibold mb-4 text-[#8c5eff]">Component Preview</h2>
              <div className="bg-[#0b1021] p-4 rounded min-h-[300px] flex items-center justify-center">
                {activeDemo ? (
                  <UIInstructionsContainer />
                ) : (
                  <p className="text-gray-400">Select an instruction type to preview</p>
                )}
              </div>
            </div>
            
            {result && (
              <div className="bg-[#121833] p-5 rounded-lg">
                <h2 className="text-xl font-semibold mb-4 text-[#8c5eff]">Response Data</h2>
                <div className="bg-[#0b1021] p-4 rounded overflow-x-auto">
                  <pre className="text-sm">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}