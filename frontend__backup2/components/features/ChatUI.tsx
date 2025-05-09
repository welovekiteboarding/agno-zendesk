"use client";
import React, { useState, useRef, useEffect, useCallback } from "react";
import { useDropzone } from "react-dropzone";

interface Message {
  sender: "user" | "agent";
  text: string;
}

const backendUrl = process.env.NEXT_PUBLIC_BACKEND || "http://localhost:8001";

const ChatUI: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "agent",
      text: "Hi! I can help you submit a bug report. What is your email address?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [awaitingAttachments, setAwaitingAttachments] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadStatus, setUploadStatus] = useState<string[]>([]);
  const [permanentKeys, setPermanentKeys] = useState<string[]>([]);
  const [allFilesReady, setAllFilesReady] = useState(false);
  const [reportSubmitted, setReportSubmitted] = useState(false);
  const pollingRefs = useRef<{ [key: string]: NodeJS.Timeout }>({});
  const listRef = useRef<HTMLDivElement>(null);

  // Broader: looks for any combination of "upload/attach/file/attachment"
  const isAttachmentPrompt = (msg: string) =>
    /(upload|attach).*?(file|attachment|document)/i.test(msg);

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
        { method: "HEAD" }
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
        { method: "HEAD" }
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
        clearInterval(pollingRefs.current[tempKey]);
        return;
      }
      // Only after retries, mark as infected
      if (retries-- <= 0) {
        setUploadStatus((prev) => {
          const next = [...prev];
          next[idx] = "I-N-F-E-C-T-E-D (deleted)";
          return next;
        });
        clearInterval(pollingRefs.current[tempKey]);
      }
    };
    pollingRefs.current[tempKey] = setInterval(check, 2000);
    check();
  };

  // Check if all uploaded files are marked as "Clean (ready)"
  useEffect(() => {
    if (selectedFiles.length > 0 && uploadStatus.every(s => s === "Clean (ready)") && !allFilesReady) {
      setAllFilesReady(true);
      // Add a message when all files are ready
      setMessages(msgs => [
        ...msgs,
        { 
          sender: "agent", 
          text: "Your files have uploaded. Would you like to add anything else? If not, click Submit to finalize your report." 
        }
      ]);
    } else if (selectedFiles.length === 0 || !uploadStatus.every(s => s === "Clean (ready)")) {
      setAllFilesReady(false);
    }
  }, [uploadStatus, selectedFiles.length, allFilesReady]);

  /* Unified handler so we can reuse for <input> and Dropzone */
  const handleFiles = async (files: File[]) => {
    setSelectedFiles((prevFiles) => [...prevFiles, ...files]);
    setUploadStatus((prev) => [...prev, ...files.map(() => "Uploading…")]);
    const startIdx = uploadStatus.length;
    
    for (let i = 0; i < files.length; ++i) {
      const file = files[i];
      const idx = startIdx + i;
      const safeName = file.name.replace(/\s+/g, "_");
      const meta = { name: safeName, type: file.type, size: file.size };
      console.log('[DEBUG] Requesting presigned URL:', meta, 'to', `${backendUrl}/generate-presigned-url`);
      const res = await fetch(`${backendUrl}/generate-presigned-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(meta),
      });
      console.log('[DEBUG] Presign response status:', res.status);
      if (!res.ok) {
        const txt = await res.text();
        console.log('[DEBUG] Presign error response:', txt);
        setUploadStatus((prev) => {
          const next = [...prev];
          next[idx] = `Presign error ${res.status}: ${txt || res.statusText}`;
          return next;
        });
        continue;
      }
      const { url, key } = await res.json();
      console.log('[DEBUG] Got presigned URL:', url, 'S3 key:', key);
      const uploadRes = await fetch(url, {
        method: "PUT",
        body: file,
        headers: { "Content-Type": file.type },
      });
      console.log('[DEBUG] S3 upload response status:', uploadRes.status);
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

  const onDrop = useCallback((accepted: File[]) => {
    if (!accepted.length) return;
    // Only accept new files if the total count will be 3 or fewer
    const availableSlots = 3 - selectedFiles.length;
    if (availableSlots <= 0) {
      alert("Maximum 3 files allowed. Please remove some files before adding more.");
      return;
    }
    
    const filesToAdd = accepted.slice(0, availableSlots);
    handleFiles(filesToAdd);
  }, [selectedFiles.length]);

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
      alert("Maximum 3 files allowed. Please remove some files before adding more.");
      return;
    }
    
    handleFiles(files.slice(0, availableSlots));
  }

  const removeFile = (idx: number) => {
    setSelectedFiles(prev => {
      const next = [...prev];
      next.splice(idx, 1);
      return next;
    });
    setUploadStatus(prev => {
      const next = [...prev];
      next.splice(idx, 1);
      return next;
    });
    setPermanentKeys(prev => {
      // Remove corresponding permanent key if it exists
      if (idx < prev.length) {
        const next = [...prev];
        next.splice(idx, 1);
        return next;
      }
      return prev;
    });
  };
    
  const submitReport = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${backendUrl}/api/form-collector/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: "frontend-session",
          user_message: "Submit my report now",
          meta: { attachments: permanentKeys, submit: true },
        }),
      });
      if (!res.ok) throw new Error("Submit error");
      const data = await res.json();
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
    } catch (err) {
      setMessages((m) => [
        ...m,
        { sender: "agent", text: "Sorry, there was a problem submitting your report. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const skipAttachments = async () => {
    setLoading(true);
    try {
      // Instead of sending "no" to the API, we'll simulate the behavior of submitting files
      // and getting the error message, which is what we want to be consistent
      setMessages((m) => [
        ...m,
        { 
          sender: "agent", 
          text: "Would you like to add anything else? If not, click Submit to finalize your report." 
        }
      ]);
      
      // Hide the attachments UI
      setAwaitingAttachments(false);
      setSelectedFiles([]);
      setUploadStatus([]);
      
      // Add a fake permanentKey to ensure the Submit button shows
      setPermanentKeys(["skipped-attachments"]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        { sender: "agent", text: "Sorry, there was a problem. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

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
      const res = await fetch(`${backendUrl}/api/form-collector/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: "frontend-session",
          user_message: input,
          meta,
        }),
      });
      if (!res.ok) throw new Error("Agent error");
      const data = await res.json();
      setMessages((msgs) => [
        ...msgs,
        { sender: "agent", text: data.assistant_message },
      ]);
      
      // Check if the new message is an attachment prompt
      const isNewAttachmentPrompt = isAttachmentPrompt(data.assistant_message);
      
      // Always show attachment UI if it's a new attachment prompt
      if (isNewAttachmentPrompt) {
        setAwaitingAttachments(true);
        // Reset file states when a new attachment prompt is received
        setSelectedFiles([]);
        setUploadStatus([]);
        setPermanentKeys([]);
        setAllFilesReady(false);
      }
    } catch (err: any) {
      setMessages((msgs) => [
        ...msgs,
        { sender: "agent", text: "Sorry, something went wrong." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    if (!reportSubmitted) {
      const lastAgentMsg =
        messages.length > 0 ? messages[messages.length - 1].text : "";
      // Debug log for troubleshooting
      console.log(
        "Last agent message:",
        lastAgentMsg,
        "Attachment prompt:",
        isAttachmentPrompt(lastAgentMsg)
      );
      
      // If it's an attachment prompt, set awaiting attachments
      if (isAttachmentPrompt(lastAgentMsg)) {
        setAwaitingAttachments(true);
      }
    }
  }, [messages, reportSubmitted]);

  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, loading]);

  // Show uploads section if user has added files or we're awaiting attachments
  const showUploadsSection = !reportSubmitted && awaitingAttachments; // Only show when explicitly awaiting attachments
  
  // Show submit button if there are files ready or skip was used
  const showSubmitButton = !reportSubmitted && (permanentKeys.length > 0 || !awaitingAttachments);

  return (
    <div className="fixed inset-0 flex flex-col bg-[#0b1021] text-white">
      {/* Message list */}
      <div
        ref={listRef}
        className="flex-1 overflow-y-auto p-4 flex flex-col gap-3"
      >
        {messages.map((msg, i) => (
          <div 
            key={i} 
            className={msg.sender === "user" ? "flex justify-end" : "flex justify-start"}
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
                Drag &amp; drop files here, or click to select&nbsp;files {selectedFiles.length > 0 ? `(${3 - selectedFiles.length} slots remaining)` : ""}
              </p>
            )}
          </div>
          <input type="file" multiple className="hidden" onChange={handleFileChange} />
          <ul className="mt-2">
            {selectedFiles.map((file, i) => (
              <li key={i} className="flex items-center justify-between my-1 text-white">
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
            className="bg-[#6d4aff] hover:bg-[#5d3aef] transition-colors text-white rounded-full w-10 h-10 flex items-center justify-center disabled:opacity-50"
            disabled={loading || !input.trim()}
            aria-label="Send"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M15.964.686a.5.5 0 0 0-.65-.65L.767 5.855H.766l-.452.18a.5.5 0 0 0-.082.887l.41.26.001.002 4.995 3.178 3.178 4.995.002.002.26.41a.5.5 0 0 0 .886-.083l6-15Zm-1.833 1.89L6.637 10.07l-.215-.338a.5.5 0 0 0-.154-.154l-.338-.215 7.494-7.494 1.178-.471-.47 1.178Z"/>
            </svg>
          </button>
          
          {/* Submit button - ALWAYS here when it should be visible */}
          {showSubmitButton && (
            <button
              className="bg-gradient-to-r from-[#6d4aff] to-[#8c5eff] hover:opacity-90 transition-opacity text-white rounded-full px-5 py-2 font-bold disabled:opacity-50"
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

export default ChatUI;
