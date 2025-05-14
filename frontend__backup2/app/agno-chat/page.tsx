import AgnoChatUI from '@/components/features/AgnoChatUI';

export default function AgnoChatPage() {
  return (
    <div className="w-full min-h-screen flex flex-col items-center justify-center bg-[#0b1021]">
      <h1 className="font-bold text-2xl mb-6 text-white">Agno Agent Chat</h1>
      <div className="w-full max-w-2xl">
        <AgnoChatUI />
      </div>
    </div>
  );
}