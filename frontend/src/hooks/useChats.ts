import { useCallback, useEffect, useMemo, useState } from "react";
import type { Chat, Message } from "../types";

const STORAGE_KEY = "lead-agent.chats.v1";
const ACTIVE_KEY = "lead-agent.activeChatId.v1";

function uid() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function loadChats(): Chat[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed as Chat[];
  } catch {
    return [];
  }
}

export function useChats() {
  const [chats, setChats] = useState<Chat[]>(() => loadChats());
  const [activeId, setActiveId] = useState<string | null>(
    () => localStorage.getItem(ACTIVE_KEY) || null
  );

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(chats));
  }, [chats]);

  useEffect(() => {
    if (activeId) localStorage.setItem(ACTIVE_KEY, activeId);
    else localStorage.removeItem(ACTIVE_KEY);
  }, [activeId]);

  const activeChat = useMemo(
    () => chats.find((c) => c.id === activeId) ?? null,
    [chats, activeId]
  );

  const createChat = useCallback((): Chat => {
    const now = Date.now();
    const chat: Chat = {
      id: uid(),
      title: "New chat",
      messages: [],
      createdAt: now,
      updatedAt: now,
    };
    setChats((prev) => [chat, ...prev]);
    setActiveId(chat.id);
    return chat;
  }, []);

  const deleteChat = useCallback(
    (id: string) => {
      setChats((prev) => {
        const next = prev.filter((c) => c.id !== id);
        if (activeId === id) {
          setActiveId(next[0]?.id ?? null);
        }
        return next;
      });
    },
    [activeId]
  );

  const renameChat = useCallback((id: string, title: string) => {
    setChats((prev) =>
      prev.map((c) =>
        c.id === id ? { ...c, title: title.trim() || c.title, updatedAt: Date.now() } : c
      )
    );
  }, []);

  const appendMessage = useCallback(
    (chatId: string, msg: Omit<Message, "id" | "createdAt">) => {
      const full: Message = { ...msg, id: uid(), createdAt: Date.now() };
      setChats((prev) =>
        prev.map((c) => {
          if (c.id !== chatId) return c;
          const isFirstUser =
            c.messages.length === 0 && msg.role === "user" && c.title === "New chat";
          return {
            ...c,
            title: isFirstUser ? derivedTitle(msg.content) : c.title,
            messages: [...c.messages, full],
            updatedAt: Date.now(),
          };
        })
      );
      return full;
    },
    []
  );

  return {
    chats,
    activeChat,
    activeId,
    setActiveId,
    createChat,
    deleteChat,
    renameChat,
    appendMessage,
  };
}

function derivedTitle(text: string): string {
  const trimmed = text.trim().replace(/\s+/g, " ");
  if (!trimmed) return "New chat";
  return trimmed.length > 48 ? trimmed.slice(0, 45) + "…" : trimmed;
}
