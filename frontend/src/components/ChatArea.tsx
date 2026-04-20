import { useEffect, useRef } from "react";
import { Bot, User, Sparkles } from "lucide-react";
import type { Chat } from "../types";

type Props = {
  chat: Chat | null;
  onStartChat: () => void;
};

export default function ChatArea({ chat, onStartChat }: Props) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat?.messages.length, chat?.id]);

  if (!chat) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-6 text-center">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/20">
          <Sparkles className="h-7 w-7 text-white" />
        </div>
        <h2 className="text-xl font-semibold text-white">Lead Agent</h2>
        <p className="mt-2 max-w-sm text-sm text-muted-fg">
          Start a conversation to generate, validate, and enrich business leads.
        </p>
        <button
          onClick={onStartChat}
          className="mt-6 rounded-lg bg-white px-4 py-2 text-sm font-medium text-canvas-900 transition hover:bg-white/90"
        >
          Start a new chat
        </button>
      </div>
    );
  }

  if (chat.messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-6 text-center">
        <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-canvas-800">
          <Bot className="h-6 w-6 text-brand-accent" />
        </div>
        <h2 className="text-lg font-semibold text-white">How can I help?</h2>
        <p className="mt-1 max-w-sm text-sm text-muted-fg">
          Describe the industry, region, or type of leads you want to find.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-3xl flex-1 overflow-y-auto px-6 py-8">
      <div className="space-y-6">
        {chat.messages.map((m) => (
          <div
            key={m.id}
            className={`flex gap-3 ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {m.role === "assistant" && (
              <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-canvas-800">
                <Bot className="h-4 w-4 text-brand-accent" />
              </div>
            )}

            <div
              className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-[14px] leading-6 ${
                m.role === "user"
                  ? "bg-indigo-500/90 text-white"
                  : "bg-canvas-800 text-[#e2e4e7]"
              }`}
            >
              {m.content}
            </div>

            {m.role === "user" && (
              <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-canvas-700">
                <User className="h-4 w-4 text-white" />
              </div>
            )}
          </div>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
