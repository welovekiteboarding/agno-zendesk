// uiInstructionStateTest.ts
// Test file for UI Instruction State Management (Task 20.4)

import { 
  UIInstructionStateManager, 
  UIInstructionState,
  InstructionStatus,
  StateEventType
} from './uiInstructionState';
import { UIInstruction, UIInstructionType } from './uiInstruction';

/**
 * Creates a mock instruction for testing
 */
function createMockInstruction(
  type: UIInstructionType = 'show_file_upload',
  priority: 'low' | 'normal' | 'high' = 'normal',
  sequence?: number,
  agentId?: string
): UIInstruction {
  return {
    instruction_type: type,
    parameters: {},
    metadata: {
      priority,
      sequence,
      version: '1.0.0',
      agent_id: agentId
    }
  };
}

/**
 * Test basic queueing and activation
 */
function testBasicQueueing() {
  console.log('Running basic queueing tests...');
  
  // Create a new state manager for isolated testing
  const manager = new UIInstructionStateManager({
    defaultTimeout: 1000, // Shorter timeout for testing
    enablePersistence: false,
    debugLevel: 'none'
  });
  
  // Enqueue a basic instruction
  const id1 = manager.enqueue(createMockInstruction());
  
  if (!id1) {
    console.error('❌ Failed to enqueue first instruction');
    return false;
  }
  
  // Check that the instruction is in the queue
  const queue = manager.getQueue();
  
  if (queue.length !== 1) {
    console.error(`❌ Expected queue to have 1 instruction, found ${queue.length}`);
    return false;
  }
  
  // Check that the instruction was activated
  const active = manager.getActive();
  
  if (!active) {
    console.error('❌ Expected an active instruction, found none');
    return false;
  }
  
  if (active.id !== id1) {
    console.error(`❌ Expected active instruction ID to be ${id1}, found ${active.id}`);
    return false;
  }
  
  if (active.status !== 'active') {
    console.error(`❌ Expected active instruction status to be 'active', found '${active.status}'`);
    return false;
  }
  
  // Complete the active instruction
  manager.completeActive();
  
  // Check that active is now null
  if (manager.getActive() !== null) {
    console.error('❌ Expected active instruction to be null after completion');
    return false;
  }
  
  // Queue should still have the completed instruction
  const queueAfterComplete = manager.getQueue();
  
  if (queueAfterComplete.length !== 1) {
    console.error(`❌ Expected queue to still have 1 instruction, found ${queueAfterComplete.length}`);
    return false;
  }
  
  if (queueAfterComplete[0].status !== 'completed') {
    console.error(`❌ Expected instruction status to be 'completed', found '${queueAfterComplete[0].status}'`);
    return false;
  }
  
  console.log('✅ Basic queueing tests passed');
  return true;
}

/**
 * Test priority ordering
 */
function testPriorityOrdering() {
  console.log('Running priority ordering tests...');
  
  // Create a new state manager for isolated testing
  const manager = new UIInstructionStateManager({
    defaultTimeout: 1000,
    enablePersistence: false,
    debugLevel: 'none'
  });
  
  // Enqueue instructions with different priorities
  const lowId = manager.enqueue(createMockInstruction('request_email', 'low'));
  const normalId = manager.enqueue(createMockInstruction('display_form', 'normal'));
  const highId = manager.enqueue(createMockInstruction('show_confirmation_dialog', 'high'));
  
  if (!lowId || !normalId || !highId) {
    console.error('❌ Failed to enqueue all instructions');
    return false;
  }
  
  // First instruction should be activated immediately
  const active = manager.getActive();
  
  if (!active) {
    console.error('❌ Expected an active instruction, found none');
    return false;
  }
  
  // Mark it as completed to activate the next one
  manager.completeActive();
  
  // Now the high priority instruction should be activated
  const activeAfterFirst = manager.getActive();
  
  if (!activeAfterFirst) {
    console.error('❌ Expected an active instruction after completing first, found none');
    return false;
  }
  
  if (activeAfterFirst.instruction.metadata.priority !== 'high') {
    console.error(`❌ Expected high priority instruction to be activated, found '${activeAfterFirst.instruction.metadata.priority}'`);
    return false;
  }
  
  // Complete it
  manager.completeActive();
  
  // Now the normal priority instruction should be activated
  const activeAfterSecond = manager.getActive();
  
  if (!activeAfterSecond) {
    console.error('❌ Expected an active instruction after completing second, found none');
    return false;
  }
  
  if (activeAfterSecond.instruction.metadata.priority !== 'normal') {
    console.error(`❌ Expected normal priority instruction to be activated, found '${activeAfterSecond.instruction.metadata.priority}'`);
    return false;
  }
  
  // Complete it
  manager.completeActive();
  
  // Now there should be no active instruction
  if (manager.getActive() !== null) {
    console.error('❌ Expected no active instruction after completing all, found one');
    return false;
  }
  
  console.log('✅ Priority ordering tests passed');
  return true;
}

