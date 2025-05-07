"use client";
import React, { useState } from 'react';

interface Message {
  sender: 'user' | 'agent';
  text: string;
}

const backendUrl = process.env.NEXT_PUBLIC_BACKEND || 'http://localhost:8001';

const ChatUI: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'agent', text: 'Hi! I can help you submit a bug report. What is your email address?' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    const userMsg = { sender: 'user', text: input };
    setMessages((msgs) => [...msgs, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const res = await fetch(`${backendUrl}/api/form-collector/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: 'frontend-session', user_message: input }),
      });
      if (!res.ok) throw new Error('Agent error');
      const data = await res.json();
      setMessages((msgs) => [...msgs, { sender: 'agent', text: data.assistant_message }]);
    } catch (err: any) {
      setMessages((msgs) => [...msgs, { sender: 'agent', text: 'Sorry, something went wrong.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-lg border rounded p-4 bg-white dark:bg-gray-900">
      <div className="h-64 overflow-y-auto flex flex-col gap-2 mb-4">
        {messages.map((msg, i) => (
          <div key={i} className={msg.sender === 'user' ? 'text-right' : 'text-left'}>
            <span className={msg.sender === 'user' ? 'bg-blue-100 text-blue-900 rounded px-2 py-1 inline-block' : 'bg-gray-100 text-gray-900 rounded px-2 py-1 inline-block'}>
              {msg.text}
            </span>
          </div>
        ))}
        {loading && <div className="text-left text-gray-400">Agent is typing…</div>}
      </div>
      <form onSubmit={sendMessage} className="flex gap-2">
        <input
          className="flex-1 border rounded p-2"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={loading}
        />
        <button type="submit" className="bg-blue-600 text-white rounded px-4 py-2" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatUI;
