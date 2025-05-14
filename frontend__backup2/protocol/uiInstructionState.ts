// agno-zendesk/frontend__backup2/protocol/uiInstructionState.ts

import { UIInstruction, UIInstructionType } from "./uiInstruction";
import { AgentRegistry, agentRegistry } from "./agentRegistry";
import { UIInstructionVerifier, uiInstructionVerifier } from "./uiInstructionVerifier";

// Extended status types for instructions
export type InstructionStatus = "pending" | "active" | "completed" | "cancelled" | "error" | "timeout" | "superseded" | "deferred";

// Event types for state manager logging
export type StateEventType = "enqueue" | "activate" | "complete" | "cancel" | "error" | "timeout" | "conflict" | "supersede" | "resume";

// Debug level for logging
export type DebugLevel = "none" | "error" | "warn" | "info" | "debug";

// Event log entry for tracing state changes
export interface StateEvent {
  type: StateEventType;
  timestamp: number;
  instructionId?: string;
  instructionType?: UIInstructionType;
  message?: string;
  details?: any;
}

// Enhanced instruction state with additional metadata
export interface UIInstructionState {
  id: string; // Unique identifier for this instruction instance
  instruction: UIInstruction;
  status: InstructionStatus;
  error?: string;
  startedAt?: number;
  completedAt?: number;
  timeoutMs?: number;
  agent_id?: string; // The agent that sent this instruction
  conflictsWith?: string[]; // IDs of instructions this conflicts with
  supersededBy?: string; // ID of instruction that superseded this one
  retryCount?: number; // Number of times this instruction has been retried
  persistenceKey?: string; // Key for persisting state across page reloads
}

// Configuration for the state manager
export interface UIInstructionStateManagerConfig {
  defaultTimeout: number; // Default timeout in milliseconds
  maxQueueLength: number; // Maximum number of instructions in queue
  enablePersistence: boolean; // Whether to persist state across page reloads
  storageKey: string; // Key for localStorage
  debugLevel: DebugLevel; // Level of debug logging
  autoResume: boolean; // Whether to automatically resume active instruction on page load
  conflictRules: Record<UIInstructionType, {
    conflicts: UIInstructionType[];
    supersedes: UIInstructionType[];
  }>; // Rules for conflict resolution
  rateLimits: {
    maxInstructionsPerMinute: number; // Maximum number of instructions per minute
    maxInstructionsPerAgent: Record<string, number>; // Maximum instructions per agent
  };
}

/**
 * Enhanced state manager for UI instructions with
 * - Prioritization
 * - Conflict resolution
 * - Timeout handling
 * - State persistence
 * - Debugging and logging
 */
export class UIInstructionStateManager {
  private queue: UIInstructionState[] = [];
  private active: UIInstructionState | null = null;
  private onChange: ((state: UIInstructionState | null) => void)[] = [];
  private onQueueChange: ((queue: UIInstructionState[]) => void)[] = [];
  private eventLog: StateEvent[] = [];
  private timeoutHandlers: Record<string, NodeJS.Timeout> = {};
  private instructionCounter: number = 0;
  private instructionTimestamps: number[] = []; // For rate limiting
  private instructionCountByAgent: Record<string, { count: number, resetTime: number }> = {};
  private agentRegistry: AgentRegistry;
  private verifier: UIInstructionVerifier;
  
  // Default configuration
  private config: UIInstructionStateManagerConfig = {
    defaultTimeout: 120000, // 2 minutes
    maxQueueLength: 10,
    enablePersistence: true,
    storageKey: 'agno_ui_instruction_state',
    debugLevel: 'error',
    autoResume: true,
    conflictRules: {
      'show_file_upload': {
        conflicts: ['show_file_upload', 'display_form'],
        supersedes: []
      },
      'request_email': {
        conflicts: ['request_email'],
        supersedes: []
      },
      'display_form': {
        conflicts: ['display_form', 'show_file_upload'],
        supersedes: []
      },
      'show_auth_prompt': {
        conflicts: ['show_auth_prompt'],
        supersedes: ['request_email']
      },
      'show_selection_menu': {
        conflicts: ['show_selection_menu'],
        supersedes: []
      },
      'show_progress_indicator': {
        conflicts: [],
        supersedes: []
      },
      'show_confirmation_dialog': {
        conflicts: ['show_confirmation_dialog'],
        supersedes: ['show_confirmation_dialog']
      }
    },
    rateLimits: {
      maxInstructionsPerMinute: 10,
      maxInstructionsPerAgent: {
        'form_collector': 5,
        'email_verifier': 3,
        'ticket_poster': 2
      }
    }
  };

