# Multi-Agent Chat System: Architecture & Workflow Vision

## 1. Background & Motivation

As the system evolves, multiple specialized agents (e.g., Agno Agent, Form Collector, Email Verifier, Zendesk Ticket Poster, etc.) will collaborate to handle complex user workflows. The goal is to provide a seamless, unified chat experience for users, while keeping the codebase modular, maintainable, and scalable.

---

## 2. Is This in the PRD/Tasks?

- **Current State:**  
  The PRD and tasks describe the existence of multiple agents and some handoff logic, but **do not provide a single, clear, end-to-end vision for multi-agent orchestration and frontend/backend integration**.
- **What’s Missing:**  
  - A unified architectural plan for agent orchestration
  - A clear frontend strategy for a universal chat UI
  - Explicit documentation of agent handoff protocols and extensibility

---

## 3. Multi-Agent Workflow: The Vision

### A. User Experience

- The user interacts with a single chat window.
- The conversation may involve multiple agents, but the transition is seamless and invisible to the user.
- The UI adapts dynamically (e.g., shows file upload, asks for email, etc.) based on the current agent’s needs.

### B. Backend Orchestration

- **Session State:**  
  The backend maintains a session object for each user, tracking:
  - Conversation history
  - Current active agent
  - Any collected data (e.g., bug report fields, email verification status)
- **Agent Registry:**  
  Each agent (Agno, Form Collector, Email Verifier, Zendesk, etc.) is registered and can be invoked by the orchestrator.
- **Orchestrator Logic:**  
  - Receives each user message
  - Decides which agent should handle the message (based on intent, workflow state, etc.)
  - Forwards the message to the appropriate agent
  - Handles agent handoff (e.g., when Agno detects a bug report intent, hands off to Form Collector)
  - Returns the agent’s response and any UI instructions to the frontend

### C. Frontend Universal Chat UI

- **Single Chat Component:**  
  One main React component (e.g., `UniversalChatUI.tsx`) handles all chat interactions.
- **Dynamic UI Rendering:**  
  The backend can send UI hints (e.g., "show file upload", "ask for email") as part of its response, and the frontend renders the appropriate controls.
- **Agent-Agnostic:**  
  The frontend does not need to know which agent is active; it simply displays messages and adapts UI based on backend instructions.

---

## 4. Agent Handoff & Integration Protocol

- **Handoff Trigger:**  
  The orchestrator detects when a handoff is needed (e.g., user says "I want to report a bug").
- **Handoff Action:**  
  The orchestrator updates the session’s active agent and forwards the next message to the new agent.
- **Frontend Notification:**  
  The backend can include an `agent_type` or `ui_instruction` field in its response to help the frontend adapt if needed.
- **Extensibility:**  
  New agents can be added by registering them with the orchestrator and defining their handoff triggers and expected UI instructions.

---

## 5. Example Workflow

1. **User:** "Hi"
2. **Orchestrator:** Routes to Agno Agent (general assistant)
3. **User:** "I want to report a bug"
4. **Orchestrator:** Detects intent, hands off to Form Collector Agent
5. **Form Collector:** Collects bug details, prompts for file upload
6. **User:** Uploads files via UI
7. **Form Collector:** Completes report, hands off to Email Verifier Agent if needed
8. **Email Verifier:** Verifies email, then hands off to Zendesk Agent
9. **Zendesk Agent:** Posts ticket, confirms to user

---

## 6. Major Tasks & How They Achieve the Vision

Below are the key tasks required for the multi-agent architecture, with an explanation of how each one contributes to the end vision.  
**Each task is hyperlinked to its full definition in the `tasks/` directory for direct review.**

---

### **Task: [Implement Agent Registry with Handoff Protocol (Task 19)](../tasks/task_019.txt)**

**Purpose:**  
Design and implement a centralized agent registry system with a standardized process for agent registration, discovery, and handoff trigger definition.

**How it achieves the vision:**  
- Enables seamless orchestration and extensibility by allowing new agents to be registered and discovered dynamically.
- Provides a single source of truth for which agents are available and how/when they should take over the conversation.
- Makes agent handoff logic explicit and maintainable, supporting complex workflows.
- See [Task 19](../tasks/task_019.txt) for full requirements and test strategy.

---

### **Task: [Define Backend-to-Frontend UI Instruction Protocol (Task 20)](../tasks/task_020.txt)**

**Purpose:**  
Design and document a standardized protocol for backend systems to send UI instructions to the frontend, enabling dynamic agent-driven interface updates in the universal chat component.

