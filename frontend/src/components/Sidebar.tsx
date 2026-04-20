import { useState } from "react";
import { Plus, MessageSquare, Trash2, Search } from "lucide-react";
import type { Chat } from "../types";

type Props = {
  chats: Chat[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete: (id: string) => void;
};

export default function Sidebar({
  chats,
  activeId,
  onSelect,
  onNewChat,
  onDelete,
}: Props) {
  const [query, setQuery] = useState("");

  const filtered = query.trim()
    ? chats.filter((c) =>
        c.title.toLowerCase().includes(query.trim().toLowerCase())
      )
    : chats;

  return (
    <aside className="flex h-full w-72 shrink-0 flex-col border-r border-canvas-600/60 bg-canvas-850">
      {/* Brand */}
      <div className="flex items-center gap-2 px-4 py-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-indigo-400 to-violet-500 text-xs font-bold text-white">
          L
        </div>
        <span className="text-[14px] font-semibold text-white">Lead Agent</span>
      </div>

      {/* New chat */}
      <div className="px-3">
        <button
          onClick={onNewChat}
          className="flex w-full items-center justify-center gap-2 rounded-lg border border-canvas-600/70 bg-canvas-800 px-3 py-2 text-[13px] font-medium text-white transition hover:bg-canvas-700"
        >
          <Plus className="h-4 w-4" />
          New chat
        </button>
      </div>

      {/* Search */}
      <div className="mt-3 px-3">
        <div className="flex items-center gap-2 rounded-lg bg-canvas-800 px-3 py-1.5">
          <Search className="h-3.5 w-3.5 text-muted-fg" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search chats"
            className="w-full bg-transparent text-[12px] text-white placeholder:text-muted-fg focus:outline-none"
          />
        </div>
      </div>

      {/* History */}
      <div className="mt-4 px-2 text-[11px] font-semibold uppercase tracking-wider text-muted-fg">
        <div className="px-2 pb-1">History</div>
      </div>

      <nav className="flex-1 overflow-y-auto px-2 pb-3">
        {filtered.length === 0 ? (
          <div className="px-3 py-6 text-center text-[12px] text-muted-fg">
            {chats.length === 0
              ? "No chats yet. Start a new one."
              : "No chats match your search."}
          </div>
        ) : (
          <ul className="space-y-0.5">
            {filtered.map((chat) => (
              <SidebarChatItem
                key={chat.id}
                chat={chat}
                active={chat.id === activeId}
                onSelect={() => onSelect(chat.id)}
                onDelete={() => onDelete(chat.id)}
              />
            ))}
          </ul>
        )}
      </nav>

      {/* Footer */}
      <div className="border-t border-canvas-600/60 px-4 py-3 text-[11px] text-muted-fg">
        {chats.length} chat{chats.length === 1 ? "" : "s"}
      </div>
    </aside>
  );
}

function SidebarChatItem({
  chat,
  active,
  onSelect,
  onDelete,
}: {
  chat: Chat;
  active: boolean;
  onSelect: () => void;
  onDelete: () => void;
}) {
  const [confirming, setConfirming] = useState(false);

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirming) {
      setConfirming(true);
      setTimeout(() => setConfirming(false), 2500);
      return;
    }
    onDelete();
  };

  return (
    <li>
      <div
        onClick={onSelect}
        className={`group flex cursor-pointer items-center gap-2 rounded-md px-2 py-2 text-[13px] transition-colors ${
          active
            ? "bg-canvas-700 text-white"
            : "text-muted-fg2 hover:bg-canvas-700/70 hover:text-white"
        }`}
      >
        <MessageSquare className="h-3.5 w-3.5 shrink-0 text-muted-fg" />
        <span className="min-w-0 flex-1 truncate" title={chat.title}>
          {chat.title}
        </span>
        <button
          onClick={handleDelete}
          title={confirming ? "Click again to confirm" : "Delete chat"}
          className={`shrink-0 rounded p-1 text-muted-fg transition ${
            active
              ? "opacity-100"
              : "opacity-0 group-hover:opacity-100"
          } hover:bg-canvas-600 hover:text-red-400 ${
            confirming ? "text-red-400 opacity-100" : ""
          }`}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
    </li>
  );
}
