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
  const pollingRefs = useRef<{ [key: string]: NodeJS.Timeout }>({});
  const listRef = useRef<HTMLDivElement>(null);

  // Broader: looks for any combination of “upload/attach/file/attachment”
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
        setPermanentKeys((prev) => [...prev, permKey]);
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

  /* Unified handler so we can reuse for <input> and Dropzone */
  const handleFiles = async (files: File[]) => {
    setSelectedFiles(files);
    setUploadStatus(files.map(() => "Uploading…"));
    setPermanentKeys([]);
    for (let i = 0; i < files.length; ++i) {
      const file = files[i];
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
          next[i] = `Presign error ${res.status}: ${txt || res.statusText}`;
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
          next[i] = "Failed to upload to S3";
          return next;
        });
        continue;
      }
      setUploadStatus((prev) => {
        const next = [...prev];
        next[i] = "Uploaded, scanning…";
        return next;
      });
      pollForPermanent(key, i);
    }
  };

  const onDrop = useCallback((accepted: File[]) => {
    if (!accepted.length) return;
    handleFiles(accepted.slice(0, 3)); // cap at 3 files
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    maxFiles: 3,
  });

  /* Handle file‑picker fallback */
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) =>
    handleFiles(Array.from(e.target.files || []));

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
      setAwaitingAttachments(isAttachmentPrompt(data.assistant_message));
      setSelectedFiles([]);
      setUploadStatus([]);
      setPermanentKeys([]);
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
    const lastAgentMsg =
      messages.length > 0 ? messages[messages.length - 1].text : "";
    // Debug log for troubleshooting
    console.log(
      "Last agent message:",
      lastAgentMsg,
      "Attachment prompt:",
      isAttachmentPrompt(lastAgentMsg)
    );
    setAwaitingAttachments(isAttachmentPrompt(lastAgentMsg));
  }, [messages]);

  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, loading]);

  return (
    <div className="fixed inset-0 flex flex-col bg-white dark:bg-gray-900">
      {/* Message list */}
      <div
        ref={listRef}
        className="flex-1 overflow-y-auto p-4 flex flex-col gap-2"
      >
        {messages.map((msg, i) => (
          <div key={i} className={msg.sender === "user" ? "text-right" : "text-left"}>
            <span
              className={
                msg.sender === "user"
                  ? "bg-blue-100 text-blue-900 rounded px-2 py-1 inline-block"
                  : "bg-gray-100 text-gray-900 rounded px-2 py-1 inline-block"
              }
            >
              {msg.text}
            </span>
          </div>
        ))}
        {loading && <div className="text-left text-gray-400">Agent is typing…</div>}
      </div>
      {awaitingAttachments && (
        <div className="border-t p-4">
          <label className="block font-semibold mb-2">
            Upload attachments (up to 3 files, 100&nbsp;MB each):
          </label>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded p-4 text-center cursor-pointer transition ${
              isDragActive
                ? "border-blue-600 bg-blue-50 dark:bg-gray-800"
                : "border-gray-400 dark:border-gray-600"
            }`}
          >
            <input {...getInputProps()} />
            {isDragActive ? (
              <p>Drop the files here…</p>
            ) : (
              <p>
                Drag &amp; drop files here, or click to select&nbsp;files
              </p>
            )}
          </div>
          <input type="file" multiple className="hidden" onChange={handleFileChange} />
          <ul className="mt-2">
            {selectedFiles.map((file, i) => (
              <li key={i}>
                {file.name} — {uploadStatus[i]}
                {uploadStatus[i]?.startsWith("Infected") && (
                  <button
                    className="ml-2 underline text-blue-600"
                    onClick={() => handleFiles([file])}
                  >
                    Retry
                  </button>
                )}
                {uploadStatus[i]?.startsWith("Clean") && <span> ✔️</span>}
              </li>
            ))}
          </ul>
          <div className="mt-2">
            <button
              className="bg-blue-600 text-white rounded px-4 py-2"
              disabled={permanentKeys.length === 0 || loading}
              onClick={async () => {
                setLoading(true);
                const res = await fetch(`${backendUrl}/api/form-collector/chat`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    session_id: "frontend-session",
                    user_message: "",
                    meta: { attachments: permanentKeys },
                  }),
                });
                const data = await res.json();
                setMessages((m) => [
                  ...m,
                  { sender: "agent", text: data.assistant_message },
                ]);
                setAwaitingAttachments(isAttachmentPrompt(data.assistant_message));
                setSelectedFiles([]);
                setUploadStatus([]);
                setPermanentKeys([]);
                setLoading(false);
              }}
            >
              Send Attachments
            </button>
            <button
              className="ml-2 bg-gray-400 text-white rounded px-4 py-2"
              disabled={loading}
              onClick={async () => {
                setLoading(true);
                const res = await fetch(`${backendUrl}/api/form-collector/chat`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    session_id: "frontend-session",
                    user_message: "no",
                  }),
                });
                const data = await res.json();
                setMessages((m) => [
                  ...m,
                  { sender: "agent", text: data.assistant_message },
                ]);
                setAwaitingAttachments(isAttachmentPrompt(data.assistant_message));
                setSelectedFiles([]);
                setUploadStatus([]);
                setPermanentKeys([]);
                setLoading(false);
              }}
            >
              Skip
            </button>
          </div>
        </div>
      )}
      <form
        onSubmit={sendMessage}
        className="border-t p-4 flex gap-2 bg-white dark:bg-gray-900"
      >
        <input
          className="flex-1 border rounded p-2"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message…"
          disabled={loading}
        />
        <button
          type="submit"
          className="bg-blue-600 text-white rounded px-4 py-2"
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatUI;
