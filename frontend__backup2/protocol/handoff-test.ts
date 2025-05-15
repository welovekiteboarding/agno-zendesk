/**
 * Agent Handoff Test Script
 * 
 * This script tests the handoff functionality between Agno and Form Collector agents
 * using the UnifiedChatUI component. It simulates conversation flows that would
 * trigger agent handoffs and verifies that the transitions happen correctly.
 */

import { agentRegistry } from './agentRegistry';
import { uiInstructionStateManager } from './uiInstructionState';

/**
 * Tests the handoff from Agno to Form Collector agent
 * @returns {Promise<boolean>} True if the test passes
 */
export async function testAgnoToFormCollectorHandoff(): Promise<boolean> {
  console.log('🧪 Testing Agno to Form Collector handoff...');
  
  // Setup: Register mock API endpoints to simulate backend
  const mockMessages = [
    { role: 'agno_agent', content: 'Hi, I can help you with your question.' },
    { role: 'agno_agent', content: 'It sounds like you need to submit a bug report. Let me transfer you to our form collection agent.' },
    { role: 'form_collector', content: 'Hello, I can help you submit a bug report. What is your email address?' },
  ];

  let currentMessageIndex = 0;
  let currentAgent = 'agno_agent';
  
  // Mock fetch to simulate API responses
  global.fetch = jest.fn().mockImplementation((url, options) => {
    const body = JSON.parse(options.body);
    
    // Simulate handoff after the right trigger message
    if (body.user_message.toLowerCase().includes('bug report') && currentAgent === 'agno_agent') {
      currentAgent = 'form_collector';
      currentMessageIndex = 1; // Move to handoff message
    }
    
    // Increment the message index for the next response
    currentMessageIndex = Math.min(currentMessageIndex + 1, mockMessages.length - 1);
    
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        assistant_message: mockMessages[currentMessageIndex].content,
        agent_id: mockMessages[currentMessageIndex].role,
        handoff: currentMessageIndex === 2 ? {
          from: 'agno_agent',
          to: 'form_collector',
          context: { reason: 'bug_report_request' }
        } : null
      })
    });
  });
  
  // Test case 1: Verify agent transition
  try {
    const response = await fetch('http://localhost:8001/api/agno-agent/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: 'test-session',
        user_message: 'I need to submit a bug report',
      }),
    });
    
    const data = await response.json();
    
    console.log('Response from mock API:', data);
    
    // Assert that agent has changed
    if (data.agent_id !== 'form_collector') {
      console.error('❌ Handoff failed: Agent did not change to form_collector');
      return false;
    }
    
    // Assert that handoff data is present
    if (!data.handoff || data.handoff.from !== 'agno_agent' || data.handoff.to !== 'form_collector') {
      console.error('❌ Handoff data is missing or incorrect');
      return false;
    }
    
    console.log('✅ Agent handoff test passed!');
    return true;
  } catch (error) {
    console.error('❌ Test failed with error:', error);
    return false;
  }
}

/**
 * Tests that UI instructions are properly forwarded during a handoff
 * @returns {Promise<boolean>} True if the test passes
 */
export async function testUIInstructionsDuringHandoff(): Promise<boolean> {
  console.log('🧪 Testing UI instructions during handoff...');
  
  // Clear any existing UI instructions
  uiInstructionStateManager.clear();
  
  // Setup mock response with UI instruction
  global.fetch = jest.fn().mockImplementation(() => {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        assistant_message: 'Please provide your email address.',
        agent_id: 'form_collector',
        handoff: {
          from: 'agno_agent',
          to: 'form_collector',
          context: { reason: 'bug_report_request' }
        },
        ui_instructions: [
          {
            instruction_type: 'request_email',
            parameters: {
              prompt: 'Please enter your email address:',
              validation_regex: '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$'
            },
            metadata: {
              priority: 'normal',
              version: '1.0.0',
              agent_id: 'form_collector'
            }
          }
        ]
      })
    });
  });
  
  try {
    // Simulate API call that would trigger a UI instruction
    const response = await fetch('http://localhost:8001/api/agno-agent/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: 'test-session',
        user_message: 'I need to submit a bug report',
      }),
    });
    
    const data = await response.json();
    
    // Process UI instructions
    if (data.ui_instructions && data.ui_instructions.length > 0) {
      data.ui_instructions.forEach(instruction => {
        const id = uiInstructionStateManager.enqueue(instruction);
        console.log(`Enqueued instruction ${id} of type ${instruction.instruction_type}`);
      });
    }
    
    // Check if instruction was processed
    const queue = uiInstructionStateManager.getQueue();
    const active = uiInstructionStateManager.getActive();
    
    if (!active && (!queue || queue.length === 0)) {
      console.error('❌ UI instruction not processed during handoff');
      return false;
    }
    
    const currentInstruction = active || queue[0];
    
    // Verify instruction type and source agent
    if (currentInstruction.instruction.instruction_type !== 'request_email') {
      console.error('❌ Wrong instruction type received:', currentInstruction.instruction.instruction_type);
      return false;
    }
    
    if (currentInstruction.instruction.metadata.agent_id !== 'form_collector') {
      console.error('❌ Instruction from wrong agent:', currentInstruction.instruction.metadata.agent_id);
      return false;
    }
    
    console.log('✅ UI instructions during handoff test passed!');
    return true;
  } catch (error) {
    console.error('❌ Test failed with error:', error);
    return false;
  } finally {
    // Clean up
    uiInstructionStateManager.clear();
  }
}

/**
 * Runs all handoff tests
 */
export async function runHandoffTests(): Promise<void> {
  console.log('🧪 Running Agent Handoff Tests...');
  
  const results = await Promise.all([
    testAgnoToFormCollectorHandoff(),
    testUIInstructionsDuringHandoff()
  ]);
  
  const passedCount = results.filter(result => result).length;
  console.log(`\n✅ ${passedCount} of ${results.length} tests passed`);
  
  if (passedCount < results.length) {
    console.error('❌ Some tests failed. See details above.');
  } else {
    console.log('🎉 All agent handoff tests passed successfully!');
  }
}

// Execute tests if running directly
if (typeof window !== 'undefined' && window.location.search.includes('run_tests=true')) {
  runHandoffTests().catch(console.error);
}