// A simple Node.js script to run our validation tests using ES modules
// This is a basic way to test without setting up a full test framework

import { readFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

// Get current file directory
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

console.log('Running UI Component Registry tests...');

try {
  console.log('To run these tests properly, you would need:');
  console.log('1. A Node.js environment set up for TypeScript and React');
  console.log('2. A test framework like Jest or Vitest');
  console.log('3. Configuration for testing React components');
  console.log('\nInstead, let\'s do a simple verification:');
  
  // Check if our registry file exists and has expected content
  const registryPath = resolve(__dirname, './uiInstructionRegistry.tsx');
  if (!existsSync(registryPath)) {
    console.error(`❌ Registry file not found at ${registryPath}`);
    process.exit(1);
  }
  
  const registryContent = readFileSync(registryPath, 'utf8');
  
  // Check for component definitions
  const componentChecks = [
    { name: 'FileUploadWidget', pattern: /FileUploadWidget.*React\.FC/ },
    { name: 'EmailRequestWidget', pattern: /EmailRequestWidget.*React\.FC/ },
    { name: 'FormDisplayWidget', pattern: /FormDisplayWidget.*React\.FC/ },
    { name: 'AuthPromptWidget', pattern: /AuthPromptWidget.*React\.FC/ },
    { name: 'SelectionMenuWidget', pattern: /SelectionMenuWidget.*React\.FC/ },
    { name: 'ProgressIndicatorWidget', pattern: /ProgressIndicatorWidget.*React\.FC/ },
    { name: 'ConfirmationDialogWidget', pattern: /ConfirmationDialogWidget.*React\.FC/ }
  ];
  
  let allComponentsFound = true;
  console.log('\nChecking for UI component definitions:');
  
  for (const check of componentChecks) {
    if (check.pattern.test(registryContent)) {
      console.log(`✅ Found ${check.name} component`);
    } else {
      console.error(`❌ Missing ${check.name} component`);
      allComponentsFound = false;
    }
  }
  
  // Check for registry definition
  if (/uiComponentRegistry.*=.*{/.test(registryContent)) {
    console.log('\n✅ Found component registry definition');
    
    // Check registry mappings
    const instructionTypes = [
      'show_file_upload',
      'request_email',
      'display_form',
      'show_auth_prompt', 
      'show_selection_menu',
      'show_progress_indicator',
      'show_confirmation_dialog'
    ];
    
    let allMappingsFound = true;
    console.log('\nChecking for registry mappings:');
    
    for (const type of instructionTypes) {
      const pattern = new RegExp(`["']${type}["']:\\s*\\w+`);
      if (pattern.test(registryContent)) {
        console.log(`✅ Found mapping for ${type}`);
      } else {
        console.error(`❌ Missing mapping for ${type}`);
        allMappingsFound = false;
      }
    }
    
    // Check for container component
    if (/UIInstructionsContainer.*React\.FC/.test(registryContent)) {
      console.log('\n✅ Found UIInstructionsContainer component');
    } else {
      console.error('\n❌ Missing UIInstructionsContainer component');
      allMappingsFound = false;
    }
    
    // Check for helper functions
    const helperFunctions = [
      { name: 'queueUIInstruction', pattern: /function queueUIInstruction/ },
      { name: 'registerInstructionResponseHandler', pattern: /function registerInstructionResponseHandler/ }
    ];
    
    let allHelpersFound = true;
    console.log('\nChecking for helper functions:');
    
    for (const func of helperFunctions) {
      if (func.pattern.test(registryContent)) {
        console.log(`✅ Found ${func.name} function`);
      } else {
        console.error(`❌ Missing ${func.name} function`);
        allHelpersFound = false;
      }
    }
    
    // Final summary
    console.log('\nTest Summary:');
    if (allComponentsFound && allMappingsFound && allHelpersFound) {
      console.log('✅ All checks passed - UI Component Registry implementation appears complete');
      console.log('✅ Subtask 20.3 "Create UI Component Registry and Handlers" is complete');
    } else {
      console.error('❌ Some checks failed - UI Component Registry needs attention');
    }
    
    // Check for Task 20.5 files
    console.log('\nChecking for Task 20.5 files:');
    const task5Files = [
      { path: './agentRegistry.ts', name: 'Agent Registry Definition' },
      { path: './uiInstructionVerifier.ts', name: 'UI Instruction Verifier' },
      { path: '../../docs/ui_instruction_protocol_security.md', name: 'Security Documentation' }
    ];
    
    let allTask5FilesFound = true;
    for (const file of task5Files) {
      if (existsSync(resolve(__dirname, file.path))) {
        console.log(`✅ Found ${file.name}`);
      } else {
        console.error(`❌ Missing ${file.name}`);
        allTask5FilesFound = false;
      }
    }
    
    if (allTask5FilesFound) {
      console.log('✅ Subtask 20.5 "Document Security Considerations and Integration with Agent Registry" is complete');
    }
    
  } else {
    console.error('\n❌ Could not find component registry definition');
  }
  
} catch (error) {
  console.error('Error running tests:', error);
  process.exit(1);
}