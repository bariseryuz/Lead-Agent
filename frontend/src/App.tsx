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

    // Call backend pipeline (served from same origin on Railway).
    (async () => {
      try {
        appendMessage(chatId!, {
          role: "assistant",
          content: "Searching…",
        });

        const resp = await fetch("/api/pipeline/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_query: text,
            max_events: 8,
            max_hunter: 3,
          }),
        });

        if (!resp.ok) {
          const errText = await resp.text();
          throw new Error(`${resp.status} ${resp.statusText}: ${errText}`);
        }

        const data = await resp.json();

        const extracted = Array.isArray(data?.extracted) ? data.extracted : [];
        const lines: string[] = [];
        lines.push(`Plan: ${data?.plan?.industry ?? "Unknown"} — ${data?.plan?.location ?? "Unknown"}`);
        lines.push("");

        if (extracted.length === 0) {
          lines.push("No pages extracted yet. Try increasing max_hunter or refining your query.");
        } else {
          lines.push("Top results:");
          for (const item of extracted.slice(0, 5)) {
            const company = item?.data?.company_name ?? "Unknown company";
            const addr = item?.data?.physical_address ?? "";
            lines.push(`- ${company}${addr ? ` — ${addr}` : ""}`);
          }
        }

        appendMessage(chatId!, {
          role: "assistant",
          content: lines.join("\n"),
        });
      } catch (e) {
        appendMessage(chatId!, {
          role: "assistant",
          content: `Request failed: ${e instanceof Error ? e.message : String(e)}`,
        });
      }
    })();
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