/**
 * Test conflict resolution
 */
function testConflictResolution() {
  console.log('Running conflict resolution tests...');
  
  // Create a new state manager with conflict rules
  const manager = new UIInstructionStateManager({
    defaultTimeout: 1000,
    enablePersistence: false,
    debugLevel: 'none',
    conflictRules: {
      'show_file_upload': {
        conflicts: ['show_file_upload'],
        supersedes: []
      },
      'request_email': {
        conflicts: [],
        supersedes: []
      }
    }
  });
  
  // Enqueue a first instruction and complete it to avoid active state interference
  const setupId = manager.enqueue(createMockInstruction('request_email', 'normal', 1, 'setup'));
  manager.completeActive();
  
  // Enqueue a first instruction from agent1
  const firstId = manager.enqueue(createMockInstruction('show_file_upload', 'normal', 2, 'agent1'));
  
  // Get it to be active
  const firstActive = manager.getActive();
  
  if (!firstActive || firstActive.id !== firstId) {
    console.error('❌ Failed to activate first instruction');
    return false;
  }
  
  // Enqueue a second instruction of the same type from same agent
  const secondId = manager.enqueue(createMockInstruction('show_file_upload', 'normal', 3, 'agent1'));
  
  // The first one should be cancelled/superseded
  const firstAgain = manager.getInstructionById(firstId);
  
  if (!firstAgain) {
    console.error('❌ Failed to find first instruction after enqueueing second');
    return false;
  }
  
  if (firstAgain.status !== 'cancelled') {
    console.error(`❌ Expected first instruction to be cancelled, found '${firstAgain.status}'`);
    return false;
  }
  
  // The second one should be active
  const secondActive = manager.getActive();
  
  if (!secondActive || secondActive.id !== secondId) {
    console.error('❌ Failed to activate second instruction');
    return false;
  }
  
  // Reset by completing the active instruction
  manager.completeActive();
  
  // Enqueue a third instruction from agent1
  const thirdId = manager.enqueue(createMockInstruction('show_file_upload', 'normal', 4, 'agent1'));
  
  // Enqueue a fourth instruction of the same type but from agent2
  const fourthId = manager.enqueue(createMockInstruction('show_file_upload', 'normal', 5, 'agent2'));
  
  // The third one should remain active (no superseding across agents)
  const thirdActive = manager.getActive();
  
  if (!thirdActive || thirdActive.id !== thirdId) {
    console.error('❌ Failed to keep third instruction active');
    return false;
  }
  
  // The fourth one should be pending and have a conflict
  const fourthInstruction = manager.getInstructionById(fourthId!);
  
  if (!fourthInstruction) {
    console.error('❌ Failed to find fourth instruction');
    return false;
  }
  
  if (fourthInstruction.status !== 'pending') {
    console.error(`❌ Expected fourth instruction to be pending, found '${fourthInstruction.status}'`);
    return false;
  }
  
  if (!fourthInstruction.conflictsWith || !fourthInstruction.conflictsWith.includes(thirdId!)) {
    console.error('❌ Expected fourth instruction to conflict with third');
    return false;
  }
  
  console.log('✅ Conflict resolution tests passed');
  return true;
}

/**
 * Test timeouts
 */
async function testTimeouts() {
  console.log('Running timeout tests...');
  
  // Create a new state manager with a very short timeout
  const manager = new UIInstructionStateManager({
    defaultTimeout: 50,  // 50ms
    enablePersistence: false,
    debugLevel: 'none'
  });
  
  // Enqueue an instruction
  const id = manager.enqueue(createMockInstruction());
  
  if (!id) {
    console.error('❌ Failed to enqueue instruction');
    return false;
  }
  
  // Wait for the timeout
  await new Promise(resolve => setTimeout(resolve, 100));
  
  // The instruction should be timed out
  const instruction = manager.getInstructionById(id);
  
  if (!instruction) {
    console.error('❌ Failed to find instruction after timeout');
    return false;
  }
  
  if (instruction.status !== 'timeout') {
    console.error(`❌ Expected instruction status to be 'timeout', found '${instruction.status}'`);
    return false;
  }
  
  // There should be no active instruction
  if (manager.getActive() !== null) {
    console.error('❌ Expected no active instruction after timeout');
    return false;
  }
  
  console.log('✅ Timeout tests passed');
  return true;
}