**How it achieves the vision:**  
- Allows the backend (and any agent) to control the frontend UI dynamically (e.g., show file upload, request email, display form).
- Makes the chat UI agent-agnostic: the frontend simply follows backend instructions, so new agents and UI flows can be added without frontend rewrites.
- Supports a richer, more adaptive user experience.
- See [Task 20](../tasks/task_020.txt) for full requirements and test strategy.

---

### **Task: Build a Universal, Agent-Agnostic Chat UI ([Task 21](../tasks/task_021.txt) if present)**

**Purpose:**  
Develop a single chat UI component that adapts to backend UI instructions and supports all agent handoffs.

**How it achieves the vision:**  
- Provides a unified, seamless chat experience for the user, regardless of which agent is active.
- Reduces code duplication and complexity in the frontend.
- Ensures that all agent workflows (form collection, email verification, ticket posting, etc.) are supported in one place.
- See [Task 21](../tasks/task_021.txt) (if present) or add this task if not yet created.

---

### **Task: Implement Backend Orchestrator Endpoint ([Task 22](../tasks/task_022.txt) if present)**

**Purpose:**  
Create a backend endpoint that manages session state, agent registry, and agent handoff logic for all agents.

**How it achieves the vision:**  
- Centralizes all agent orchestration logic, making it easy to manage session context and agent transitions.
- Ensures that the right agent is handling each user message, and that handoffs are smooth and stateful.
- Provides a single API for the frontend to interact with, simplifying integration.
- See [Task 22](../tasks/task_022.txt) (if present) or add this task if not yet created.

---

### **Task: Document the Multi-Agent Architecture and Handoff Protocol ([Task 17](../tasks/task_017.txt) or similar)**

**Purpose:**  
Prepare comprehensive documentation for the multi-agent architecture, agent handoff protocol, and extensibility guidelines.

**How it achieves the vision:**  
- Ensures all developers and future contributors understand how the system works and how to extend it.
- Reduces onboarding time and risk of architectural drift.
- Provides clear, actionable guidance for adding new agents, UI instructions, and orchestrator logic.
- See [Task 17](../tasks/task_017.txt) or the most recent documentation task for details.

---

### **Other Supporting Files & Modules**

| File/Module                       | Responsibility                                                      |
|------------------------------------|---------------------------------------------------------------------|
| `UniversalChatUI.tsx`              | Main frontend chat component, renders messages & dynamic controls   |
| `api/routes/orchestrator_chat.py`  | Main backend endpoint, handles session, agent registry, handoffs    |
| `agents/` (backend)                | Individual agent implementations (Agno, Form Collector, etc.)       |
| `session_manager.py` (backend)     | Session state management                                            |
| `agent_registry.py` (backend)      | Agent registration and invocation logic                             |

---

## 7. Extending the System

- **To add a new agent:**
  1. Implement the agent in the backend (`agents/your_agent.py`)
  2. Register it with the orchestrator
  3. Define handoff triggers and UI instructions
  4. (Optionally) Update frontend to handle new UI instructions if needed

---

## 8. UI Instruction Protocol (Example)

Backend responses can include:
```json
{
  "assistant_message": "Please upload your attachments now.",
  "agent_type": "form_collector",
  "ui_instruction": "show_file_upload"
}
```
Frontend renders the file upload UI when `ui_instruction` is `show_file_upload`.

---

## 9. Summary Diagram

```
User <-> UniversalChatUI.tsx <-> Orchestrator API <-> [Agno Agent, Form Collector, Email Verifier, Zendesk Agent, ...]
```
- Orchestrator manages agent switching and session state.
- UniversalChatUI adapts UI based on backend instructions.

---

## 10. Next Steps

- Refactor frontend to use a universal, agent-agnostic chat component.
- Refactor backend to centralize agent orchestration and session management.
- Document agent registration, handoff triggers, and UI instruction protocol.
- Update roadmap/tasks to reflect this unified vision.

---

# Conclusion

This document is your architectural blueprint for a scalable, maintainable, multi-agent chat system.  
Each major task described above is essential for achieving the end vision:
- The agent registry and handoff protocol make the system extensible and orchestrated.
- The backend-to-frontend UI instruction protocol enables a truly universal, adaptive chat UI.
- The universal chat UI and orchestrator endpoint provide a seamless, agent-agnostic user experience.
- Comprehensive documentation ensures the system can grow and evolve with clarity.

**You do NOT need a separate UI file for each agent.**  
**You DO need a universal chat UI and a robust backend orchestrator.**