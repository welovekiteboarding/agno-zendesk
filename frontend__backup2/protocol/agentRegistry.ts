// agno-zendesk/frontend__backup2/protocol/agentRegistry.ts
// Agent Registry interface for UI Instruction Protocol integration
// This is a client-side interface to the backend Agent Registry

import { UIInstructionType } from "./uiInstruction";

// Agent information interface
export interface AgentInfo {
  id: string;
  name: string;
  description: string;
  priority: number;
  capabilities: {
    ui_instructions?: UIInstructionType[];
    [key: string]: any;
  };
  rateLimits?: {
    uiInstructionsPerMinute?: number;
    [key: string]: any;
  };
}

// Agent Registry interface
export interface AgentRegistry {
  // Get information about a specific agent
  getAgent(agentId: string): AgentInfo | null;
  
  // Check if an agent is registered
  hasAgent(agentId: string): boolean;
  
  // Get all registered agents
  getAllAgents(): AgentInfo[];
  
  // Check if an agent is authorized to use a specific instruction type
  isAuthorized(agentId: string, instructionType: UIInstructionType): boolean;
  
  // Get the priority of an agent (higher number = higher priority)
  getAgentPriority(agentId: string): number;
}

// Mock implementation for testing until the real Agent Registry is implemented
export class MockAgentRegistry implements AgentRegistry {
  private agents: Record<string, AgentInfo> = {
    "form_collector": {
      id: "form_collector",
      name: "Form Collection Agent",
      description: "Collects form information for ticket submission",
      priority: 2,
      capabilities: {
        ui_instructions: [
          "show_file_upload",
          "request_email",
          "display_form"
        ]
      },
      rateLimits: {
        uiInstructionsPerMinute: 5
      }
    },
    "email_verifier": {
      id: "email_verifier",
      name: "Email Verification Agent",
      description: "Verifies email addresses and sends confirmation links",
      priority: 1,
      capabilities: {
        ui_instructions: [
          "request_email",
          "show_confirmation_dialog"
        ]
      },
      rateLimits: {
        uiInstructionsPerMinute: 3
      }
    },
    "ticket_poster": {
      id: "ticket_poster",
      name: "Ticket Submission Agent",
      description: "Posts completed tickets to Zendesk",
      priority: 3,
      capabilities: {
        ui_instructions: [
          "show_progress_indicator",
          "show_confirmation_dialog"
        ]
      },
      rateLimits: {
        uiInstructionsPerMinute: 2
      }
    }
  };

  getAgent(agentId: string): AgentInfo | null {
    return this.agents[agentId] || null;
  }

  hasAgent(agentId: string): boolean {
    return !!this.agents[agentId];
  }

  getAllAgents(): AgentInfo[] {
    return Object.values(this.agents);
  }

  isAuthorized(agentId: string, instructionType: UIInstructionType): boolean {
    const agent = this.agents[agentId];
    if (!agent) return false;
    
    const allowedInstructions = agent.capabilities.ui_instructions || [];
    return allowedInstructions.includes(instructionType);
  }

  getAgentPriority(agentId: string): number {
    const agent = this.agents[agentId];
    return agent ? agent.priority : 0;
  }
}

// Create a singleton instance
export const agentRegistry = new MockAgentRegistry();