/**
 * Test retry and resume functionality
 */
async function testRetryAndResume() {
  console.log('Running retry and resume tests...');
  
  // Create a new state manager
  const manager = new UIInstructionStateManager({
    defaultTimeout: 1000,
    enablePersistence: false,
    debugLevel: 'none'
  });
  
  // Enqueue an instruction and make it time out
  const id = manager.enqueue(createMockInstruction(), 10);
  
  if (!id) {
    console.error('❌ Failed to enqueue instruction');
    return false;
  }
  
  // Wait for the timeout
  await new Promise(resolve => setTimeout(resolve, 50));
  
  // The instruction should be timed out
  const instruction = manager.getInstructionById(id);
  
  if (!instruction) {
    console.error('❌ Failed to find instruction after timeout');
    return false;
  }
  
  if (instruction.status !== 'timeout') {
    console.error(`❌ Expected instruction status to be 'timeout', found '${instruction.status}'`);
    return false;
  }
  
  // Retry the instruction
  const retrySuccess = manager.retryInstruction(id);
  
  if (!retrySuccess) {
    console.error('❌ Failed to retry instruction');
    return false;
  }
  
  // The instruction should be pending or active
  const retryInstruction = manager.getInstructionById(id);
  
  if (!retryInstruction) {
    console.error('❌ Failed to find instruction after retry');
    return false;
  }
  
  if (retryInstruction.status !== 'pending' && retryInstruction.status !== 'active') {
    console.error(`❌ Expected instruction status to be 'pending' or 'active', found '${retryInstruction.status}'`);
    return false;
  }
  
  if (retryInstruction.retryCount !== 1) {
    console.error(`❌ Expected retry count to be 1, found ${retryInstruction.retryCount}`);
    return false;
  }
  
  // Get the active instruction (should be our retried one)
  const active = manager.getActive();
  
  if (!active || active.id !== id) {
    console.error('❌ Expected retried instruction to be active');
    return false;
  }
  
  // Manually defer the active instruction
  manager.deferActive('Testing defer');
  
  // The instruction should now be deferred
  const deferredInstruction = manager.getInstructionById(id);
  
  if (!deferredInstruction) {
    console.error('❌ Failed to find instruction after deferral');
    return false;
  }
  
  if (deferredInstruction.status !== 'deferred') {
    console.error(`❌ Expected instruction status to be 'deferred', found '${deferredInstruction.status}'`);
    return false;
  }
  
  // There should be no active instruction
  if (manager.getActive() !== null) {
    console.error('❌ Expected no active instruction after deferral');
    return false;
  }
  
  // Resume the instruction
  const resumeSuccess = manager.resumeInstruction(id);
  
  if (!resumeSuccess) {
    console.error('❌ Failed to resume instruction');
    return false;
  }
  
  // The instruction should be pending or active
  const resumedInstruction = manager.getInstructionById(id);
  
  if (!resumedInstruction) {
    console.error('❌ Failed to find instruction after resume');
    return false;
  }
  
  if (resumedInstruction.status !== 'pending' && resumedInstruction.status !== 'active') {
    console.error(`❌ Expected instruction status to be 'pending' or 'active', found '${resumedInstruction.status}'`);
    return false;
  }
  
  console.log('✅ Retry and resume tests passed');
  return true;
}

/**
 * Run all tests
 */
async function runAllTests() {
  console.group('UI Instruction State Management Tests (Task 20.4)');
  
  let allPassed = true;
  
  allPassed = testBasicQueueing() && allPassed;
  allPassed = testPriorityOrdering() && allPassed;
  allPassed = testConflictResolution() && allPassed;
  allPassed = await testTimeouts() && allPassed;
  allPassed = await testRetryAndResume() && allPassed;
  
  console.log('\nTest Summary:');
  if (allPassed) {
    console.log('✅ All tests passed! The UI Instruction State Management implementation (Task 20.4) is complete.');
  } else {
    console.error('❌ Some tests failed. The UI Instruction State Management implementation needs more work.');
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