"use client";

import { useState } from "react";

export default function Chat() {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input) return;

    setLoading(true);

    const res = await fetch("http://localhost:8000/ask", {
      method: "POST",
      body: JSON.stringify({ query: input }),
      headers: { "Content-Type": "application/json" },
    });

    const data = await res.json();

    setMessages((prev) => [
      ...prev,
      { role: "user", content: input },
      { role: "assistant", content: data.answer },
    ]);

    setInput("");
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`p-3 rounded-lg max-w-xl ${
              msg.role === "user"
                ? "bg-primary self-end"
                : "bg-slate-800 self-start"
            }`}
          >
            {msg.content}
          </div>
        ))}

        {loading && (
          <div className="text-muted text-sm">Thinking...</div>
        )}
      </div>

      <div className="flex gap-2 p-4 border-t border-slate-700">
        <input
          className="flex-1 p-3 rounded bg-slate-800 outline-none"
          placeholder="Ask your tutor..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />

        <button
          onClick={sendMessage}
          className="bg-primary px-5 rounded hover:opacity-90"
        >
          Send
        </button>
      </div>
    </div>
  );
}