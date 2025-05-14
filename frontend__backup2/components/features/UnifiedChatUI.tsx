"use client";
/**
 * UnifiedChatUI Component
 * 
 * This component provides a consolidated chat interface that integrates with both:
 * - The Agent Registry for agent management and handoffs
 * - The UI Instruction Protocol for dynamic UI updates
 * 
 * It supports different agent types (currently "bug_report" and "agno") and handles:
 * - Message display and history
 * - File uploads with S3/R2 integration
 * - Dynamic UI updates via protocol
 * - Session persistence across page reloads
 * - Error handling and retry logic
 * 
 * The implementation follows the architecture documented in:
 * /docs/UNIFIED_CHAT_INTERFACE.md
 */
import React, { useState, useRef, useEffect, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { UIInstructionsContainer } from "@/protocol/uiInstructionRegistry";
import { queueUIInstruction, registerInstructionResponseHandler } from "@/protocol/uiInstructionRegistry";
import type { UIInstructionType } from "@/protocol/uiInstruction";

interface Message {
  sender: "user" | "agent";
  text: string;
  agent_type?: string; // Track which agent type sent this message
}

/**
 * Props for the UnifiedChatUI component
 * 
 * @property {string} agentType - The type of agent to communicate with:
 *   - "bug_report": For bug report submission and form collection
 *   - "agno": For general Agno agent interactions
 * 
 * @property {string} initialGreeting - Optional custom initial message from the agent
 * 
 * @property {string} apiEndpoint - Optional override for the API endpoint 
 *   (by default, endpoints are selected based on agentType)
 * 
 * @property {string} sessionId - Optional custom session identifier for conversation persistence
 *   (default: "unified-chat-session")
 */
interface UnifiedChatUIProps {
  agentType?: "bug_report" | "agno";
  initialGreeting?: string;
  apiEndpoint?: string;
  sessionId?: string;
}

/**
 * Unified Chat Interface Component
 * 
 * This component serves as the primary chat interface for the application,
 * combining features from legacy components into a single, configurable interface.
 * It dynamically adapts based on the agent type and supports file uploads,
 * UI instruction protocol, and session persistence.
 * 
 * @param {UnifiedChatUIProps} props - Component properties
 * @returns {React.ReactElement} The rendered chat interface
 */
const UnifiedChatUI: React.FC<UnifiedChatUIProps> = ({
  agentType = "bug_report",
  initialGreeting,
  apiEndpoint,
  sessionId = "unified-chat-session",
}) => {
  // Initialize default API endpoints based on agent type
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND || "http://localhost:8001";
  // Make sure we're specifically targeting the agno-agent endpoint, not form-collector
  const agnoBackendUrl = process.env.NEXT_PUBLIC_AGNO_BACKEND || "http://localhost:8001/api/agno-agent/chat";
  
  // Check for URL parameters that modify behavior
  const [debugMode, setDebugMode] = useState<boolean>(false);
  
  // Effect to check URL parameters on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Check for debug mode in URL params
      const urlParams = new URLSearchParams(window.location.search);
      const debugParam = urlParams.get('ui_debug') === 'true';
      
      // Update debug mode state
      setDebugMode(debugParam);
      
      // Store in localStorage if enabled via URL
      if (debugParam) {
        localStorage.setItem('ui_debug', 'true');
      }
      
      console.log(`[UnifiedChatUI] Debug mode: ${debugParam ? 'enabled' : 'disabled'}`);
    }
  }, []);
  
  // Use provided API endpoint or fallback to the appropriate one based on agent type
  const activeApiEndpoint = apiEndpoint || 
    (agentType === "agno" 
      ? `${backendUrl}/api/agno-agent/chat` // Make sure we hit the right endpoint
      : `${backendUrl}/api/form-collector/chat`);
      
  console.log(`Configured API endpoint for agent type "${agentType}": ${activeApiEndpoint}`);
    
  // Configure timeout and retry settings based on agent type
  const apiTimeout = agentType === "agno" ? 15000 : 10000; // 15s for Agno, 10s for others
  const maxRetries = 3;

  // Set default greeting based on agent type
  const defaultGreeting = agentType === "agno"
    ? "Hi! I'm the Agno Agent. How can I help you today?"
    : "Hi! I can help you submit a bug report. What is your email address?";

  // Define a sessionStorageKey based on agentType and sessionId for persistence
  const sessionStorageKey = `unified-chat-${agentType}-${sessionId}`;
  
  // Load persisted state if available
  const loadPersistedState = () => {
    if (typeof window === 'undefined') return null;
    
    try {
      const saved = localStorage.getItem(sessionStorageKey);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (err) {
      console.error("Error loading persisted state:", err);
    }
    return null;
  };
  
  // Get initial state from session storage or use defaults
  const persistedState = loadPersistedState();
  
  const [messages, setMessages] = useState<Message[]>(
    persistedState?.messages || [
      {
        sender: "agent",
        text: initialGreeting || defaultGreeting,
      },
    ]
  );
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [awaitingAttachments, setAwaitingAttachments] = useState(persistedState?.awaitingAttachments || false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadStatus, setUploadStatus] = useState<string[]>([]);
  const [permanentKeys, setPermanentKeys] = useState<string[]>(persistedState?.permanentKeys || []);
  const [allFilesReady, setAllFilesReady] = useState(persistedState?.allFilesReady || false);
  const [reportSubmitted, setReportSubmitted] = useState(persistedState?.reportSubmitted || false);
  const pollingRefs = useRef<{ [key: string]: NodeJS.Timeout }>({});
  const listRef = useRef<HTMLDivElement>(null);
  
  // Save state to session storage when key values change
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

  // Broader: looks for any combination of "upload/attach/file/attachment"
  const isAttachmentPrompt = (msg: string) =>
    /(upload|attach).*?(file|attachment|document)/i.test(msg);

  // Register response handlers for UI instructions
  useEffect(() => {
    // Handler for file uploads - modified to work with direct file handling
    const unsubscribeFileUpload = registerInstructionResponseHandler(
      'show_file_upload' as UIInstructionType,
      (response) => {
        console.log("File upload response (deprecated):", response);
        // Don't modify permanentKeys here as it would conflict with direct file handling
        // We'll let the pollForPermanent function handle this instead
      }
    );
    
    // Handler for email requests
    const unsubscribeEmail = registerInstructionResponseHandler(
      'request_email' as UIInstructionType,
      (response) => {
        console.log("Email response:", response);
        if (response.value) {
          setMessages((msgs) => [
            ...msgs,
            {
              sender: "user",
              text: response.value,
            },
          ]);
          // Trigger backend with the email value
          handleEmailSubmission(response.value);
        }
      }
    );
    
    // Handler for form submissions
    const unsubscribeForm = registerInstructionResponseHandler(
      'display_form' as UIInstructionType,
      (response) => {
        console.log("Form submission response:", response);
        if (response.formData) {
          // Add form data as a message
          const formSummary = Object.entries(response.formData)
            .map(([key, value]) => `${key}: ${value}`)
            .join('\n');
            
          setMessages((msgs) => [
            ...msgs,
            {
              sender: "user",
              text: `Form submitted:\n${formSummary}`,
            },
          ]);
          
          // Submit form data to backend
          setLoading(true);
          
          fetch(activeApiEndpoint, {
            method: "POST",
            headers: { 
              "Content-Type": "application/json",
              "X-Agent-Type": agentType,
              "X-Form-Submission": "true"
            },
            body: JSON.stringify({
              session_id: sessionId,
              user_message: "Form submission",
              meta: { 
                form_data: response.formData,
                agent_type: agentType
              },
            }),
          })
          .then(res => res.json())
          .then(data => {
            setMessages((msgs) => [
              ...msgs,
              { sender: "agent", text: data.assistant_message },
            ]);
          })
          .catch(err => {
            console.error("Form submission error:", err);
            setMessages((msgs) => [
              ...msgs,
              { sender: "agent", text: "Sorry, there was a problem processing your form submission." },
            ]);
          })
          .finally(() => {
            setLoading(false);
          });
        }
      }
    );
    
    // Handler for authentication prompts
    const unsubscribeAuth = registerInstructionResponseHandler(
      'show_auth_prompt' as UIInstructionType,
      (response) => {
        console.log("Auth response:", response);
        if (response.value) {
          // Handle auth values securely - don't add to visible messages
          console.log("Auth value received");
          
          // Just notify the agent that authentication was provided
          setMessages((msgs) => [
            ...msgs,
            {
              sender: "user",
              text: "Authentication provided",
            },
          ]);
          
          // Submit to backend
          setLoading(true);
          
          fetch(activeApiEndpoint, {
            method: "POST",
            headers: { 
              "Content-Type": "application/json",
              "X-Agent-Type": agentType,
              "X-Auth-Submission": "true"
            },
            body: JSON.stringify({
              session_id: sessionId,
              user_message: "Authentication provided",
              meta: { 
                auth_value: response.value,
                auth_field: response.field,
                agent_type: agentType
              },
            }),
          })
          .then(res => res.json())
          .then(data => {
            setMessages((msgs) => [
              ...msgs,
              { sender: "agent", text: data.assistant_message },
            ]);
          })
          .catch(err => {
            console.error("Auth submission error:", err);
            setMessages((msgs) => [
              ...msgs,
              { sender: "agent", text: "Sorry, there was a problem processing your authentication." },
            ]);
          })
          .finally(() => {
            setLoading(false);
          });
        }
      }
    );
    
    // Handler for selection menus
    const unsubscribeSelection = registerInstructionResponseHandler(
      'show_selection_menu' as UIInstructionType,
      (response) => {
        console.log("Selection response:", response);
        if (response.value) {
          // Handle both single and multi-select
          const valueText = Array.isArray(response.value)
            ? response.value.join(', ')
            : response.value;
            
          setMessages((msgs) => [
            ...msgs,
            {
              sender: "user",
              text: `Selected: ${valueText}`,
            },
          ]);
          
          // Submit to backend
          setLoading(true);
          
          fetch(activeApiEndpoint, {
            method: "POST",
            headers: { 
              "Content-Type": "application/json",
              "X-Agent-Type": agentType
            },
            body: JSON.stringify({
              session_id: sessionId,
              user_message: `Selected: ${valueText}`,
              meta: { 
                selection_value: response.value,
                selection_field: response.field,
                agent_type: agentType
              },
            }),
          })
          .then(res => res.json())
          .then(data => {
            setMessages((msgs) => [
              ...msgs,
              { sender: "agent", text: data.assistant_message },
            ]);
          })
          .catch(err => {
            console.error("Selection submission error:", err);
            setMessages((msgs) => [
              ...msgs,
              { sender: "agent", text: "Sorry, there was a problem processing your selection." },
            ]);
          })
          .finally(() => {
            setLoading(false);
          });
        }
      }
    );
    
    // Handler for confirmation dialogs
    const unsubscribeConfirmation = registerInstructionResponseHandler(
      'show_confirmation_dialog' as UIInstructionType,
      (response) => {
        console.log("Confirmation response:", response);
        
        // Only add message for explicit confirmations/cancellations
        // Skip intermediate confirmation dialogs like success notifications
        if (response.field === "confirmation" && response.value !== undefined) {
          setMessages((msgs) => [
            ...msgs,
            {
              sender: "user",
              text: response.value ? "Confirmed" : "Cancelled",
            },
          ]);
          
          // If confirmation was for an important action, handle it
          if (response.field === "confirmation" && response.action) {
            if (response.value && response.action === "retry_submission") {
              // Retry submission
              submitReport();
            }
          }
        }
      }
    );
    
    return () => {
      // Clean up all handlers
      unsubscribeFileUpload();
      unsubscribeEmail();
      unsubscribeForm();
      unsubscribeAuth();
      unsubscribeSelection();
      unsubscribeConfirmation();
    };
  }, [activeApiEndpoint, agentType, sessionId]);

  const handleEmailSubmission = async (email: string) => {
    setLoading(true);
    try {
      const requestOptions = {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "X-Agent-Type": agentType
        },
        body: JSON.stringify({
          session_id: sessionId,
          user_message: email,
          agent_type: agentType
        }),
      };
      
      // Use retry logic for email submission
      const res = await fetchWithRetry(activeApiEndpoint, requestOptions);
      
      if (!res.ok) throw new Error(`Email submission error: ${res.status}`);
      const data = await res.json();
      
      // Log response for debugging
      console.log(`[${agentType}] Email submission response:`, data);
      
      setMessages((msgs) => [
        ...msgs,
        { sender: "agent", text: data.assistant_message },
      ]);
      
      // Check if response is asking for attachments
      if (isAttachmentPrompt(data.assistant_message)) {
        // Set awaiting attachments flag directly
        setAwaitingAttachments(true);
        // Reset file states when a new attachment prompt is received
        setSelectedFiles([]);
        setUploadStatus([]);
        setPermanentKeys([]);
        setAllFilesReady(false);
      }
    } catch (err: any) {
      console.error("Email Submission Error:", err);
      setMessages((msgs) => [
        ...msgs,
        { 
          sender: "agent", 
          text: err.message?.includes("AbortError")
            ? "Sorry, the email submission timed out. Please try again."
            : "Sorry, something went wrong with your email submission. Please try again."
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const pollForPermanent = async (tempKey: string, idx: number) => {
    setUploadStatus((prev) => {
      const next = [...prev];
      next[idx] = "Scanning...";
      return next;
    });
    let retries = 60; // 2 minutes
    const permKey = tempKey.replace("temp/", "permanent/");
    const check = async () => {
      // First check temp/
      const resTemp = await fetch(
        `${backendUrl}/check-file-status?key=${encodeURIComponent(tempKey)}`,
        { method: "HEAD" },
      );
      if (resTemp.status === 200) {
        setUploadStatus((prev) => {
          const next = [...prev];
          next[idx] = "Uploaded, scanning...";
          return next;
        });
        return;
      }
      // If not in temp/, check permanent/
      const resPerm = await fetch(
        `${backendUrl}/check-file-status?key=${encodeURIComponent(permKey)}`,
        { method: "HEAD" },
      );
      if (resPerm.status === 200) {
        setUploadStatus((prev) => {
          const next = [...prev];
          next[idx] = "Clean (ready)";
          return next;
        });
        setPermanentKeys((prev) => {
          const newKeys = [...prev];
          if (!newKeys.includes(permKey)) {
            newKeys.push(permKey);
          }
          return newKeys;
        });
        if (pollingRefs.current[tempKey]) {
          clearInterval(pollingRefs.current[tempKey]);
          delete pollingRefs.current[tempKey]; // Remove the reference
        }
        return;
      }
      // Only after retries, mark as infected
      if (retries-- <= 0) {
        setUploadStatus((prev) => {
          const next = [...prev];
          next[idx] = "I-N-F-E-C-T-E-D (deleted)";
          return next;
        });
        if (pollingRefs.current[tempKey]) {
          clearInterval(pollingRefs.current[tempKey]);
          delete pollingRefs.current[tempKey]; // Remove the reference
        }
      }
    };
    pollingRefs.current[tempKey] = setInterval(check, 2000);
    check();
  };

  // Check if all uploaded files are marked as "Clean (ready)"
  useEffect(() => {
    if (
      selectedFiles.length > 0 &&
      uploadStatus.every((s) => s === "Clean (ready)") &&
      !allFilesReady
    ) {
      setAllFilesReady(true);
      // Add a message when all files are ready
      setMessages((msgs) => [
        ...msgs,
        {
          sender: "agent",
          text: "Your files have uploaded. Would you like to add anything else? If not, click Submit to finalize your report.",
        },
      ]);
    } else if (
      selectedFiles.length === 0 ||
      !uploadStatus.every((s) => s === "Clean (ready)")
    ) {
      setAllFilesReady(false);
    }
  }, [uploadStatus, selectedFiles.length, allFilesReady]);

  /**
   * Handles file uploads with S3/R2 integration
   * 
   * This unified handler processes file uploads from both the dropzone and file input:
   * 1. Updates UI to show upload status
   * 2. Gets presigned URLs for each file
   * 3. Uploads files to S3/R2 storage
   * 4. Polls for virus scanning status
   * 5. Manages permanent keys for successful uploads
   * 
   * @param {File[]} files - Array of files to upload
   */
  const handleFiles = async (files: File[]) => {
    setSelectedFiles((prevFiles) => [...prevFiles, ...files]);
    setUploadStatus((prev) => [...prev, ...files.map(() => "Uploading…")]);
    const startIdx = uploadStatus.length;

    for (let i = 0; i < files.length; ++i) {
      const file = files[i];
      const idx = startIdx + i;
      const safeName = file.name.replace(/\s+/g, "_");
      const meta = { name: safeName, type: file.type, size: file.size };
      console.log(
        "[DEBUG] Requesting presigned URL:",
        meta,
        "to",
        `${backendUrl}/generate-presigned-url`,
      );
      const res = await fetch(`${backendUrl}/generate-presigned-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(meta),
      });
      console.log("[DEBUG] Presign response status:", res.status);
      if (!res.ok) {
        const txt = await res.text();
        console.log("[DEBUG] Presign error response:", txt);
        setUploadStatus((prev) => {
          const next = [...prev];
          next[idx] = `Presign error ${res.status}: ${txt || res.statusText}`;
          return next;
        });
        continue;
      }
      const { url, key } = await res.json();
      console.log("[DEBUG] Got presigned URL:", url, "S3 key:", key);
      const uploadRes = await fetch(url, {
        method: "PUT",
        body: file,
        headers: { "Content-Type": file.type },
      });
      console.log("[DEBUG] S3 upload response status:", uploadRes.status);
      if (!uploadRes.ok) {
        setUploadStatus((prev) => {
          const next = [...prev];
          next[idx] = "Failed to upload to S3";
          return next;
        });
        continue;
      }
      setUploadStatus((prev) => {
        const next = [...prev];
        next[idx] = "Uploaded, scanning…";
        return next;
      });
      pollForPermanent(key, idx);
    }
  };

  const onDrop = useCallback(
    (accepted: File[]) => {
      if (!accepted.length) return;
      // Only accept new files if the total count will be 3 or fewer
      const availableSlots = 3 - selectedFiles.length;
      if (availableSlots <= 0) {
        alert(
          "Maximum 3 files allowed. Please remove some files before adding more.",
        );
        return;
      }

      const filesToAdd = accepted.slice(0, availableSlots);
      handleFiles(filesToAdd);
    },
    [selectedFiles.length],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    maxFiles: 3,
  });

  /* Handle file‑picker fallback */
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const availableSlots = 3 - selectedFiles.length;
    if (availableSlots <= 0) {
      alert(
        "Maximum 3 files allowed. Please remove some files before adding more.",
      );
      return;
    }

    handleFiles(files.slice(0, availableSlots));
  };

  const removeFile = (idx: number) => {
    setSelectedFiles((prev) => {
      const next = [...prev];
      next.splice(idx, 1);
      return next;
    });
    setUploadStatus((prev) => {
      const next = [...prev];
      next.splice(idx, 1);
      return next;
    });
    setPermanentKeys((prev) => {
      // Remove corresponding permanent key if it exists
      if (idx < prev.length) {
        const next = [...prev];
        next.splice(idx, 1);
        return next;
      }
      return prev;
    });
  };

  /**
   * Submits the completed report with attachments
   * 
   * This function:
   * 1. Sends a submit action to the backend with all attachments
   * 2. Processes the agent's response
   * 3. Shows confirmation UI via the UI Instruction Protocol
   * 4. Handles error cases with appropriate UI feedback
   * 5. Resets upload state on successful submission
   */
  const submitReport = async () => {
    setLoading(true);
    try {
      const requestOptions = {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "X-Agent-Type": agentType,
          "X-Submit-Action": "true" // Additional header to indicate submit action
        },
        body: JSON.stringify({
          session_id: sessionId,
          user_message: "Submit my report now",
          meta: { 
            attachments: permanentKeys, 
            submit: true,
            agent_type: agentType
          },
        }),
      };
      
      // Use retry logic for report submission
      const res = await fetchWithRetry(activeApiEndpoint, requestOptions);
      
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Submit error (${res.status}): ${errorText || res.statusText}`);
      }
      
      const data = await res.json();
      
      // Log submission for debugging
      console.log(`[${agentType}] Report submission response:`, data);
      
      setMessages((m) => [
        ...m,
        { sender: "agent", text: data.assistant_message },
      ]);
      
      // Clear the upload state after successful submission
      setReportSubmitted(true);
      setAwaitingAttachments(false);
      setSelectedFiles([]);
      setUploadStatus([]);
      setPermanentKeys([]);
      setAllFilesReady(false);
      
      // Create UI instruction for successful submission acknowledgement
      queueUIInstruction({
        instruction_type: "show_confirmation_dialog",
        parameters: {
          title: "Report Submitted",
          message: "Your report has been successfully submitted. Thank you for your feedback!",
          confirm_label: "Continue"
        },
        metadata: {
          priority: "high",
          version: "1.0.0",
          agent_id: agentType === "agno" ? "agno_agent" : "form_collector"
        }
      });
    } catch (err: any) {
      console.error("Report Submission Error:", err);
      
      setMessages((m) => [
        ...m,
        {
          sender: "agent",
          text: err.message?.includes("AbortError")
            ? "Sorry, the submission request timed out. Please try again."
            : "Sorry, there was a problem submitting your report. Please try again.",
        },
      ]);
      
      // Show error dialog via UI instruction protocol
      queueUIInstruction({
        instruction_type: "show_confirmation_dialog",
        parameters: {
          title: "Submission Failed",
          message: "There was a problem submitting your report. Would you like to try again?",
          confirm_label: "Try Again",
          cancel_label: "Cancel"
        },
        metadata: {
          priority: "high",
          version: "1.0.0",
          agent_id: agentType === "agno" ? "agno_agent" : "form_collector"
        }
      });
    } finally {
      setLoading(false);
    }
  };

  const skipAttachments = async () => {
    setLoading(true);
    try {
      // For bug reports, we send a "skip attachments" signal to the backend
      if (agentType === "bug_report") {
        const requestOptions = {
          method: "POST",
          headers: { 
            "Content-Type": "application/json",
            "X-Agent-Type": agentType,
            "X-Action": "skip_attachments"
          },
          body: JSON.stringify({
            session_id: sessionId,
            user_message: "I don't want to upload any files",
            meta: { 
              skip_attachments: true,
              agent_type: agentType
            },
          }),
        };
        
        try {
          // Attempt to communicate with backend about skipping attachments
          const res = await fetchWithRetry(activeApiEndpoint, requestOptions);
          
          if (res.ok) {
            const data = await res.json();
            setMessages((m) => [
              ...m,
              { sender: "agent", text: data.assistant_message || "Would you like to add anything else? If not, click Submit to finalize your report." },
            ]);
          } else {
            // If API fails, fall back to the local approach
            throw new Error("API error for skip attachments");
          }
        } catch (apiError) {
          // Fall back to client-side simulation if API call fails
          console.log("Falling back to client-side skip handling:", apiError);
          setMessages((m) => [
            ...m,
            {
              sender: "agent",
              text: "Would you like to add anything else? If not, click Submit to finalize your report.",
            },
          ]);
        }
      } else {
        // For other agent types, just add a message
        setMessages((m) => [
          ...m,
          {
            sender: "agent",
            text: "No problem. Is there anything else I can help you with?",
          },
        ]);
      }

      // Hide the attachments UI
      setAwaitingAttachments(false);
      setSelectedFiles([]);
      setUploadStatus([]);

      // Add a fake permanentKey to ensure the Submit button shows for bug reports
      if (agentType === "bug_report") {
        setPermanentKeys(["skipped-attachments"]);
      }
    } catch (err: any) {
      console.error("Skip Attachments Error:", err);
      setMessages((m) => [
        ...m,
        {
          sender: "agent",
          text: "Sorry, there was a problem. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Makes API requests with built-in exponential backoff retry logic
   * 
   * This function handles network failures, timeouts, and server errors (5xx)
   * by automatically retrying the request with increasing delays between attempts.
   * 
   * @param {string} url - The API endpoint URL
   * @param {RequestInit} options - Fetch request options
   * @param {number} retries - Number of retry attempts remaining (defaults to maxRetries)
   * @param {number} backoff - Base delay in milliseconds for exponential backoff
   * @returns {Promise<Response>} The fetch response
   */
  const fetchWithRetry = async (url: string, options: RequestInit, retries = maxRetries, backoff = 300) => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), apiTimeout);
      
      const fetchOptions = {
        ...options,
        signal: controller.signal
      };
      
      const response = await fetch(url, fetchOptions);
      clearTimeout(timeoutId);
      
      // If response is 429 (too many requests) or 5xx (server errors), retry
      if ((response.status === 429 || response.status >= 500) && retries > 0) {
        // Wait with exponential backoff
        const delay = backoff * Math.pow(2, maxRetries - retries);
        await new Promise(resolve => setTimeout(resolve, delay));
        return fetchWithRetry(url, options, retries - 1, backoff);
      }
      
      return response;
    } catch (error: any) {
      // If error is due to timeout or network issues and we have retries left
      if ((error.name === "AbortError" || error.name === "TypeError") && retries > 0) {
        const delay = backoff * Math.pow(2, maxRetries - retries);
        await new Promise(resolve => setTimeout(resolve, delay));
        return fetchWithRetry(url, options, retries - 1, backoff);
      }
      throw error;
    }
  };

  /**
   * Handles sending user messages to the appropriate backend agent
   * 
   * This function:
   * 1. Adds the user message to the UI
   * 2. Sends the message to the appropriate backend agent
   * 3. Processes the agent response
   * 4. Handles UI Instruction Protocol messages (like file upload requests)
   * 5. Implements error handling and retry logic
   * 
   * @param {React.FormEvent} e - The form submission event
   */
  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && !awaitingAttachments) return;
    const userMsg = { sender: "user", text: input };
    setMessages((msgs) => [...msgs, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const meta =
        permanentKeys.length > 0 ? { attachments: permanentKeys } : undefined;
        
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
          agent_type: agentType // Include in body for older APIs that don't check headers
        }),
      };
      
      // Log the request for debugging
      console.log(`Sending request to ${activeApiEndpoint} with agent type: ${agentType}`);
      console.log(`Request body:`, JSON.parse(requestOptions.body));
      
      // Use retry logic for API requests
      const res = await fetchWithRetry(activeApiEndpoint, requestOptions);
      
      if (!res.ok) throw new Error(`Agent error: ${res.status}`);
      const data = await res.json();
      
      // Enhanced logging for debugging
      console.log(`[${agentType}] Response received:`, {
        endpoint: activeApiEndpoint,
        status: res.status,
        headers: Object.fromEntries(res.headers.entries()),
        data
      });
      
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

      // Check if the new message is an attachment prompt
      const isNewAttachmentPrompt = isAttachmentPrompt(data.assistant_message);

      // Set awaiting attachments flag directly like in ChatUI
      if (isNewAttachmentPrompt) {
        setAwaitingAttachments(true);
        // Reset file states when a new attachment prompt is received
        setSelectedFiles([]);
        setUploadStatus([]);
        setPermanentKeys([]);
        setAllFilesReady(false);
      }
    } catch (err: any) {
      console.error("API Error:", err);
      setMessages((msgs) => [
        ...msgs,
        { 
          sender: "agent", 
          text: err.message?.includes("AbortError") 
            ? "Sorry, the request timed out. Please try again."
            : "Sorry, something went wrong. Please try again." 
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    if (!reportSubmitted) {
      const lastAgentMsg =
        messages.length > 0 ? messages[messages.length - 1].text : "";
      
      // Only auto-queue email request for bug_report agent type, not for regular agno chat
      if (messages.length === 1 && messages[0].sender === "agent" && 
          /email|e-mail|email address/i.test(messages[0].text) && 
          agentType === "bug_report") {  // Only for bug_report agent
        queueUIInstruction({
          instruction_type: "request_email",
          parameters: {
            prompt: "Please enter your email address:",
            validation_regex: "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"
          },
          metadata: {
            priority: "normal",
            version: "1.0.0",
            agent_id: "form_collector"
          }
        });
      }

      // Debug log for troubleshooting
      console.log(
        "Last agent message:",
        lastAgentMsg,
        "Attachment prompt:",
        isAttachmentPrompt(lastAgentMsg),
      );

      // If it's an attachment prompt, set awaiting attachments
      if (isAttachmentPrompt(lastAgentMsg)) {
        setAwaitingAttachments(true);
      }
    }
  }, [messages, reportSubmitted, agentType]);

  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, loading]);
  
  // Cleanup all intervals when component unmounts
  useEffect(() => {
    return () => {
      // Clear all polling intervals
      Object.keys(pollingRefs.current).forEach((key) => {
        clearInterval(pollingRefs.current[key]);
      });
    };
  }, []);

  // Show uploads section if user has added files or we're awaiting attachments
  const showUploadsSection = !reportSubmitted && awaitingAttachments; // Only show when explicitly awaiting attachments

  // Show submit button if there are files ready or skip was used
  const showSubmitButton =
    !reportSubmitted && (permanentKeys.length > 0 || !awaitingAttachments);

  return (
    <div className="fixed inset-0 flex flex-col bg-[#0b1021] text-white scrollbar-custom">
      {/* Message list */}
      <div
        ref={listRef}
        className="flex-1 overflow-y-auto p-4 flex flex-col gap-3 scrollbar-custom"
      >
        {messages.map((msg, i) => (
          <div
            key={i}
            className={
              msg.sender === "user" ? "flex justify-end" : "flex justify-start"
            }
          >
            <div
              className={
                msg.sender === "user"
                  ? "bg-gradient-to-r from-[#6d4aff] to-[#8c5eff] rounded-2xl px-4 py-3 max-w-[80%] shadow-md"
                  : "bg-[#121833] rounded-2xl px-4 py-3 max-w-[80%] shadow-md"
              }
            >
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-[#121833] rounded-2xl px-4 py-3 text-gray-400">
              Typing...
            </div>
          </div>
        )}
      </div>
      
      {/* UI Instructions Container - This will render active instructions */}
      <UIInstructionsContainer />

      {/* File upload section - shown ONLY when awaiting attachments */}
      {showUploadsSection && (
        <div className="border-t border-[#1e2642] p-4">
          <label className="block font-semibold mb-2 text-white">
            Upload attachments (up to 3 files, 100&nbsp;MB each):
          </label>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition ${
              isDragActive
                ? "border-[#6d4aff] bg-[#121833]"
                : "border-[#1e2642]"
            }`}
          >
            <input {...getInputProps()} />
            {isDragActive ? (
              <p>Drop the files here…</p>
            ) : (
              <p>
                Drag &amp; drop files here, or click to select&nbsp;files{" "}
                {selectedFiles.length > 0
                  ? `(${3 - selectedFiles.length} slots remaining)`
                  : ""}
              </p>
            )}
          </div>
          <input
            type="file"
            multiple
            className="hidden"
            onChange={handleFileChange}
          />
          <ul className="mt-2">
            {selectedFiles.map((file, i) => (
              <li
                key={i}
                className="flex items-center justify-between my-1 text-white"
              >
                <span className="flex-grow">
                  {file.name} — {uploadStatus[i]}
                  {uploadStatus[i]?.startsWith("I-N-F-E-C-T-E-D") && (
                    <button
                      className="ml-2 underline text-[#8c5eff]"
                      onClick={() => handleFiles([file])}
                    >
                      Retry
                    </button>
                  )}
                  {uploadStatus[i]?.startsWith("Clean") && <span> ✔️</span>}
                </span>
                <button
                  className="text-red-400 ml-2 px-2"
                  onClick={() => removeFile(i)}
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
          <div className="mt-4 flex justify-end">
            {selectedFiles.length === 0 && (
              <button
                className="bg-[#242d4f] hover:bg-[#343e60] text-white rounded-full px-5 py-2 mr-auto transition-colors"
                disabled={loading}
                onClick={skipAttachments}
              >
                Skip
              </button>
            )}
          </div>
        </div>
      )}

      {/* Message input - now centered with max width */}
      <div className="border-t border-[#1e2642] p-4 flex justify-center">
        <form
          onSubmit={sendMessage}
          className="flex gap-2 items-center w-full max-w-3xl"
        >
          <input
            className="flex-1 rounded-full bg-[#121833] border border-[#1e2642] text-white p-3 focus:outline-none focus:ring-2 focus:ring-[#6d4aff] placeholder-gray-400"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message…"
            disabled={loading}
          />
          <button
            type="submit"
            className="bg-[#6d4aff] hover:bg-[#5d3aef] transition-colors text-white rounded-full px-5 py-2 font-medium disabled:opacity-50"
            disabled={loading || !input.trim()}
          >
            Send
          </button>

          {/* Submit button - ALWAYS here when it should be visible */}
          {showSubmitButton && (
            <button
              className="bg-gradient-to-r from-[#124a2c] to-[#1a6e40] hover:opacity-90 transition-opacity text-white rounded-full px-5 py-2 font-bold disabled:opacity-50"
              disabled={loading}
              onClick={submitReport}
            >
              Submit Report
            </button>
          )}
        </form>
      </div>
    </div>
  );
};

// Add global styles for custom scrollbars
const scrollbarStyles = `
  .scrollbar-custom::-webkit-scrollbar {
    width: 10px;
  }

  .scrollbar-custom::-webkit-scrollbar-track {
    background: #0b1021;
  }

  .scrollbar-custom::-webkit-scrollbar-thumb {
    background: linear-gradient(to bottom, #6d4aff, #8c5eff);
    border-radius: 5px;
  }

  .scrollbar-custom::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(to bottom, #5d3aef, #7c4eef);
  }
`;

// Insert the styles into the document head
if (typeof document !== "undefined") {
  const style = document.createElement("style");
  style.type = "text/css";
  style.appendChild(document.createTextNode(scrollbarStyles));
  document.head.appendChild(style);
}

export default UnifiedChatUI;