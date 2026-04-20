import { useEffect, useRef, useState } from "react";
import { SendHorizontal } from "lucide-react";

type Props = {
  disabled?: boolean;
  onSend: (text: string) => void;
};

export default function PromptInput({ disabled, onSend }: Props) {
  const [value, setValue] = useState("");
  const taRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const el = taRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [value]);

  const send = () => {
    const text = value.trim();
    if (!text || disabled) return;
    onSend(text);
    setValue("");
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="px-4 pb-5 pt-2">
      <div className="mx-auto w-full max-w-3xl">
        <div className="flex items-end gap-2 rounded-2xl border border-canvas-600/70 bg-canvas-800 px-3 py-2 shadow-lg shadow-black/30 focus-within:border-canvas-600">
          <textarea
            ref={taRef}
            rows={1}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Message Lead Agent…"
            className="max-h-[200px] flex-1 resize-none bg-transparent py-1.5 text-[14px] text-white placeholder:text-muted-fg focus:outline-none"
          />

          <button
            onClick={send}
            disabled={disabled || value.trim().length === 0}
            aria-label="Send message"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white text-canvas-900 transition hover:bg-white/90 disabled:cursor-not-allowed disabled:bg-canvas-700 disabled:text-muted-fg"
          >
            <SendHorizontal className="h-4 w-4" />
          </button>
        </div>
        <div className="mt-1.5 text-center text-[11px] text-muted-fg">
          Press <kbd className="rounded bg-canvas-800 px-1">Enter</kbd> to send ·{" "}
          <kbd className="rounded bg-canvas-800 px-1">Shift</kbd>+
          <kbd className="rounded bg-canvas-800 px-1">Enter</kbd> for newline
        </div>
      </div>
    </div>
  );
}
