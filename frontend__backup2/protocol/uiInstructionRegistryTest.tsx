// agno-zendesk/frontend__backup2/protocol/uiInstructionRegistryTest.tsx

import React, { useState, useEffect } from 'react';
import { UIInstruction } from './uiInstruction';
import { 
  UIInstructionsContainer,
  queueUIInstruction,
  registerInstructionResponseHandler
} from './uiInstructionRegistry';

/**
 * Test component for validating the UI Component Registry functionality
 * This component allows testing all instruction types with sample data
 */
export const UIComponentRegistryTest: React.FC = () => {
  const [responses, setResponses] = useState<Array<{type: string, data: any}>>([]);
  const [selectedTest, setSelectedTest] = useState<string>('');

  // Register response handlers for all instruction types
  useEffect(() => {
    const unsubscribeHandlers = [
      registerInstructionResponseHandler('show_file_upload', (response) => {
        setResponses(prev => [...prev, { type: 'show_file_upload', data: response }]);
      }),
      registerInstructionResponseHandler('request_email', (response) => {
        setResponses(prev => [...prev, { type: 'request_email', data: response }]);
      }),
      registerInstructionResponseHandler('display_form', (response) => {
        setResponses(prev => [...prev, { type: 'display_form', data: response }]);
      }),
      registerInstructionResponseHandler('show_auth_prompt', (response) => {
        setResponses(prev => [...prev, { type: 'show_auth_prompt', data: response }]);
      }),
      registerInstructionResponseHandler('show_selection_menu', (response) => {
        setResponses(prev => [...prev, { type: 'show_selection_menu', data: response }]);
      }),
      registerInstructionResponseHandler('show_confirmation_dialog', (response) => {
        setResponses(prev => [...prev, { type: 'show_confirmation_dialog', data: response }]);
      })
    ];

    return () => {
      // Clean up all event listeners
      unsubscribeHandlers.forEach(unsubscribe => unsubscribe());
    };
  }, []);

  // Example instructions for testing
  const testInstructions: Record<string, UIInstruction> = {
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
    },
    emailRequest: {
      instruction_type: 'request_email',
      parameters: {
        prompt: 'Please enter your email address to continue:',
        validation_regex: '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$',
        placeholder: 'your.email@example.com',
        field_name: 'user_email'
      },
      metadata: {
        priority: 'high',
        version: '1.0.0',
        agent_id: 'test_agent'
      }
    },
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
    },
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
    },
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
    },
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
    },
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
    }
  };

  const runTest = (testKey: string) => {
    setSelectedTest(testKey);
    const instruction = testInstructions[testKey];
    if (instruction) {
      queueUIInstruction(instruction);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b1021] text-white p-6">
      <h1 className="text-2xl font-bold mb-6">UI Component Registry Test</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-[#121833] p-4 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Test Controls</h2>
          <div className="space-y-2">
            <p className="mb-2">Select a component to test:</p>
            {Object.keys(testInstructions).map((key) => (
              <button
                key={key}
                onClick={() => runTest(key)}
                className={`block w-full text-left px-4 py-2 rounded ${
                  selectedTest === key 
                    ? 'bg-[#6d4aff] text-white' 
                    : 'bg-[#1a243b] hover:bg-[#242d4f]'
                }`}
              >
                {key.replace(/([A-Z])/g, ' $1').replace(/^./, (str) => str.toUpperCase())}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-[#121833] p-4 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Component Preview</h2>
          <div className="bg-[#0b1021] p-4 rounded min-h-[300px]">
            {/* The UI component will be rendered here by the Container */}
            <UIInstructionsContainer />
          </div>
        </div>
      </div>

      <div className="mt-6 bg-[#121833] p-4 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Response Log</h2>
        {responses.length === 0 ? (
          <p className="text-gray-400">No responses yet. Interact with a component to see responses here.</p>
        ) : (
          <div className="space-y-4">
            {responses.map((response, index) => (
              <div key={index} className="bg-[#0b1021] p-3 rounded">
                <div className="font-semibold text-[#6d4aff] mb-1">
                  {response.type.replace(/([A-Z])/g, ' $1').replace(/^./, (str) => str.toUpperCase())}
                </div>
                <pre className="text-sm overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(response.data, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// For testing in isolation
if (typeof document !== 'undefined') {
  const testContainer = document.getElementById('ui-test-container');
  if (testContainer) {
    const root = document.createElement('div');
    testContainer.appendChild(root);
    // Note: In a real app, you would use ReactDOM.render() or createRoot()
    // This is just a placeholder for the test component
  }
}

export default UIComponentRegistryTest;