import { redirect } from 'next/navigation';

// Server-side redirect component - more efficient than client-side redirect
export default function ChatWithRegistryPage() {
  // Redirect to main page with UI debug mode enabled
  redirect('/?ui_debug=true');
  
  // This part won't execute due to the redirect, but Next.js requires a component return
  return null;
}