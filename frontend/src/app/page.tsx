import { Header } from "@/components/layout/header";
import { ChatContainer } from "@/components/chat/chat-container";

export default function Home() {
  return (
    <div className="flex h-screen flex-col">
      <Header />
      <ChatContainer />
    </div>
  );
}
