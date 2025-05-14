// agno-zendesk/frontend__backup2/protocol/uiInstructionVerifier.ts
// Verification system for UI Instructions that integrates with the Agent Registry

import { AgentRegistry, agentRegistry } from "./agentRegistry";
import { UIInstruction, UIInstructionValidationError, validateUIInstruction } from "./uiInstruction";

/**
 * Verifies UI Instructions against agent permissions using the Agent Registry
 */
export class UIInstructionVerifier {
  private agentRegistry: AgentRegistry;

  /**
   * Creates a new instance of the UI Instruction Verifier
   * @param agentRegistry The Agent Registry to use for verification
   */
  constructor(agentRegistry: AgentRegistry) {
    this.agentRegistry = agentRegistry;
  }

  /**
   * Verifies that an instruction is valid and that the sending agent is authorized to use it
   * @param instruction The UI Instruction to verify
   * @returns True if the instruction is valid and authorized
   * @throws UIInstructionValidationError if validation fails
   */
  verify(instruction: UIInstruction): boolean {
    // First, perform basic validation (structure, parameters, etc.)
    validateUIInstruction(instruction);

    // Get agent ID from instruction
    const agentId = instruction.metadata.agent_id;
    if (!agentId) {
      throw new UIInstructionValidationError("Missing agent_id in instruction metadata");
    }

    // Verify agent is registered
    if (!this.agentRegistry.hasAgent(agentId)) {
      throw new UIInstructionValidationError(`Unknown agent: ${agentId}`);
    }

    // Verify agent is authorized for this instruction type
    if (!this.agentRegistry.isAuthorized(agentId, instruction.instruction_type)) {
      throw new UIInstructionValidationError(
        `Agent ${agentId} not authorized to use ${instruction.instruction_type}`
      );
    }

    return true;
  }

  /**
   * Gets an agent's name from its ID
   * @param agentId The ID of the agent
   * @returns The name of the agent, or the ID if not found
   */
  getAgentName(agentId: string): string {
    const agent = this.agentRegistry.getAgent(agentId);
    return agent ? agent.name : agentId;
  }

  /**
   * Gets an agent's priority from its ID
   * @param agentId The ID of the agent
   * @returns The priority of the agent, or 0 if not found
   */
  getAgentPriority(agentId: string): number {
    return this.agentRegistry.getAgentPriority(agentId);
  }

  /**
   * Compares the priorities of two agents
   * @param agentIdA The ID of the first agent
   * @param agentIdB The ID of the second agent
   * @returns Positive if A has higher priority, negative if B has higher priority, 0 if equal
   */
  compareAgentPriorities(agentIdA: string, agentIdB: string): number {
    const priorityA = this.getAgentPriority(agentIdA);
    const priorityB = this.getAgentPriority(agentIdB);
    return priorityA - priorityB;
  }
}

// Create a singleton instance using the default agent registry
export const uiInstructionVerifier = new UIInstructionVerifier(agentRegistry);