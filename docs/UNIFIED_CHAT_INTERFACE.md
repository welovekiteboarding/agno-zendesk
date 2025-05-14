# Unified Chat Interface Architecture

This document describes the architecture and implementation details of the unified chat interface in the Agno Zendesk integration project.

## Background

Previously, the project had multiple separate chat interface implementations:

1. **ChatUI.tsx** - Basic chat interface with file upload functionality for bug reports
2. **AgnoChatUI.tsx** - Simple chat interface for Agno agent interactions
3. **ChatUIWithRegistry.tsx** - Enhanced chat interface with UI Instruction Protocol support

This fragmentation led to code duplication, inconsistent user experiences, and maintenance challenges.

## Unified Architecture

The new architecture consolidates these implementations into a single, configurable component: `UnifiedChatUI.tsx`, located at `/frontend__backup2/components/features/UnifiedChatUI.tsx`.

### Key Features

- **Agent Type Configuration** - Can be configured for different agent types (bug_report, agno)
- **UI Instruction Protocol Integration** - Supports dynamic UI updates via the UI Instruction Protocol
- **File Upload Support** - Integrated S3/R2 file upload with virus scanning feedback
- **Consistent Styling** - Unified visual design across all chat experiences
- **Progressive Enhancement** - Core chat functionality works even without advanced features
- **Accessibility Support** - Meets WCAG accessibility standards
- **Agent Handoff Management** - Seamless transition between different agent types
- **Error Recovery** - Robust error handling with retry logic

## Component Structure

### Props Interface

```typescript
interface UnifiedChatUIProps {
  agentType?: "bug_report" | "agno"; // Determines which agent to communicate with
  initialGreeting?: string; // Custom initial message
  apiEndpoint?: string; // Override default API endpoint
  sessionId?: string; // Custom session identifier
}
```

### Internal State Management

The component uses React's useState and useRef hooks to manage several key state categories:

#### Message State
```typescript
const [messages, setMessages] = useState<Message[]>(/* ... */);
const [loading, setLoading] = useState(false);
```

#### Session State
```typescript
const sessionStorageKey = `unified-chat-${agentType}-${sessionId}`;
const [reportSubmitted, setReportSubmitted] = useState(/* ... */);
```

#### File Upload State
```typescript
const [awaitingAttachments, setAwaitingAttachments] = useState(/* ... */);
const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
const [uploadStatus, setUploadStatus] = useState<string[]>([]);
const [permanentKeys, setPermanentKeys] = useState<string[]>(/* ... */);
const [allFilesReady, setAllFilesReady] = useState(/* ... */);
const pollingRefs = useRef<{ [key: string]: NodeJS.Timeout }>({});
```

### Key Logic Components

#### 1. Message Management

The component uses a message array that tracks both user and agent messages with proper attribution:

```typescript
interface Message {
  sender: "user" | "agent";
  text: string;
  agent_type?: string; // Track which agent type sent this message
}
```

Key functions:
- `sendMessage(e: React.FormEvent)`: Handles user message submission
- `listRef` with auto-scroll behavior: Ensures new messages are visible

#### 2. File Upload System

The file upload functionality is built around these key functions:

- `handleFiles(files: File[])`: Processes file selection and initiates uploads
- `pollForPermanent(tempKey: string, idx: number)`: Monitors virus scanning status
- `onDrop` and `useDropzone()`: Provides drag-and-drop functionality
- `removeFile(idx: number)`: Handles file removal
- `submitReport()`: Submits the report with uploaded files
- `skipAttachments()`: Allows proceeding without file uploads

The component renders file uploads conditionally:
```tsx
{showUploadsSection && (
  <div className="border-t border-[#1e2642] p-4">
    {/* File upload UI */}
  </div>
)}
```

#### 3. UI Instruction Handling

The component registers handlers for various UI instruction types through the UI Instruction Protocol:

