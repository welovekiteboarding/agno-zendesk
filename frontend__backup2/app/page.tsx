import UnifiedChatUI from "@/components/features/UnifiedChatUI";
import Link from "next/link";

export default function Home() {
  return (
    <div className="fixed inset-0 flex flex-col items-center bg-[#0b1021] text-white">
      <header className="w-full max-w-5xl p-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-[#6d4aff] to-[#8c5eff] bg-clip-text text-transparent">
          Agno Chat
        </h1>
        <div className="text-sm text-gray-400">
          Try: "I want to report a bug" to see agent handoff
        </div>
      </header>
      
      {/* Added prominent Bug Report button */}
      <div className="absolute top-4 right-4 z-10">
        <a 
          href="/bug-report.html" 
          className="px-4 py-2 bg-[#242d4f] hover:bg-[#343e60] text-white rounded-md transition-colors"
        >
          Bug Report Form
        </a>
      </div>

      <main className="flex-1 w-full max-w-5xl p-4">
        <UnifiedChatUI
          agentType="agno"
          initialGreeting="Hi! I'm Agno, your AI assistant. How can I help you today? I can answer general questions or help you report bugs when needed."
          sessionId="agno-main-session-v2"
        />
      </main>
    </div>
  );
}
