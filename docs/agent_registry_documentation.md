# Agent Registry & Handoff Protocol Guide

This guide documents the Agent Registry system, which provides a centralized registry for AI agents with a standardized handoff protocol. The Agent Registry enables a modular, extensible multi-agent system by handling agent registration, discovery, and seamless transitions between agents.

## Table of Contents

1. [Introduction](#1-introduction)
2. [Architecture Overview](#2-architecture-overview)
3. [Agent Registry Core](#3-agent-registry-core)
4. [Agent Registration](#4-agent-registration)
5. [Agent Capabilities](#5-agent-capabilities)
6. [Handoff Protocol](#6-handoff-protocol)
7. [Configuration System](#7-configuration-system)
8. [Integration with UI Instruction Protocol](#8-integration-with-ui-instruction-protocol)
9. [Best Practices](#9-best-practices)
10. [Common Patterns & Examples](#10-common-patterns--examples)

## 1. Introduction

The Agent Registry is a core infrastructure component that enables a multi-agent architecture. Instead of hard-coding agent interactions, the registry provides a flexible, configuration-driven approach to agent management. Key features include:

- Centralized registry of all available agents with their metadata
- Standardized agent registration API
- Dynamic handoff between agents based on triggers and conditions
- Configuration-driven agent instantiation
- Integration with the UI Instruction Protocol for frontend interactions

This system enables:

- Adding new agent types without changing existing code
- Standardized agent-to-agent handoff with context preservation
- Dynamic discovery of agent capabilities
- Permission management for UI instructions

## 2. Architecture Overview

The Agent Registry architecture consists of several components:

```
┌─────────────────────────────────┐
│         Agent Registry          │
├─────────────────────────────────┤
│ - Registered Agent Types        │
│ - Agent Instances               │
│ - Configuration Management      │
│ - Agent Discovery               │
│ - Handoff Trigger Evaluation    │
└──────────────┬──────────────────┘
               │
     ┌─────────▼────────┐
     │  Handoff Manager │
     └─────────┬────────┘
               │
     ┌─────────▼────────┐
     │  Session Manager │
     └─────────┬────────┘
               │
┌──────────────▼─────────────────┐
│       Orchestrator API         │
└──────────────────────────────────┘
```

**Key Components:**

- **Agent Registry**: Central registry of agent types and instances
- **Handoff Manager**: Handles agent transitions and context transfer
- **Session Manager**: Tracks user sessions and active agents
- **Orchestrator API**: Exposes the multi-agent system to clients

## 3. Agent Registry Core

The core of the system is the `AgentRegistry` class that maintains a collection of registered agents and their metadata.

### Key Concepts

- **Agent Type**: A class of agent with specific capabilities and behavior (e.g., Form Collector, Email Verifier)
- **Agent Instance**: A specific instance of an agent type assigned to a user session
- **Agent Metadata**: Information about an agent, including its capabilities and handoff triggers
- **Capability**: A specific function an agent can perform (e.g., form collection, email verification)
- **Handoff Trigger**: A condition that causes control to be transferred from one agent to another

### Accessing the Registry

```python
from backend.agent_registry import get_registry

# Get the singleton registry instance
registry = get_registry()

# Get all registered agent types
agent_types = registry.get_agent_types()

# Get agents with a specific capability
form_agents = registry.get_agents_by_capability(CapabilityType.FORM_COLLECTION)

# Check if an agent can use a UI instruction
can_upload = registry.is_authorized_for_ui_instruction("form_collector", "show_file_upload")
```

## 4. Agent Registration

There are two ways to register an agent:

### 1. Using the Decorator

```python
from backend.agent_registry import register_agent, AgentCapability, CapabilityType
from backend.agents.base_agent import BaseAgent

@register_agent(
    id="my_agent",
    name="My Custom Agent",
    description="A custom agent that does something useful",
    version="1.0.0",
    capabilities={
        "my_capability": AgentCapability(
            type=CapabilityType.DATA_EXTRACTION,
            description="Extracts data from user messages",
            ui_instructions=["show_selection_menu"]
        )
    },
    handoff_triggers=[
        HandoffTrigger(
            target_agent_id="other_agent",
            description="Handoff when data extraction is complete",
            condition_function="my_module.is_extraction_complete"
        )
    ]
)
class MyCustomAgent(BaseAgent):
    def process_message(self, message, context):
        # Implementation
        pass
```

### 2. Manual Registration

```python
from backend.agent_registry import get_registry, AgentMetadata

# Create metadata
metadata = AgentMetadata(
    id="my_agent",
    name="My Custom Agent",
    description="A custom agent that does something useful",
    version="1.0.0",
    capabilities={...},
    handoff_triggers=[...]
)

# Register the agent
registry = get_registry()
registry.register_agent_type(metadata, MyCustomAgent)
```

## 5. Agent Capabilities

Capabilities define what an agent can do. Each capability has:

- **Type**: The category of capability (e.g., form collection, data extraction)
- **Description**: Human-readable description of the capability
- **Parameters**: Optional configuration parameters for the capability
- **UI Instructions**: Which UI instructions this capability can use

Example capabilities:

```python
capabilities = {
    "form_collection": AgentCapability(
        type=CapabilityType.FORM_COLLECTION,
        description="Collects structured form data based on a JSON schema",
        ui_instructions=["show_file_upload", "request_email", "display_form"]
    ),
    "email_verification": AgentCapability(
        type=CapabilityType.EMAIL_VERIFICATION,
        description="Verifies email addresses against Zendesk",
        ui_instructions=["request_email", "show_confirmation_dialog"]
    )
}
```

## 6. Handoff Protocol

Handoffs enable seamless transitions between agents. Each agent can define triggers for when to hand off to another agent.

### Handoff Triggers

Triggers can be defined by:

1. **Condition Functions**: Custom Python functions that return True/False
2. **Keyword Patterns**: Regex patterns to match in user messages
3. **Intent Names**: Specific intent names detected in the conversation

Example trigger:

```python
handoff_triggers = [
    HandoffTrigger(
        target_agent_id="email_verifier",
        description="Form collection complete, needs email verification",
        priority=2,
        condition_function="backend.agents.form_collector_agent.is_form_complete"
    ),
    HandoffTrigger(
        target_agent_id="ticket_poster",
        description="User explicitly wants to submit the ticket",
        keyword_patterns=["submit(?: the)? ticket", "create(?: the)? ticket"]
    )
]
```

### Handoff Process

1. The orchestrator receives a user message
2. It evaluates handoff triggers for the current agent
3. If a trigger matches, it initiates a handoff to the target agent
4. The handoff context is created with session data
5. The target agent receives the handoff context and takes over

### Context Transfer

During a handoff, the following context is transferred:

- Source and target agent information
- Session ID and timestamp
- Relevant message history
- Collected data from previous agents
- Reason for the handoff

## 7. Configuration System

Agents can be configured via YAML or JSON files. This enables easy adjustments to agent behavior without code changes.

### Configuration Format

```yaml
# Agent instances to create on startup
agents:
  - agent_id: agno_assistant
    enabled: true
    params:
      model_name: "claude-3-5-sonnet"
      temperature: 0.7
      
  - agent_id: form_collector
    enabled: true
    params:
      schema_path: "schemas/bug_report_schema.json"
      max_retries: 3

# Default agent to use when a session starts
default_agent_id: agno_assistant

# Whether to hot-reload when config changes
hot_reload: true
```

### Loading Configuration

```python
from backend.agent_registry import get_registry

registry = get_registry()
registry.load_config("config/agents.yaml")
```

## 8. Integration with UI Instruction Protocol

The Agent Registry integrates with the UI Instruction Protocol to control which agents can use which UI instructions.

### UI Instruction Authorization

```python
# Check if an agent can use a specific UI instruction
registry = get_registry()
can_use = registry.is_authorized_for_ui_instruction("form_collector", "show_file_upload")

# Find all agents that can use a specific UI instruction
upload_agents = registry.find_agents_by_ui_instruction("show_file_upload")
```

### UI Instruction Creation

```python
from backend.protocol.ui_instruction import create_file_upload_instruction

# Create a UI instruction with agent authorization check
instruction = create_file_upload_instruction(
    max_files=3,
    max_size_mb=10,
    accepted_types=["image/png", "image/jpeg"],
    upload_url="/api/upload",
    agent_id="form_collector"
)
```

## 9. Best Practices

When using the Agent Registry, follow these best practices:

### Agent Design

- **Single Responsibility**: Each agent should have a clear, focused purpose
- **Clear Handoff Conditions**: Handoff triggers should be specific and deterministic
- **Explicit Capabilities**: Document all capabilities an agent provides
- **Minimal Dependencies**: Minimize dependencies between agents

### Registration

- **Use Decorators**: Use the `@register_agent` decorator for clear agent registration
- **Version Agents**: Always include a semantic version for each agent
- **Document Triggers**: Clearly document when handoffs occur

### Handoffs

- **Transfer Context**: Pass all relevant context during handoffs
- **Prioritize Triggers**: Set appropriate priorities for competing triggers
- **Handle Rejections**: Have fallback logic if a handoff is rejected

## 10. Common Patterns & Examples

### Example 1: Bug Reporting Workflow

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│    Agno     │──────│    Form     │──────│    Email    │──────│   Ticket    │
│  Assistant  │──────│  Collector  │──────│  Verifier   │──────│   Poster    │
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
```

1. **Agno Assistant**: Initial agent that handles general queries
   - Handoff Trigger: User mentions "bug" or "report issue"
   
2. **Form Collector**: Collects bug report information
   - Capabilities: Form collection, data extraction
   - UI Instructions: show_file_upload, display_form
   - Handoff Trigger: Form complete with email address
   
3. **Email Verifier**: Verifies the user's email with Zendesk
   - Capabilities: Email verification
   - UI Instructions: request_email, show_confirmation_dialog
   - Handoff Trigger: Email verified
   
4. **Ticket Poster**: Creates the Zendesk ticket
   - Capabilities: Ticket creation
   - UI Instructions: show_progress_indicator, show_confirmation_dialog

### Example 2: Agent Implementation

```python
@register_agent(
    id="form_collector",
    name="Form Collection Agent",
    description="Collects form information for bug reports",
    version="1.0.0",
    capabilities={
        "form_collection": AgentCapability(
            type=CapabilityType.FORM_COLLECTION,
            description="Collects structured form data based on a JSON schema",
            ui_instructions=["show_file_upload", "request_email", "display_form"]
        )
    },
    handoff_triggers=[
        HandoffTrigger(
            target_agent_id="email_verifier",
            description="Form collection complete, needs email verification",
            condition_function="backend.agents.form_collector_agent.is_form_complete"
        )
    ]
)
class FormCollectorAgent(BaseAgent):
    def initialize(self, schema_path=None, **kwargs):
        # Load schema and initialize state
        self.schema = load_schema(schema_path)
        self.collected_data = {}
        
    def process_message(self, message, context):
        # Process message and update collected data
        # Example of initiating a handoff:
        if self.is_form_complete():
            return {
                "message": "Thanks for providing all the information!",
                "data": self.collected_data,
                "handoff_to": "email_verifier",
                "handoff_reason": "Form collection complete"
            }
            
        # Example of using a UI instruction:
        return {
            "message": "Please upload any relevant screenshots.",
            "ui_instruction": "show_file_upload",
            "ui_instruction_params": {
                "max_files": 3,
                "max_size_mb": 10,
                "accepted_types": ["image/png", "image/jpeg"],
                "upload_url": "/api/upload"
            }
        }
```

## Conclusion

The Agent Registry provides a powerful framework for building extensible multi-agent systems. By standardizing agent registration, capabilities, and handoffs, it enables a modular architecture where agents can be developed and configured independently while working together seamlessly.

For more details on specific implementations, refer to the API reference or examine the code in the `backend/agent_registry.py` and `backend/agent_handoff.py` files.