  constructor(config?: Partial<UIInstructionStateManagerConfig>, registry?: AgentRegistry) {
    // Set up agent registry and verifier
    this.agentRegistry = registry || agentRegistry;
    this.verifier = new UIInstructionVerifier(this.agentRegistry);
    
    // Apply any custom configuration
    if (config) {
      this.config = { ...this.config, ...config };
    }

    // Initialize agent-specific rate limits from registry
    this.initializeRateLimits();

    // Load persisted state if enabled
    if (this.config.enablePersistence && typeof window !== 'undefined') {
      this.tryLoadPersistedState();
    }

    // Set up event listeners for window focus/blur if persistence is enabled
    if (this.config.enablePersistence && typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => this.persistState());
      
      // Auto-resume active instruction when tab becomes visible again
      if (this.config.autoResume) {
        window.addEventListener('visibilitychange', () => {
          if (document.visibilityState === 'visible') {
            this.tryLoadPersistedState();
          }
        });
      }
    }
  }
  
  /**
   * Initialize rate limits from Agent Registry
   */
  private initializeRateLimits() {
    const agents = this.agentRegistry.getAllAgents();
    const rateLimits: Record<string, number> = {};
    
    agents.forEach(agent => {
      rateLimits[agent.id] = agent.rateLimits?.uiInstructionsPerMinute || 
                             this.config.rateLimits.maxInstructionsPerMinute;
    });
    
    // Merge with existing configuration
    this.config.rateLimits.maxInstructionsPerAgent = {
      ...this.config.rateLimits.maxInstructionsPerAgent,
      ...rateLimits
    };
  }

  /**
   * Subscribe to changes in the active instruction
   * @param cb Callback function called when active instruction changes
   * @returns Unsubscribe function
   */
  subscribe(cb: (state: UIInstructionState | null) => void) {
    this.onChange.push(cb);
    return () => {
      this.onChange = this.onChange.filter((fn) => fn !== cb);
    };
  }

  /**
   * Subscribe to changes in the instruction queue
   * @param cb Callback function called when queue changes
   * @returns Unsubscribe function
   */
  subscribeToQueue(cb: (queue: UIInstructionState[]) => void) {
    this.onQueueChange.push(cb);
    return () => {
      this.onQueueChange = this.onQueueChange.filter((fn) => fn !== cb);
    };
  }

  /**
   * Notify subscribers of changes to active instruction
   */
  private notifyStateChange() {
    this.onChange.forEach((cb) => cb(this.active));
  }

  /**
   * Notify subscribers of changes to queue
   */
  private notifyQueueChange() {
    this.onQueueChange.forEach((cb) => cb(this.getQueue()));
  }

  /**
   * Generate a unique ID for an instruction
   */
  private generateInstructionId(): string {
    this.instructionCounter++;
    return `${Date.now()}-${this.instructionCounter}`;
  }

  /**
   * Log an event for debugging
   */
  private logEvent(event: StateEventType, message?: string, details?: any, instructionId?: string, instructionType?: UIInstructionType) {
    const logEvent: StateEvent = {
      type: event,
      timestamp: Date.now(),
      message,
      details,
      instructionId,
      instructionType
    };
    
    this.eventLog.push(logEvent);
    
    // Trim event log if it gets too large
    if (this.eventLog.length > 100) {
      this.eventLog = this.eventLog.slice(-100);
    }
    
    // Output to console if debug level is appropriate
    if (this.shouldLog(event)) {
      const logFn = event === 'error' ? console.error : 
                   (event === 'conflict' || event === 'supersede') ? console.warn : 
                   console.log;
      
      logFn(`[UI Instruction] ${event.toUpperCase()}: ${message || ''}`, details || '');
    }
  }

  /**
   * Determine if an event should be logged based on debug level
   */
  private shouldLog(event: StateEventType): boolean {
    const { debugLevel } = this.config;
    
    if (debugLevel === 'none') return false;
    if (debugLevel === 'error') return event === 'error';
    if (debugLevel === 'warn') return ['error', 'conflict', 'supersede', 'timeout'].includes(event);
    if (debugLevel === 'info') return event !== 'debug';
    return true; // debug level
  }

  /**
   * Check if rate limits have been exceeded
   */
  private checkRateLimits(agentId?: string): boolean {
    // Check global rate limit
    const now = Date.now();
    const oneMinuteAgo = now - 60000;
    
    // Remove timestamps older than 1 minute
    this.instructionTimestamps = this.instructionTimestamps.filter(ts => ts > oneMinuteAgo);
    
    // Check if we're over the global limit
    if (this.instructionTimestamps.length >= this.config.rateLimits.maxInstructionsPerMinute) {
      this.logEvent('error', 'Global rate limit exceeded', { 
        limit: this.config.rateLimits.maxInstructionsPerMinute,
        current: this.instructionTimestamps.length 
      });
      return false;
    }
    
    // Check agent-specific rate limit if agent ID is provided
    if (agentId) {
      const agentLimit = this.config.rateLimits.maxInstructionsPerAgent[agentId];
      
      if (agentLimit) {
        // Initialize agent counter if not exists
        if (!this.instructionCountByAgent[agentId]) {
          this.instructionCountByAgent[agentId] = { count: 0, resetTime: now + 60000 };
        }
        
        const agentCounter = this.instructionCountByAgent[agentId];
        
        // Reset counter if time has passed
        if (now > agentCounter.resetTime) {
          agentCounter.count = 0;
          agentCounter.resetTime = now + 60000;
        }
        
        // Check if agent is over their limit
        if (agentCounter.count >= agentLimit) {
          this.logEvent('error', `Agent rate limit exceeded for ${agentId}`, { 
            limit: agentLimit, 
            current: agentCounter.count 
          });
          return false;
        }
        
        // Increment agent counter
        agentCounter.count++;
      }
    }
    
    // Add current timestamp to the list
    this.instructionTimestamps.push(now);
    
    return true;
  }

  /**
   * Check if an instruction conflicts with any existing instructions
   * If it supersedes other instructions, mark them as superseded
   * Uses Agent Registry for priority-based conflict resolution
   */
  private handleConflicts(newState: UIInstructionState): string[] {
    const conflicts: string[] = [];
    const superseded: string[] = [];
    
    const instructionType = newState.instruction.instruction_type;
    const agentId = newState.instruction.metadata.agent_id;
    
    // Skip conflict checking if no conflict rules exist
    if (!this.config.conflictRules[instructionType]) {
      return conflicts;
    }
    
    // Get conflict and supersede rules for this instruction type
    const { conflicts: conflictTypes, supersedes: supersedeTypes } = this.config.conflictRules[instructionType];
    
    // Check each instruction in the queue for conflicts
    this.queue.forEach(queuedState => {
      // Skip if this is the same instruction
      if (queuedState.id === newState.id) return;
      
      const queuedType = queuedState.instruction.instruction_type;
      const queuedAgentId = queuedState.agent_id;
      
      // Check if this instruction conflicts with the queued instruction
      if (conflictTypes.includes(queuedType)) {
        // If from same agent, newer one takes precedence
        if (agentId && queuedAgentId === agentId) {
          // Mark the older instruction as superseded
          queuedState.status = 'superseded';
          queuedState.supersededBy = newState.id;
          superseded.push(queuedState.id);
          
          this.logEvent('supersede', 
            `Instruction ${queuedState.id} (${queuedType}) superseded by ${newState.id} (${instructionType})`,
            { oldInstruction: queuedState, newInstruction: newState },
            queuedState.id,
            queuedType
          );
        } else if (agentId && queuedAgentId) {
          // Different agents - use priority to determine precedence
          const comparison = this.verifier.compareAgentPriorities(agentId, queuedAgentId);
          
          // Higher priority agent's instruction supersedes lower priority agent's instruction
          if (comparison > 0) {
            // New instruction is from higher priority agent
            queuedState.status = 'superseded';
            queuedState.supersededBy = newState.id;
            superseded.push(queuedState.id);
            
            const newAgentName = this.verifier.getAgentName(agentId);
            const queuedAgentName = this.verifier.getAgentName(queuedAgentId);
            
            this.logEvent('supersede', 
              `Instruction ${queuedState.id} from ${queuedAgentName} superseded by ${newState.id} from ${newAgentName} (higher priority)`,
              { oldInstruction: queuedState, newInstruction: newState, priorityDiff: comparison },
              queuedState.id,
              queuedType
            );
          } else if (comparison < 0) {
            // Queued instruction is from higher priority agent - record conflict
            conflicts.push(queuedState.id);
            
            const newAgentName = this.verifier.getAgentName(agentId);
            const queuedAgentName = this.verifier.getAgentName(queuedAgentId);
            
            this.logEvent('conflict', 
              `Instruction ${newState.id} from ${newAgentName} conflicts with ${queuedState.id} from ${queuedAgentName} (higher priority)`,
              { instruction: newState, conflict: queuedState, priorityDiff: comparison },
              newState.id,
              instructionType
            );
          } else {
            // Equal priority - use instruction priority as tiebreaker
            const newPriority = this.priorityValue(newState);
            const queuedPriority = this.priorityValue(queuedState);
            
            if (newPriority > queuedPriority) {
              queuedState.status = 'superseded';
              queuedState.supersededBy = newState.id;
              superseded.push(queuedState.id);
              
              this.logEvent('supersede', 
                `Instruction ${queuedState.id} (${queuedType}) superseded by ${newState.id} (${instructionType}) (higher instruction priority)`,
                { oldInstruction: queuedState, newInstruction: newState },
                queuedState.id,
                queuedType
              );
            } else {
              // Record as conflict
              conflicts.push(queuedState.id);
            }
          }
        } else {
          // Missing agent ID on one or both instructions - fall back to default behavior
          conflicts.push(queuedState.id);
        }
      }
      
      // Check if this instruction supersedes the queued instruction by type
      if (supersedeTypes.includes(queuedType)) {
        // Mark the queued instruction as superseded
        queuedState.status = 'superseded';
        queuedState.supersededBy = newState.id;
        superseded.push(queuedState.id);
        
        this.logEvent('supersede', 
          `Instruction ${queuedState.id} (${queuedType}) superseded by ${newState.id} (${instructionType}) (rule-based)`,
          { oldInstruction: queuedState, newInstruction: newState },
          queuedState.id,
          queuedType
        );
      }
    });
    
    // If we have active instruction, also check for conflicts/supersedes
    if (this.active) {
      const activeType = this.active.instruction.instruction_type;
      const activeAgentId = this.active.agent_id;
      
      // Check for conflict with active instruction
      if (conflictTypes.includes(activeType)) {
        // If from same agent, newer one takes precedence
        if (agentId && activeAgentId === agentId) {
          // Cancel the active instruction
          this.cancelActive(`Superseded by new instruction ${newState.id}`);
          superseded.push(this.active.id);
        } else if (agentId && activeAgentId) {
          // Different agents - use priority to determine precedence
          const comparison = this.verifier.compareAgentPriorities(agentId, activeAgentId);
          
          if (comparison > 0) {
            // New instruction is from higher priority agent
            this.cancelActive(`Superseded by higher priority agent instruction ${newState.id}`);
            superseded.push(this.active.id);
          } else if (comparison < 0) {
            // Active instruction is from higher priority agent
            conflicts.push(this.active.id);
          } else {
            // Equal priority - use instruction priority as tiebreaker
            const newPriority = this.priorityValue(newState);
            const activePriority = this.priorityValue(this.active);
            
            if (newPriority > activePriority) {
              this.deferActive(`Deferred for higher priority instruction ${newState.id}`);
            } else {
              conflicts.push(this.active.id);
            }
          }
        } else {
          // Missing agent ID on one or both instructions - fall back to instruction priority
          if (newState.instruction.metadata.priority === 'high' && 
              this.active.instruction.metadata.priority !== 'high') {
            this.deferActive(`Deferred for higher priority instruction ${newState.id}`);
          } else {
            conflicts.push(this.active.id);
          }
        }
      }
      
      // Check if this instruction supersedes the active instruction by type
      if (supersedeTypes.includes(activeType)) {
        // Cancel the active instruction
        this.cancelActive(`Superseded by new instruction ${newState.id} (rule-based)`);
        superseded.push(this.active.id);
      }
    }
    
    // Record any conflicts
    if (conflicts.length > 0) {
      newState.conflictsWith = conflicts;
      
      this.logEvent('conflict', 
        `Instruction ${newState.id} (${instructionType}) conflicts with ${conflicts.join(', ')}`,
        { instruction: newState, conflicts },
        newState.id,
        instructionType
      );
    }
    
    return conflicts;
  }

  /**
   * Add a new instruction to the queue
   */
  enqueue(instruction: UIInstruction, timeoutMs?: number): string | null {
    try {
      // Verify the instruction against the agent registry
      this.verifier.verify(instruction);
      
      // Check if we're over the queue length limit
      if (this.queue.length >= this.config.maxQueueLength) {
        this.logEvent('error', 'Queue length limit exceeded, dropping instruction', { 
          limit: this.config.maxQueueLength,
          instruction 
        });
        return null;
      }
      
      // Check rate limits
      const agentId = instruction.metadata.agent_id;
      if (!this.checkRateLimits(agentId)) {
        return null;
      }
      
      // Create a unique ID for this instruction
      const id = this.generateInstructionId();
      
      // Create the instruction state
      const state: UIInstructionState = {
        id,
        instruction,
        status: "pending",
        timeoutMs: timeoutMs ?? this.config.defaultTimeout,
        agent_id: agentId,
        retryCount: 0
      };
      
      // Check for conflicts and superseded instructions
      this.handleConflicts(state);
      
      // Add to the queue
      this.queue.push(state);
      
      // Re-sort the queue by priority
      this.sortQueue();
      
      // Log with agent name for better traceability
      const agentName = this.verifier.getAgentName(agentId || "");
      this.logEvent('enqueue', 
        `Instruction ${id} (${instruction.instruction_type}) queued from agent ${agentName}`, 
        { instruction, timeoutMs, agentName }, 
        id, 
        instruction.instruction_type
      );
      
      // Try to activate the next instruction
      this.tryActivateNext();
      
      // Notify subscribers
      this.notifyQueueChange();
      
      // Persist state if enabled
      if (this.config.enablePersistence) {
        this.persistState();
      }
      
      return id;
    } catch (error) {
      // Log verification errors
      this.logEvent('error', 
        `Instruction validation failed: ${error instanceof Error ? error.message : String(error)}`, 
        { instruction, error }
      );
      return null;
    }
  }

  /**
   * Sort the queue by priority and sequence
   */
  private sortQueue() {
    this.queue.sort((a, b) => {
      // First sort by status - pending items come first
      if (a.status === 'pending' && b.status !== 'pending') return -1;
      if (a.status !== 'pending' && b.status === 'pending') return 1;
      
      // Then sort by priority
      const priorityDiff = this.priorityValue(b) - this.priorityValue(a);
      if (priorityDiff !== 0) return priorityDiff;
      
      // Then sort by sequence number if present
      const aSeq = a.instruction.metadata.sequence;
      const bSeq = b.instruction.metadata.sequence;
      
      if (aSeq !== undefined && bSeq !== undefined) {
        return aSeq - bSeq;
      }
      
      // Finally sort by ID (timestamp) for consistent ordering
      return a.id.localeCompare(b.id);
    });
  }

  /**
   * Convert priority string to numeric value for sorting
   */
  private priorityValue(state: UIInstructionState): number {
    const p = state.instruction.metadata.priority;
    if (p === "high") return 2;
    if (p === "low") return 0;
    return 1;
  }

  /**
   * Try to activate the next pending instruction
   */
  private tryActivateNext() {
    // Don't try to activate if there's already an active instruction
    if (this.active && this.active.status === "active") return;
    
    // Find the next pending instruction
    const next = this.queue.find((s) => s.status === "pending");
    
    if (next) {
      // Mark as active
      next.status = "active";
      next.startedAt = Date.now();
      this.active = next;
      
      this.logEvent('activate', 
        `Instruction ${next.id} (${next.instruction.instruction_type}) activated`, 
        { instruction: next }, 
        next.id, 
        next.instruction.instruction_type
      );
      
      // Start the timeout
      this.startTimeout(next);
      
      // Notify subscribers
      this.notifyStateChange();
      this.notifyQueueChange();
      
      // Persist state if enabled
      if (this.config.enablePersistence) {
        this.persistState();
      }
    }
  }

  /**
   * Start the timeout for an instruction
   */
  private startTimeout(state: UIInstructionState) {
    if (!state.timeoutMs) return;
    
    // Clear any existing timeout for this instruction
    if (this.timeoutHandlers[state.id]) {
      clearTimeout(this.timeoutHandlers[state.id]);
    }
    
    // Set the new timeout
    this.timeoutHandlers[state.id] = setTimeout(() => {
      // Only proceed if the instruction is still active
      if (state.status === "active" && state.startedAt && Date.now() - state.startedAt >= state.timeoutMs!) {
        state.status = "timeout";
        state.error = "User did not respond in time.";
        this.active = null;
        
        this.logEvent('timeout', 
          `Instruction ${state.id} (${state.instruction.instruction_type}) timed out after ${state.timeoutMs}ms`, 
          { instruction: state }, 
          state.id, 
          state.instruction.instruction_type
        );
        
        // Try to activate the next instruction
        this.tryActivateNext();
        
        // Notify subscribers
        this.notifyStateChange();
        this.notifyQueueChange();
        
        // Persist state if enabled
        if (this.config.enablePersistence) {
          this.persistState();
        }
      }
    }, state.timeoutMs);
  }

  /**
   * Mark the active instruction as completed
   */
  completeActive(response?: any) {
    if (this.active) {
      const id = this.active.id;
      const type = this.active.instruction.instruction_type;
      
      this.active.status = "completed";
      this.active.completedAt = Date.now();
      
      this.logEvent('complete', 
        `Instruction ${id} (${type}) completed`, 
        { instruction: this.active, response }, 
        id, 
        type
      );
      
      // Clean up timeout
      if (this.timeoutHandlers[id]) {
        clearTimeout(this.timeoutHandlers[id]);
        delete this.timeoutHandlers[id];
      }
      
      // Clear active instruction
      this.active = null;
      
      // Try to activate the next instruction
      this.tryActivateNext();
      
      // Notify subscribers
      this.notifyStateChange();
      this.notifyQueueChange();
      
      // Persist state if enabled
      if (this.config.enablePersistence) {
        this.persistState();
      }
    }
  }

  /**
   * Mark the active instruction as cancelled
   */
  cancelActive(reason?: string) {
    if (this.active) {
      const id = this.active.id;
      const type = this.active.instruction.instruction_type;
      
      this.active.status = "cancelled";
      this.active.error = reason || "Cancelled by user/system.";
      this.active.completedAt = Date.now();
      
      this.logEvent('cancel', 
        `Instruction ${id} (${type}) cancelled: ${reason || 'No reason provided'}`, 
        { instruction: this.active }, 
        id, 
        type
      );
      
      // Clean up timeout
      if (this.timeoutHandlers[id]) {
        clearTimeout(this.timeoutHandlers[id]);
        delete this.timeoutHandlers[id];
      }
      
      // Clear active instruction
      this.active = null;
      
      // Try to activate the next instruction
      this.tryActivateNext();
      
      // Notify subscribers
      this.notifyStateChange();
      this.notifyQueueChange();
      
      // Persist state if enabled
      if (this.config.enablePersistence) {
        this.persistState();
      }
    }
  }

  /**
   * Mark the active instruction as deferred (to be resumed later)
   */
  deferActive(reason?: string) {
    if (this.active) {
      const id = this.active.id;
      const type = this.active.instruction.instruction_type;
      
      this.active.status = "deferred";
      this.active.error = reason || "Deferred for higher priority instruction.";
      
      this.logEvent('cancel', 
        `Instruction ${id} (${type}) deferred: ${reason || 'No reason provided'}`, 
        { instruction: this.active }, 
        id, 
        type
      );
      
      // Clean up timeout
      if (this.timeoutHandlers[id]) {
        clearTimeout(this.timeoutHandlers[id]);
        delete this.timeoutHandlers[id];
      }
      
      // Move the instruction back to the queue
      this.queue.unshift({...this.active, status: 'pending'});
      
      // Clear active instruction
      this.active = null;
      
      // Try to activate the next instruction
      this.tryActivateNext();
      
      // Notify subscribers
      this.notifyStateChange();
      this.notifyQueueChange();
      
      // Persist state if enabled
      if (this.config.enablePersistence) {
        this.persistState();
      }
    }
  }

  /**
   * Mark the active instruction as error
   */
  errorActive(errorMsg: string) {
    if (this.active) {
      const id = this.active.id;
      const type = this.active.instruction.instruction_type;
      
      this.active.status = "error";
      this.active.error = errorMsg;
      this.active.completedAt = Date.now();
      
      this.logEvent('error', 
        `Instruction ${id} (${type}) error: ${errorMsg}`, 
        { instruction: this.active }, 
        id, 
        type
      );
      
      // Clean up timeout
      if (this.timeoutHandlers[id]) {
        clearTimeout(this.timeoutHandlers[id]);
        delete this.timeoutHandlers[id];
      }
      
      // Clear active instruction
      this.active = null;
      
      // Try to activate the next instruction
      this.tryActivateNext();
      
      // Notify subscribers
      this.notifyStateChange();
      this.notifyQueueChange();
      
      // Persist state if enabled
      if (this.config.enablePersistence) {
        this.persistState();
      }
    }
  }

  /**
   * Retry a failed instruction
   */
  retryInstruction(id: string): boolean {
    // Find the instruction in the queue
    const instruction = this.queue.find(s => s.id === id);
    
    if (!instruction) {
      this.logEvent('error', `Cannot retry instruction ${id}: not found`);
      return false;
    }
    
    // Only retry if status is error, timeout, or cancelled
    if (!['error', 'timeout', 'cancelled'].includes(instruction.status)) {
      this.logEvent('error', `Cannot retry instruction ${id}: status is ${instruction.status}`);
      return false;
    }
    
    // Increment retry count
    instruction.retryCount = (instruction.retryCount || 0) + 1;
    
    // Reset instruction state
    instruction.status = 'pending';
    instruction.error = undefined;
    instruction.startedAt = undefined;
    instruction.completedAt = undefined;
    
    this.logEvent('enqueue', 
      `Instruction ${id} (${instruction.instruction.instruction_type}) retried (attempt ${instruction.retryCount})`, 
      { instruction }, 
      id, 
      instruction.instruction.instruction_type
    );
    
    // Re-sort the queue
    this.sortQueue();
    
    // Try to activate the next instruction
    this.tryActivateNext();
    
    // Notify subscribers
    this.notifyQueueChange();
    
    // Persist state if enabled
    if (this.config.enablePersistence) {
      this.persistState();
    }
    
    return true;
  }

  /**
   * Resume a deferred instruction
   */
  resumeInstruction(id: string): boolean {
    // Find the instruction in the queue
    const instruction = this.queue.find(s => s.id === id);
    
    if (!instruction) {
      this.logEvent('error', `Cannot resume instruction ${id}: not found`);
      return false;
    }
    
    // Only resume if status is deferred
    if (instruction.status !== 'deferred') {
      this.logEvent('error', `Cannot resume instruction ${id}: status is ${instruction.status}`);
      return false;
    }
    
    // Reset instruction state
    instruction.status = 'pending';
    instruction.error = undefined;
    
    this.logEvent('resume', 
      `Instruction ${id} (${instruction.instruction.instruction_type}) resumed`, 
      { instruction }, 
      id, 
      instruction.instruction.instruction_type
    );
    
    // Re-sort the queue
    this.sortQueue();
    
    // Try to activate the next instruction
    this.tryActivateNext();
    
    // Notify subscribers
    this.notifyQueueChange();
    
    // Persist state if enabled
    if (this.config.enablePersistence) {
      this.persistState();
    }
    
    return true;
  }

  /**
   * Get the currently active instruction state
   */
  getActive(): UIInstructionState | null {
    return this.active;
  }

  /**
   * Get the current instruction queue
   */
  getQueue(): UIInstructionState[] {
    return this.queue.slice();
  }

  /**
   * Get a specific instruction by ID
   */
  getInstructionById(id: string): UIInstructionState | null {
    // Check active instruction first
    if (this.active && this.active.id === id) {
      return this.active;
    }
    
    // Then check queue
    return this.queue.find(s => s.id === id) || null;
  }

  /**
   * Get instruction status by ID
   */
  getInstructionStatus(id: string): InstructionStatus | null {
    const instruction = this.getInstructionById(id);
    return instruction ? instruction.status : null;
  }

  /**
   * Get the event log
   */
  getEventLog(): StateEvent[] {
    return this.eventLog.slice();
  }

  /**
   * Clear the queue and active instruction
   */
  clear() {
    // Clean up all timeouts
    Object.keys(this.timeoutHandlers).forEach(id => {
      clearTimeout(this.timeoutHandlers[id]);
      delete this.timeoutHandlers[id];
    });
    
    this.queue = [];
    this.active = null;
    
    this.logEvent('cancel', 'Instruction queue cleared');
    
    // Notify subscribers
    this.notifyStateChange();
    this.notifyQueueChange();
    
    // Clear persisted state if enabled
    if (this.config.enablePersistence && typeof window !== 'undefined') {
      localStorage.removeItem(this.config.storageKey);
    }
  }

  /**
   * Clear completed, cancelled, error, and superseded instructions from the queue
   */
  cleanup() {
    // Filter out instructions that are done
    this.queue = this.queue.filter(s => 
      !['completed', 'cancelled', 'error', 'superseded', 'timeout'].includes(s.status)
    );
    
    this.logEvent('cancel', 'Completed instructions cleaned up from queue');
    
    // Notify subscribers
    this.notifyQueueChange();
    
    // Persist state if enabled
    if (this.config.enablePersistence) {
      this.persistState();
    }
  }

  /**
   * Persist the current state to localStorage
   */
  private persistState() {
    if (!this.config.enablePersistence || typeof window === 'undefined') {
      return;
    }
    
    try {
      const state = {
        queue: this.queue,
        active: this.active,
        timestamp: Date.now()
      };
      
      localStorage.setItem(this.config.storageKey, JSON.stringify(state));
    } catch (error) {
      this.logEvent('error', 'Failed to persist state', { error });
    }
  }

  /**
   * Try to load persisted state from localStorage
   */
  private tryLoadPersistedState() {
    if (!this.config.enablePersistence || typeof window === 'undefined') {
      return;
    }
    
    try {
      const savedState = localStorage.getItem(this.config.storageKey);
      
      if (!savedState) {
        return;
      }
      
      const state = JSON.parse(savedState);
      
      // Check if state is too old (older than 1 hour)
      if (state.timestamp && Date.now() - state.timestamp > 3600000) {
        localStorage.removeItem(this.config.storageKey);
        return;
      }
      
      // Restore queue and active instruction
      this.queue = state.queue || [];
      this.active = state.active;
      
      if (this.active && this.active.status === 'active') {
        // Restart timeout for active instruction
        this.startTimeout(this.active);
      }
      
      this.logEvent('info', 'Restored persisted state', { 
        queueLength: this.queue.length,
        hasActiveInstruction: !!this.active 
      });
      
      // Notify subscribers
      this.notifyStateChange();
      this.notifyQueueChange();
    } catch (error) {
      this.logEvent('error', 'Failed to load persisted state', { error });
      
      // Clear invalid saved state
      localStorage.removeItem(this.config.storageKey);
    }
  }

  /**
   * Serialize the current state to JSON
   */
  serialize(): string {
    return JSON.stringify({
      queue: this.queue,
      active: this.active,
      timestamp: Date.now()
    });
  }

  /**
   * Create a state manager from serialized state
   */
  static deserialize(jsonStr: string, config?: Partial<UIInstructionStateManagerConfig>): UIInstructionStateManager {
    const obj = JSON.parse(jsonStr);
    const mgr = new UIInstructionStateManager(config);
    
    mgr.queue = obj.queue || [];
    mgr.active = obj.active || null;
    
    if (mgr.active && mgr.active.status === 'active') {
      // Restart timeout for active instruction
      mgr.startTimeout(mgr.active);
    }
    
    return mgr;
  }

  /**
   * Update the configuration
   */
  updateConfig(config: Partial<UIInstructionStateManagerConfig>) {
    this.config = { ...this.config, ...config };
  }

  /**
   * Get the current configuration
   */
  getConfig(): UIInstructionStateManagerConfig {
    return { ...this.config };
  }
}

// Singleton instance for app-wide use
export const uiInstructionStateManager = new UIInstructionStateManager(undefined, agentRegistry);

// Export a simple helper function to enqueue instructions
export function queueInstruction(instruction: UIInstruction, timeoutMs?: number): string | null {
  return uiInstructionStateManager.enqueue(instruction, timeoutMs);
}

// Export a helper function to get agent name from ID
export function getAgentName(agentId: string): string {
  return uiInstructionVerifier.getAgentName(agentId);
}