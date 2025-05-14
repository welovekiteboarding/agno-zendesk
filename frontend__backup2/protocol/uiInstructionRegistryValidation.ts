// uiInstructionRegistryValidation.ts
// Validation test for the UI Component Registry

import { UIInstruction } from './uiInstruction';
import { uiComponentRegistry } from './uiInstructionRegistry';

/**
 * Validates that all required components are registered for each instruction type
 * defined in the schema.
 */
function validateComponentRegistry(): { valid: boolean; missingHandlers: string[] } {
  const instructionTypes = [
    'show_file_upload',
    'request_email',
    'display_form',
    'show_auth_prompt',
    'show_selection_menu',
    'show_progress_indicator',
    'show_confirmation_dialog'
  ];
  
  const missingHandlers: string[] = [];
  
  // Check if each instruction type has a registered component handler
  for (const type of instructionTypes) {
    if (!uiComponentRegistry[type as keyof typeof uiComponentRegistry]) {
      missingHandlers.push(type);
    }
  }
  
  return {
    valid: missingHandlers.length === 0,
    missingHandlers
  };
}

/**
 * Validates sample instructions against the component registry
 */
function validateSampleInstructions(): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  // Sample instruction for each type
  const sampleInstructions: UIInstruction[] = [
    {
      instruction_type: 'show_file_upload',
      parameters: {
        max_files: 3,
        max_size_mb: 10,
        accepted_types: ['image/png', 'image/jpeg'],
        upload_url: 'https://example.com/upload'
      },
      metadata: {
        priority: 'normal',
        version: '1.0.0'
      }
    },
    {
      instruction_type: 'request_email',
      parameters: {
        prompt: 'Please enter your email:'
      },
      metadata: {
        priority: 'normal',
        version: '1.0.0'
      }
    },
    {
      instruction_type: 'display_form',
      parameters: {
        fields: [
          { name: 'name', label: 'Name', type: 'text', required: true }
        ]
      },
      metadata: {
        priority: 'normal',
        version: '1.0.0'
      }
    },
    {
      instruction_type: 'show_auth_prompt',
      parameters: {
        prompt: 'Enter password:',
        auth_type: 'password'
      },
      metadata: {
        priority: 'high',
        version: '1.0.0'
      }
    },
    {
      instruction_type: 'show_selection_menu',
      parameters: {
        prompt: 'Select an option:',
        options: [
          { label: 'Option 1', value: '1' },
          { label: 'Option 2', value: '2' }
        ]
      },
      metadata: {
        priority: 'normal',
        version: '1.0.0'
      }
    },
    {
      instruction_type: 'show_progress_indicator',
      parameters: {
        message: 'Loading...',
        progress_percent: 50
      },
      metadata: {
        priority: 'low',
        version: '1.0.0'
      }
    },
    {
      instruction_type: 'show_confirmation_dialog',
      parameters: {
        title: 'Confirm',
        message: 'Are you sure?'
      },
      metadata: {
        priority: 'high',
        version: '1.0.0'
      }
    }
  ];
  
  // Check if each sample instruction's type has a component handler
  for (const instruction of sampleInstructions) {
    if (!uiComponentRegistry[instruction.instruction_type as keyof typeof uiComponentRegistry]) {
      errors.push(`No component handler for instruction type: ${instruction.instruction_type}`);
    }
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Runs all validation tests
 */
export function validateUIComponentRegistry(): {
  valid: boolean;
  registryValidation: ReturnType<typeof validateComponentRegistry>;
  instructionsValidation: ReturnType<typeof validateSampleInstructions>;
} {
  const registryValidation = validateComponentRegistry();
  const instructionsValidation = validateSampleInstructions();
  
  return {
    valid: registryValidation.valid && instructionsValidation.valid,
    registryValidation,
    instructionsValidation
  };
}

// Run validation if this is executed directly
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  const results = validateUIComponentRegistry();
  console.group('UI Component Registry Validation');
  console.log('Overall validation:', results.valid ? 'PASSED' : 'FAILED');
  
  console.group('Registry Completeness');
  console.log('Valid:', results.registryValidation.valid);
  if (results.registryValidation.missingHandlers.length > 0) {
    console.warn('Missing handlers for:', results.registryValidation.missingHandlers);
  } else {
    console.log('All instruction types have handlers registered');
  }
  console.groupEnd();
  
  console.group('Sample Instructions');
  console.log('Valid:', results.instructionsValidation.valid);
  if (results.instructionsValidation.errors.length > 0) {
    console.warn('Errors:', results.instructionsValidation.errors);
  } else {
    console.log('All sample instructions can be handled');
  }
  console.groupEnd();
  
  console.groupEnd();
}

export default validateUIComponentRegistry;