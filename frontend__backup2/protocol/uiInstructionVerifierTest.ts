// agno-zendesk/frontend__backup2/protocol/uiInstructionVerifierTest.ts
// Test file for UI Instruction Verifier and Agent Registry integration

import { UIInstructionVerifier } from './uiInstructionVerifier';
import { MockAgentRegistry } from './agentRegistry';
import { UIInstruction, UIInstructionValidationError } from './uiInstruction';

/**
 * Creates a mock instruction for testing
 */
function createMockInstruction(
  type = 'show_file_upload',
  agentId = 'form_collector'
): UIInstruction {
  return {
    instruction_type: type as any,
    parameters: {
      max_files: 3,
      max_size_mb: 10,
      accepted_types: ['image/png', 'image/jpeg'],
      upload_url: 'https://example.com/upload'
    },
    metadata: {
      priority: 'normal' as const,
      version: '1.0.0',
      agent_id: agentId
    }
  };
}

/**
 * Test agent authorization
 */
function testAgentAuthorization() {
  console.log('Running agent authorization tests...');
  
  // Create registry and verifier
  const registry = new MockAgentRegistry();
  const verifier = new UIInstructionVerifier(registry);
  
  // Valid agent with valid instruction type
  try {
    const validInstruction = createMockInstruction('show_file_upload', 'form_collector');
    const result = verifier.verify(validInstruction);
    console.log('✅ Valid instruction from authorized agent passed verification');
  } catch (error) {
    console.error('❌ Valid instruction from authorized agent should pass verification');
    console.error((error as Error).message);
    return false;
  }
  
  // Valid agent with unauthorized instruction type
  try {
    const unauthorizedInstruction = createMockInstruction('show_auth_prompt', 'form_collector');
    verifier.verify(unauthorizedInstruction);
    console.error('❌ Unauthorized instruction type should be rejected');
    return false;
  } catch (error) {
    if (error instanceof UIInstructionValidationError) {
      console.log('✅ Unauthorized instruction type properly rejected');
    } else {
      console.error('❌ Unexpected error type', error);
      return false;
    }
  }
  
  // Invalid agent ID
  try {
    const unknownAgentInstruction = createMockInstruction('show_file_upload', 'unknown_agent');
    verifier.verify(unknownAgentInstruction);
    console.error('❌ Unknown agent should be rejected');
    return false;
  } catch (error) {
    if (error instanceof UIInstructionValidationError) {
      console.log('✅ Unknown agent properly rejected');
    } else {
      console.error('❌ Unexpected error type', error);
      return false;
    }
  }
  
  // Missing agent ID
  try {
    const noAgentInstruction = createMockInstruction('show_file_upload', '');
    verifier.verify(noAgentInstruction);
    console.error('❌ Missing agent ID should be rejected');
    return false;
  } catch (error) {
    if (error instanceof UIInstructionValidationError) {
      console.log('✅ Missing agent ID properly rejected');
    } else {
      console.error('❌ Unexpected error type', error);
      return false;
    }
  }
  
  console.log('✅ Agent authorization tests passed');
  return true;
}

/**
 * Test agent priority comparison
 */
function testAgentPriorities() {
  console.log('Running agent priority tests...');
  
  // Create registry and verifier
  const registry = new MockAgentRegistry();
  const verifier = new UIInstructionVerifier(registry);
  
  // Form collector vs email verifier (form collector has higher priority)
  const formVsEmail = verifier.compareAgentPriorities('form_collector', 'email_verifier');
  if (formVsEmail > 0) {
    console.log('✅ Form collector correctly has higher priority than email verifier');
  } else {
    console.error('❌ Form collector should have higher priority than email verifier');
    return false;
  }
  
  // Email verifier vs ticket poster (ticket poster has higher priority)
  const emailVsTicket = verifier.compareAgentPriorities('email_verifier', 'ticket_poster');
  if (emailVsTicket < 0) {
    console.log('✅ Email verifier correctly has lower priority than ticket poster');
  } else {
    console.error('❌ Email verifier should have lower priority than ticket poster');
    return false;
  }
  
  // Same agent comparison
  const sameAgent = verifier.compareAgentPriorities('form_collector', 'form_collector');
  if (sameAgent === 0) {
    console.log('✅ Same agent comparison correctly returns 0');
  } else {
    console.error('❌ Same agent comparison should return 0');
    return false;
  }
  
  // Unknown agent should have priority 0
  const unknownAgent = verifier.getAgentPriority('unknown_agent');
  if (unknownAgent === 0) {
    console.log('✅ Unknown agent correctly has priority 0');
  } else {
    console.error('❌ Unknown agent should have priority 0');
    return false;
  }
  
  console.log('✅ Agent priority tests passed');
  return true;
}

/**
 * Test agent name retrieval
 */
function testAgentNames() {
  console.log('Running agent name tests...');
  
  // Create registry and verifier
  const registry = new MockAgentRegistry();
  const verifier = new UIInstructionVerifier(registry);
  
  // Get name of known agent
  const formCollectorName = verifier.getAgentName('form_collector');
  if (formCollectorName === 'Form Collection Agent') {
    console.log('✅ Correctly retrieved form collector agent name');
  } else {
    console.error(`❌ Expected "Form Collection Agent", got "${formCollectorName}"`);
    return false;
  }
  
  // Get name of unknown agent (should return the ID)
  const unknownName = verifier.getAgentName('unknown_agent');
  if (unknownName === 'unknown_agent') {
    console.log('✅ Correctly returned ID for unknown agent');
  } else {
    console.error(`❌ Expected "unknown_agent", got "${unknownName}"`);
    return false;
  }
  
  console.log('✅ Agent name tests passed');
  return true;
}

/**
 * Run all tests
 */
async function runAllTests() {
  console.group('UI Instruction Verifier & Agent Registry Tests (Task 20.5)');
  
  let allPassed = true;
  
  allPassed = testAgentAuthorization() && allPassed;
  allPassed = testAgentPriorities() && allPassed;
  allPassed = testAgentNames() && allPassed;
  
  console.log('\nTest Summary:');
  if (allPassed) {
    console.log('✅ All tests passed! The UI Instruction Verifier & Agent Registry integration (Task 20.5) is complete.');
  } else {
    console.error('❌ Some tests failed. The UI Instruction Verifier & Agent Registry integration needs more work.');
  }
  
  console.groupEnd();
  
  return allPassed;
}

// Run tests when executed directly
if (typeof process !== 'undefined' && process.env.NODE_ENV === 'test') {
  runAllTests().then(success => {
    process.exit(success ? 0 : 1);
  });
}

export default runAllTests;