```typescript
useEffect(() => {
  // Handler for file uploads
  const unsubscribeFileUpload = registerInstructionResponseHandler(
    'show_file_upload' as UIInstructionType,
    (response) => { /* ... */ }
  );
  
  // Other handlers...
  
  return () => {
    // Clean up all handlers
    unsubscribeFileUpload();
    // ...
  };
}, [/* dependencies */]);
```

Supported instruction types include:
- `show_file_upload`: Activates file upload UI
- `request_email`: Captures email addresses
- `display_form`: Renders interactive forms
- `show_auth_prompt`: Handles authentication requests 
- `show_selection_menu`: Displays selection options
- `show_confirmation_dialog`: Shows confirmation prompts

#### 4. API Communication

The component handles API communication through the `fetchWithRetry` function, which implements:

- Request timeouts with AbortController
- Exponential backoff retry logic
- Error categorization and specific handling
- Structured request/response handling

```typescript
const fetchWithRetry = async (url: string, options: RequestInit, retries = maxRetries, backoff = 300) => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), apiTimeout);
    
    // Make request with timeout
    const response = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(timeoutId);
    
    // Handle retry logic for certain status codes
    if ((response.status === 429 || response.status >= 500) && retries > 0) {
      const delay = backoff * Math.pow(2, maxRetries - retries);
      await new Promise(resolve => setTimeout(resolve, delay));
      return fetchWithRetry(url, options, retries - 1, backoff);
    }
    
    return response;
  } catch (error: any) {
    // Retry on network errors or timeouts
    if ((error.name === "AbortError" || error.name === "TypeError") && retries > 0) {
      const delay = backoff * Math.pow(2, maxRetries - retries);
      await new Promise(resolve => setTimeout(resolve, delay));
      return fetchWithRetry(url, options, retries - 1, backoff);
    }
    throw error;
  }
};
```

## Agent Handoff Mechanism

The component handles agent handoffs seamlessly through:

1. **Backend Detection**: The backend API (e.g., `agno_agent_chat.py`) identifies handoff triggers and sends appropriate response:

```python
# From agno_agent_chat.py
if session["current_agent"] == "agno" and should_handoff_to_form_collector(req.user_message):
    # Initialize form collector
    if not session["form_collector"]:
        session["form_collector"] = initialize_form_collector(req.session_id)
    
    # Generate handoff message
    handoff_message = "..."
    
    # Get initial message from form collector
    form_collector = session["form_collector"]
    initial_prompt = form_collector.get_field_prompt('reporterName')
    
    # Combine handoff message with initial form collector prompt
    combined_message = f"{handoff_message}\n\n{initial_prompt}"
    
    # Return the combined message with handoff indicator
    return ChatResponse(
        assistant_message=combined_message,
        agent_type="agno->form_collector"  # Indicates a handoff
    )
```

2. **Frontend Detection**: The UnifiedChatUI component detects handoff signals:

```typescript
// Check if the response indicates a different agent type (handoff)
const responseAgentType = data.agent_type || agentType;
if (responseAgentType !== agentType && responseAgentType.includes("->")) {
  console.log(`Agent handoff detected: ${responseAgentType}`);
}

setMessages((msgs) => [
  ...msgs,
  { 
    sender: "agent", 
    text: data.assistant_message,
    agent_type: responseAgentType // Store the agent type that sent this message
  },
]);
```

3. **UI Adaptation**: The component automatically adapts its behavior based on the current agent type.

## API Integration Details

The component implements robust API integration with the following features:

### Endpoint Configuration

- Automatically selects the appropriate endpoint based on agent type:
```typescript
const activeApiEndpoint = apiEndpoint || 
  (agentType === "agno" 
    ? `${backendUrl}/api/agno-agent/chat`
    : `${backendUrl}/api/form-collector/chat`);
```

- Supports custom endpoint override via props
- Adds agent-specific headers and metadata to requests:
```typescript
const requestOptions = {
  method: "POST",
  headers: { 
    "Content-Type": "application/json",
    "X-Agent-Type": agentType // Help backend identify agent type
  },
  body: JSON.stringify({
    session_id: sessionId,
    user_message: input,
    meta,
    agent_type: agentType // Include in body for older APIs
  }),
};
```

