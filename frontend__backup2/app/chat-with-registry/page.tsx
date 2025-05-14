'use client';

import ChatUIWithRegistry from '@/components/features/ChatUIWithRegistry';

export default function ChatWithRegistryPage() {
  return (
    <div className="w-full min-h-screen flex flex-col items-center justify-center bg-[#0b1021]">
      <h1 className="font-bold text-2xl mb-6 text-white">Chat with UI Component Registry</h1>
      <div className="w-full max-w-5xl h-[calc(100vh-6rem)]">
        <ChatUIWithRegistry />
      </div>
    </div>
  );
}