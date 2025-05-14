// testComponentRegistry.ts
// A simple test script to validate the UI Component Registry implementation

import { uiComponentRegistry } from './uiInstructionRegistry';
import { UIInstructionType } from './uiInstruction';

function testComponentRegistry() {
  console.group('UI Component Registry Test');
  
  // Expected instruction types
  const expectedInstructionTypes: UIInstructionType[] = [
    'show_file_upload',
    'request_email',
    'display_form',
    'show_auth_prompt',
    'show_selection_menu',
    'show_progress_indicator',
    'show_confirmation_dialog'
  ];
  
  // Test 1: Verify all expected instruction types are registered
  console.log('Test 1: Verify all expected instruction types are registered');
  
  const missingHandlers: string[] = [];
  for (const type of expectedInstructionTypes) {
    if (!uiComponentRegistry[type]) {
      missingHandlers.push(type);
    }
  }
  
  if (missingHandlers.length > 0) {
    console.error('❌ Missing handlers for the following instruction types:', missingHandlers);
  } else {
    console.log('✅ All expected instruction types have corresponding handlers');
  }
  
  // Test 2: Verify there are no extra handlers
  console.log('\nTest 2: Verify there are no extra handlers');
  
  const extraHandlers: string[] = [];
  for (const type in uiComponentRegistry) {
    if (!expectedInstructionTypes.includes(type as UIInstructionType)) {
      extraHandlers.push(type);
    }
  }
  
  if (extraHandlers.length > 0) {
    console.warn('⚠️ Found extra handlers for instruction types not in schema:', extraHandlers);
  } else {
    console.log('✅ No extra handlers found');
  }
  
  // Test 3: Check handler type (must be React components)
  console.log('\nTest 3: Check handler types');
  
  const invalidHandlers: string[] = [];
  for (const type of expectedInstructionTypes) {
    const handler = uiComponentRegistry[type];
    // In TypeScript/JavaScript, we can only do limited type checking at runtime
    // Here we check if the handler is a function (React functional components are functions)
    if (handler && typeof handler !== 'function') {
      invalidHandlers.push(type);
    }
  }
  
  if (invalidHandlers.length > 0) {
    console.error('❌ The following handlers are not valid React components:', invalidHandlers);
  } else {
    console.log('✅ All handlers appear to be valid React components');
  }
  
  // Summary
  console.log('\nTest Summary:');
  if (missingHandlers.length === 0 && invalidHandlers.length === 0) {
    console.log('✅ All tests passed - UI Component Registry implementation is complete');
  } else {
    console.error('❌ Some tests failed - UI Component Registry needs attention');
    if (missingHandlers.length > 0) {
      console.error(`- Missing handlers: ${missingHandlers.join(', ')}`);
    }
    if (invalidHandlers.length > 0) {
      console.error(`- Invalid handlers: ${invalidHandlers.join(', ')}`);
    }
  }
  
  console.groupEnd();
  
  return {
    success: missingHandlers.length === 0 && invalidHandlers.length === 0,
    missingHandlers,
    invalidHandlers,
    extraHandlers
  };
}

// Run the test if executed directly
if (typeof process !== 'undefined' && process.env.NODE_ENV === 'test') {
  const result = testComponentRegistry();
  process.exit(result.success ? 0 : 1);
}

export default testComponentRegistry;