### Resilient Communication

- Implements exponential backoff with configurable timeouts based on agent type:
```typescript
const apiTimeout = agentType === "agno" ? 15000 : 10000; // 15s for Agno, 10s for others
const maxRetries = 3;
```

- Error handling includes specific messaging:
```typescript
setMessages((msgs) => [
  ...msgs,
  { 
    sender: "agent", 
    text: err.message?.includes("AbortError") 
      ? "Sorry, the request timed out. Please try again."
      : "Sorry, something went wrong. Please try again." 
  },
]);
```

### Session Persistence

The component uses localStorage for persistent state across page reloads:

```typescript
useEffect(() => {
  if (typeof window === 'undefined') return;
  
  const stateToSave = {
    messages,
    awaitingAttachments,
    permanentKeys,
    allFilesReady,
    reportSubmitted,
    timestamp: Date.now()
  };
  
  try {
    localStorage.setItem(sessionStorageKey, JSON.stringify(stateToSave));
  } catch (err) {
    console.error("Error saving state to session storage:", err);
  }
}, [messages, awaitingAttachments, permanentKeys, allFilesReady, reportSubmitted, sessionStorageKey]);
```

### File Upload Integration

The file upload system integrates with S3/R2 storage through:

1. **Presigned URL Generation**: 
```typescript
const res = await fetch(`${backendUrl}/generate-presigned-url`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(meta),
});
const { url, key } = await res.json();
```

2. **Direct Upload to S3/R2**:
```typescript
const uploadRes = await fetch(url, {
  method: "PUT",
  body: file,
  headers: { "Content-Type": file.type },
});
```

3. **Virus Scan Status Polling**:
```typescript
// Check temp/
const resTemp = await fetch(
  `${backendUrl}/check-file-status?key=${encodeURIComponent(tempKey)}`,
  { method: "HEAD" },
);

// Check permanent/
const resPerm = await fetch(
  `${backendUrl}/check-file-status?key=${encodeURIComponent(permKey)}`,
  { method: "HEAD" },
);
```

## Routing Configuration

The application routing has been updated to use the unified component:

- **/* (Main Page)**: Uses UnifiedChatUI with agno agent type:
```tsx
// app/page.tsx
<UnifiedChatUI
  agentType="agno"
  initialGreeting="Hi! I'm Agno, your AI assistant."
  sessionId="agno-main-session-v2"
/>
```

- **/agno-chat**: Specialized Agno agent interface:
```tsx
// app/agno-chat/page.tsx
<UnifiedChatUI 
  agentType="agno"
  initialGreeting="Hi! I'm the Agno Agent. How can I help you today?"
  sessionId="agno-chat-session"
/>
```

- **/chat-with-registry**: Server-side redirect to the main interface with UI debug enabled:
```tsx
// app/chat-with-registry/page.tsx
export default function ChatWithRegistryPage() {
  // Redirect to main page with UI debug mode enabled
  redirect('/?ui_debug=true');
  return null;
}
```

The UI debug mode is detected via URL parameters:
```typescript
useEffect(() => {
  if (typeof window !== 'undefined') {
    // Check for debug mode in URL params
    const urlParams = new URLSearchParams(window.location.search);
    const debugParam = urlParams.get('ui_debug') === 'true';
    setDebugMode(debugParam);
  }
}, []);
```

## Static Bug Report Form

In addition to the chat interface, a standalone bug report form is also available at `/bug-report.html`. This static HTML implementation provides:

1. **Direct Form Access**: Non-conversational alternative for bug reporting
2. **Same File Upload Functionality**: Uses the same S3/R2 integration and virus scanning
3. **Identical Field Collection**: Collects the same bug report fields as the chat interface
4. **Form Validation**: Client-side validation matching the schema requirements

## Usage Examples

### Basic Usage
```tsx
<UnifiedChatUI 
  agentType="bug_report"
  initialGreeting="Hi! I can help you submit a bug report."
  sessionId="bug-report-session"
/>
```

