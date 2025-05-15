"use client";
/**
 * @deprecated This component is deprecated and will be removed in a future version.
 * Please use UnifiedChatUI from '@/components/features/UnifiedChatUI' instead.
 * See documentation in /docs/UNIFIED_CHAT_INTERFACE.md for migration details.
 */
import React, { useState, useRef, useEffect } from "react";

interface Message {
  sender: "user" | "agent";
  text: string;
}

const backendUrl =
  process.env.NEXT_PUBLIC_AGNO_BACKEND ||
  "http://localhost:8001/api/agno-agent/chat";

/**
 * @deprecated Please use UnifiedChatUI component instead.
 */
const AgnoChatUI: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "agent",
      text: "Hi! I'm the Agno Agent. How can I help you today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    const userMsg = { sender: "user", text: input };
    setMessages((msgs) => [...msgs, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(backendUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: "agno-chat-session",
          user_message: userMsg.text,
          meta: {},
        }),
      });
      if (!res.ok) throw new Error("Agent error");
      const data = await res.json();
      setMessages((msgs) => [
        ...msgs,
        { sender: "agent", text: data.assistant_message },
      ]);
    } catch (err) {
      setMessages((msgs) => [
        ...msgs,
        { sender: "agent", text: "Sorry, something went wrong." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, loading]);

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

      {/* Message input */}
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
        </form>
      </div>
    </div>
  );
};

// Optional: global scrollbar styles for visual match
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

if (typeof document !== "undefined") {
  const style = document.createElement("style");
  style.type = "text/css";
  style.appendChild(document.createTextNode(scrollbarStyles));
  document.head.appendChild(style);
}

export default AgnoChatUI;