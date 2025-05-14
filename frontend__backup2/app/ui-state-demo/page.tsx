'use client';

import React, { useState, useEffect } from 'react';
import { UIInstruction } from '@/protocol/uiInstruction';
import { UIInstructionsContainer, queueUIInstruction } from '@/protocol/uiInstructionRegistry';
import { uiInstructionStateManager, UIInstructionState } from '@/protocol/uiInstructionState';

export default function UIStateManagementDemo() {
  const [queue, setQueue] = useState<UIInstructionState[]>([]);
  const [active, setActive] = useState<UIInstructionState | null>(null);
  const [eventLog, setEventLog] = useState<string[]>([]);
  const [debug, setDebug] = useState<boolean>(false);

  // Enable debug mode automatically for this demo
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('ui_debug', 'true');
      setDebug(true);
    }
    
    // Subscribe to queue and active instruction changes
    const unsubscribeQueue = uiInstructionStateManager.subscribeToQueue((q) => {
      setQueue(q);
    });
    
    const unsubscribeActive = uiInstructionStateManager.subscribe((a) => {
      setActive(a);
    });
    
    // Initial state
    setQueue(uiInstructionStateManager.getQueue());
    setActive(uiInstructionStateManager.getActive());
    
    return () => {
      unsubscribeQueue();
      unsubscribeActive();
      if (typeof window !== 'undefined') {
        localStorage.removeItem('ui_debug');
      }
    };
  }, []);
  
  // Queue a test instruction
  const queueTestInstruction = (type: string, priority: string = 'normal', timeout?: number) => {
    const instruction: UIInstruction = {
      instruction_type: type as any,
      parameters: getTestParameters(type),
      metadata: {
        priority: priority as any,
        sequence: queue.length,
        version: '1.0.0',
        agent_id: 'test_agent'
      }
    };
    
    const id = queueUIInstruction(instruction, timeout);
    
    addToEventLog(`Queued ${type} instruction with priority ${priority}${timeout ? ` and timeout ${timeout}ms` : ''}${id ? ` (ID: ${id})` : ''}`);
  };
  
  // Get test parameters for different instruction types
  const getTestParameters = (type: string) => {
    switch (type) {
      case 'show_file_upload':
        return {
          max_files: 3,
          max_size_mb: 10,
          accepted_types: ['image/png', 'image/jpeg', 'application/pdf'],
          upload_url: '/api/mock-upload'
        };
      
      case 'request_email':
        return {
          prompt: 'Please enter your email address for testing:',
          validation_regex: '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$'
        };
      
      case 'display_form':
        return {
          title: 'Test Form',
          fields: [
            { name: 'name', label: 'Name', type: 'text', required: true },
            { name: 'age', label: 'Age', type: 'number', required: false }
          ],
          submit_label: 'Submit Test'
        };
      
      case 'show_confirmation_dialog':
        return {
          title: 'Confirm Action',
          message: 'This is a test confirmation. Do you want to proceed?',
          confirm_label: 'Yes, Proceed',
          cancel_label: 'No, Cancel'
        };
      
      default:
        return {};
    }
  };
  
  // Add entry to event log
  const addToEventLog = (message: string) => {
    setEventLog((prev) => {
      const now = new Date();
      const timestamp = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
      return [`[${timestamp}] ${message}`, ...prev.slice(0, 49)]; // Keep last 50 entries
    });
  };
  
  // Clear all instructions
  const clearAll = () => {
    uiInstructionStateManager.clear();
    addToEventLog('Cleared all instructions');
  };
  
  // Show conflict button only if there's an active instruction
  const canShowConflict = active !== null;
  
  // Register handlers for UI instruction responses
  useEffect(() => {
    const handleResponse = (event: Event) => {
      const customEvent = event as CustomEvent;
      const { instruction_type, instruction_id, response } = customEvent.detail;
      
      addToEventLog(`Received response from ${instruction_type} (ID: ${instruction_id}): ${JSON.stringify(response).substring(0, 100)}${JSON.stringify(response).length > 100 ? '...' : ''}`);
    };
    
    window.addEventListener('ui-instruction-response', handleResponse);
    
    return () => {
      window.removeEventListener('ui-instruction-response', handleResponse);
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#0b1021] text-white p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-center text-[#6d4aff]">UI Instruction State Management Demo</h1>
        <p className="mb-6 text-center opacity-80">This page demonstrates the advanced state management for UI instructions (Task 20.4).</p>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="bg-[#121833] p-5 rounded-lg mb-6">
              <h2 className="text-xl font-semibold mb-4 text-[#8c5eff]">UI Instruction Preview</h2>
              <div className="bg-[#0b1021] p-4 rounded min-h-[300px]">
                <UIInstructionsContainer />
              </div>
            </div>
            
            <div className="bg-[#121833] p-5 rounded-lg">
              <h2 className="text-xl font-semibold mb-4 text-[#8c5eff] flex justify-between">
                <span>Event Log</span>
                <button 
                  className="text-sm text-gray-400 hover:text-white"
                  onClick={() => setEventLog([])}
                >
                  Clear Log
                </button>
              </h2>
              <div className="bg-[#0b1021] p-4 rounded h-[200px] overflow-y-auto font-mono text-sm">
                {eventLog.length === 0 ? (
                  <p className="text-gray-400">No events recorded yet. Queue some instructions to see the log.</p>
                ) : (
                  <div className="space-y-1">
                    {eventLog.map((event, idx) => (
                      <div key={idx} className="border-b border-gray-800 pb-1">{event}</div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
          
          <div className="space-y-6">
            <div className="bg-[#121833] p-5 rounded-lg">
              <h2 className="text-xl font-semibold mb-4 text-[#8c5eff]">Queue Instructions</h2>
              
              <div className="space-y-3 mb-4">
                <button 
                  className="w-full bg-[#1a243b] hover:bg-[#242d4f] py-2 px-4 rounded text-left"
                  onClick={() => queueTestInstruction('show_file_upload', 'normal')}
                >
                  Queue File Upload (Normal Priority)
                </button>
                
                <button 
                  className="w-full bg-[#1a243b] hover:bg-[#242d4f] py-2 px-4 rounded text-left"
                  onClick={() => queueTestInstruction('request_email', 'low')}
                >
                  Queue Email Request (Low Priority)
                </button>
                
                <button 
                  className="w-full bg-[#1a243b] hover:bg-[#242d4f] py-2 px-4 rounded text-left"
                  onClick={() => queueTestInstruction('display_form', 'high')}
                >
                  Queue Form Display (High Priority)
                </button>
                
                <button 
                  className="w-full bg-[#1a243b] hover:bg-[#242d4f] py-2 px-4 rounded text-left"
                  onClick={() => queueTestInstruction('show_confirmation_dialog', 'normal')}
                >
                  Queue Confirmation Dialog (Normal Priority)
                </button>
                
                <button 
                  className="w-full bg-red-900 hover:bg-red-800 py-2 px-4 rounded text-left"
                  onClick={() => queueTestInstruction('request_email', 'high', 10000)}
                >
                  Queue Email with 10s Timeout (High Priority)
                </button>
                
                {canShowConflict && (
                  <button 
                    className="w-full bg-purple-900 hover:bg-purple-800 py-2 px-4 rounded text-left"
                    onClick={() => {
                      // Queue an instruction of the same type to test conflict resolution
                      if (active) {
                        queueTestInstruction(active.instruction.instruction_type, 'high');
                        addToEventLog(`Queued conflicting instruction of type ${active.instruction.instruction_type}`);
                      }
                    }}
                  >
                    Queue Conflicting Instruction (Same Type)
                  </button>
                )}
              </div>
              
              <button 
                className="w-full bg-[#6d4aff] hover:bg-[#5d3aef] py-2 px-4 rounded"
                onClick={clearAll}
              >
                Clear All Instructions
              </button>
            </div>
            
            <div className="bg-[#121833] p-5 rounded-lg">
              <h2 className="text-xl font-semibold mb-4 text-[#8c5eff]">Current State</h2>
              
              <div className="space-y-3">
                <div>
                  <h3 className="text-sm font-semibold text-gray-300">Active Instruction:</h3>
                  <div className="bg-[#0b1021] p-2 rounded mt-1 min-h-[40px]">
                    {active ? (
                      <div className="text-sm">
                        <span className="text-green-400">{active.instruction.instruction_type}</span>
                        <span className="text-gray-400"> (ID: {active.id})</span>
                        <div className="text-xs text-gray-500 mt-1">
                          Priority: {active.instruction.metadata.priority}, 
                          Agent: {active.agent_id || 'unknown'}
                        </div>
                      </div>
                    ) : (
                      <span className="text-gray-500 text-sm">No active instruction</span>
                    )}
                  </div>
                </div>
                
                <div>
                  <h3 className="text-sm font-semibold text-gray-300">
                    Queue Status:
                    <span className="ml-2 bg-[#1a243b] px-2 py-0.5 rounded text-xs">
                      {queue.filter(i => i.status === 'pending').length} pending, 
                      {queue.length} total
                    </span>
                  </h3>
                  <div className="bg-[#0b1021] p-2 rounded mt-1 max-h-[200px] overflow-y-auto">
                    {queue.length > 0 ? (
                      <div className="space-y-1">
                        {queue.map((instruction) => (
                          <div key={instruction.id} className="text-xs border-b border-gray-800 pb-1 flex items-center">
                            <span className={`inline-block w-2 h-2 rounded-full mr-2 ${
                              instruction.status === 'pending' ? 'bg-yellow-500' : 
                              instruction.status === 'deferred' ? 'bg-purple-500' :
                              instruction.status === 'completed' ? 'bg-green-500' :
                              instruction.status === 'error' ? 'bg-red-500' :
                              instruction.status === 'cancelled' ? 'bg-gray-500' :
                              instruction.status === 'superseded' ? 'bg-blue-500' :
                              'bg-gray-800'
                            }`}></span>
                            <span className="text-gray-300">{instruction.instruction.instruction_type}</span>
                            <span className="ml-2 text-gray-500">({instruction.status})</span>
                            {instruction.conflictsWith?.length > 0 && (
                              <span className="ml-2 bg-red-900 text-xs px-1 rounded">Conflicts: {instruction.conflictsWith.length}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span className="text-gray-500 text-sm">Queue is empty</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}