### With Custom API Endpoint
```tsx
<UnifiedChatUI 
  agentType="agno"
  apiEndpoint="https://custom-api.example.com/chat"
  sessionId="custom-session"
/>
```

### Debug Mode
```tsx
<UnifiedChatUI 
  agentType="agno"
  initialGreeting="Debug mode enabled. This instance has additional logging."
  sessionId="debug-session"
/>
```

## Extending the Component

To add new functionality to the unified chat interface:

### 1. New UI Instruction Types

Add a new instruction type to the UI Instruction Protocol:

```typescript
// In protocol/uiInstruction.ts
export type UIInstructionType =
  | "show_file_upload"
  | "request_email"
  | "display_form"
  | "show_auth_prompt"
  | "show_selection_menu"
  | "show_confirmation_dialog"
  | "my_new_instruction_type"; // Add your new type here
```

Then register a handler in UnifiedChatUI.tsx:

```typescript
const unsubscribeNewInstruction = registerInstructionResponseHandler(
  'my_new_instruction_type' as UIInstructionType,
  (response) => {
    // Handle the new instruction type
    console.log("New instruction response:", response);
    // Update UI or state based on the instruction
  }
);
```

### 2. New Agent Types

Extend the agent type definition and add corresponding routing logic:

```typescript
// Update the UnifiedChatUIProps interface
interface UnifiedChatUIProps {
  agentType?: "bug_report" | "agno" | "my_new_agent";
  // ...other props
}

// Add endpoint selection logic
const activeApiEndpoint = apiEndpoint || 
  (agentType === "agno" 
    ? `${backendUrl}/api/agno-agent/chat`
    : agentType === "my_new_agent"
      ? `${backendUrl}/api/my-new-agent/chat`
      : `${backendUrl}/api/form-collector/chat`);
```

### 3. Custom Styling

The component uses CSS classes that can be overridden or extended:

```tsx
<div className="fixed inset-0 flex flex-col bg-[#0b1021] text-white scrollbar-custom">
  {/* Message list */}
  <div
    ref={listRef}
    className="flex-1 overflow-y-auto p-4 flex flex-col gap-3 scrollbar-custom"
  >
    {/* Messages */}
  </div>
</div>
```

### 4. Additional Features

Add new features by extending the component's state and functionality:

```typescript
// Add new state
const [myNewFeatureState, setMyNewFeatureState] = useState(initialValue);

// Add new effect
useEffect(() => {
  // Initialize my new feature
  
  return () => {
    // Clean up my new feature
  };
}, [dependencies]);

// Add new rendering
return (
  <div>
    {/* Existing UI */}
    
    {myNewFeatureState && (
      <div className="my-new-feature">
        {/* New feature UI */}
      </div>
    )}
  </div>
);
```

## Future Improvements

1. **Offline Support** 
   - Implement offline message queuing with IndexedDB
   - Add sync functionality when connection is restored
   - Provide offline indicator and queue status to users

2. **User Authentication** 
   - Integrate with authentication system for personalized experiences
   - Add user identification and history retrieval
   - Support secure session management

3. **Conversation History** 
   - Implement persistent chat history beyond page refreshes
   - Add conversation search and filtering
   - Support conversation export and sharing

4. **Multi-language Support** 
   - Add internationalization capabilities using i18n
   - Support dynamic language switching
   - Localize UI elements and agent responses

5. **Advanced Analytics** 
   - Integrate usage metrics and conversation analytics
   - Track user satisfaction and completion rates
   - Provide insights for continuous improvement

6. **Voice and Audio Support**
   - Add speech-to-text input capabilities
   - Implement text-to-speech output options
   - Support audio file attachments and transcription

## Related Documentation

- [Agent Registry Documentation](agent_registry_documentation.md)
- [UI Instruction Protocol Security](ui_instruction_protocol_security.md)
- [Multi-Agent Architecture](multi-agent-architecture.md)
- [Frontend Backend Integration Plan](FRONTEND_BACKEND_INTEGRATION_PLAN.md)