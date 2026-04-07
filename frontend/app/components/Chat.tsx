"use client";

import { useMemo, useState } from "react";

type Message = { role: "user" | "assistant"; content: string };

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Chat({ webEnabled }: { webEnabled: boolean }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const sessionId = useMemo(() => {
    if (typeof window === "undefined") return "default";
    const existing = localStorage.getItem("ai_tutor_session");
    if (existing) return existing;
    const generated = crypto.randomUUID();
    localStorage.setItem("ai_tutor_session", generated);
    return generated;
  }, []);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userInput = input.trim();
    setError("");
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: userInput }]);
    setInput("");

    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        body: JSON.stringify({
          query: userInput,
          web_enabled: webEnabled,
          session_id: sessionId,
        }),
        headers: { "Content-Type": "application/json" },
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail ?? "Request failed");
      }

      setMessages((prev) => [...prev, { role: "assistant", content: data.answer }]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unexpected chat error";
      setError(message);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "I hit an error while generating the answer. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`p-3 rounded-lg max-w-xl ${
              msg.role === "user" ? "bg-primary self-end" : "bg-slate-800 self-start"
            }`}
          >
            {msg.content}
          </div>
        ))}

        {loading && <div className="text-muted text-sm">Thinking...</div>}
        {error && <div className="text-red-400 text-sm">Error: {error}</div>}
      </div>

      <div className="flex gap-2 p-4 border-t border-slate-700">
        <input
          className="flex-1 p-3 rounded bg-slate-800 outline-none"
          placeholder="Ask your tutor..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          disabled={loading}
        />

        <button
          onClick={sendMessage}
          className="bg-primary px-5 rounded hover:opacity-90 disabled:opacity-50"
          disabled={loading}
        >
          Send
        </button>
      </div>
    </div>
  );
}
