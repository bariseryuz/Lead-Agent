import { useEffect } from "react";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";
import PromptInput from "./components/PromptInput";
import { useChats } from "./hooks/useChats";

export default function App() {
  const {
    chats,
    activeChat,
    activeId,
    setActiveId,
    createChat,
    deleteChat,
    appendMessage,
  } = useChats();

  // Ensure there's always an active chat available when user sends
  useEffect(() => {
    if (!activeId && chats.length > 0) {
      setActiveId(chats[0].id);
    }
  }, [activeId, chats, setActiveId]);

  const handleSend = (text: string) => {
    let chatId = activeChat?.id;
    if (!chatId) {
      const c = createChat();
      chatId = c.id;
    }
    appendMessage(chatId, { role: "user", content: text });

    // Placeholder assistant reply until the backend is wired up.
    setTimeout(() => {
      appendMessage(chatId!, {
        role: "assistant",
        content:
          "(The agent isn't connected yet — this is a placeholder reply. Next step: wire this to FastAPI + LangGraph.)",
      });
    }, 400);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-canvas-900 text-white">
      <Sidebar
        chats={chats}
        activeId={activeId}
        onSelect={setActiveId}
        onNewChat={createChat}
        onDelete={deleteChat}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-12 shrink-0 items-center border-b border-canvas-600/60 px-4 text-[14px] font-medium text-white/90">
          {activeChat?.title ?? "Lead Agent"}
        </header>

        <ChatArea chat={activeChat} onStartChat={createChat} />

        <PromptInput onSend={handleSend} />
      </main>
    </div>
  );
}
