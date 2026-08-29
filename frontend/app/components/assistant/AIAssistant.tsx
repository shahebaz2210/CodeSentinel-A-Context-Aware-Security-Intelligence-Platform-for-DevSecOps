"use client";
import { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
}

interface Props {
  scanId?: string;
  findingId?: string;
}

export default function AIAssistant({ scanId, findingId }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm the CodeSentinel AI Security Assistant. I can explain vulnerabilities, answer security questions, and help you understand findings — all grounded in your actual scan data and security knowledge base.\n\n⚙️ Risk scores and gate results shown are computed deterministically — not by me.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage() {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    // Add streaming placeholder
    setMessages((prev) => [...prev, { role: "assistant", content: "", streaming: true }]);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const token = typeof window !== "undefined" ? localStorage.getItem("github_token") : null;

    try {
      const res = await fetch(`${apiUrl}/api/assistant/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ question, scan_id: scanId, finding_id: findingId }),
      });

      if (!res.ok) throw new Error("Request failed");

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n").filter((l) => l.startsWith("data: "));
          for (const line of lines) {
            const data = line.slice(6);
            if (data === "[DONE]") break;
            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                accumulated += parsed.content;
                setMessages((prev) => {
                  const updated = [...prev];
                  updated[updated.length - 1] = { role: "assistant", content: accumulated, streaming: true };
                  return updated;
                });
              }
            } catch {}
          }
        }
      }

      // Mark as done
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = { role: "assistant", content: accumulated || "I couldn't generate a response.", streaming: false };
        return updated;
      });
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = { role: "assistant", content: "Failed to connect to the AI assistant. Please check your backend connection.", streaming: false };
        return updated;
      });
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  const quickQuestions = [
    "Explain the highest risk finding",
    "How can I fix the critical issues?",
    "What is the OWASP category for these findings?",
    "Is this a false positive?",
  ];

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        background: "var(--cs-bg-card)",
        border: "1px solid var(--cs-border)",
        borderRadius: 12,
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid var(--cs-border)",
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <span style={{ fontSize: 16 }}>🤖</span>
        <span style={{ fontWeight: 700, fontSize: 13 }}>AI Security Assistant</span>
        <span className="ai-badge" style={{ marginLeft: 4 }}>✦ AI</span>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px", display: "flex", flexDirection: "column", gap: 12 }}>
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              gap: 10,
              alignItems: "flex-start",
              flexDirection: msg.role === "user" ? "row-reverse" : "row",
            }}
            className="animate-fade-in"
          >
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: "50%",
                background: msg.role === "user" ? "var(--cs-accent-dim)" : "rgba(92,155,255,0.15)",
                border: `1px solid ${msg.role === "user" ? "rgba(0,212,170,0.3)" : "rgba(92,155,255,0.3)"}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 12,
                flexShrink: 0,
              }}
            >
              {msg.role === "user" ? "👤" : "🤖"}
            </div>
            <div
              style={{
                maxWidth: "85%",
                padding: "10px 14px",
                borderRadius: 10,
                background: msg.role === "user" ? "var(--cs-accent-dim)" : "var(--cs-bg)",
                border: `1px solid ${msg.role === "user" ? "rgba(0,212,170,0.2)" : "var(--cs-border)"}`,
                fontSize: 13,
                lineHeight: 1.6,
                color: "var(--cs-text)",
                whiteSpace: "pre-wrap",
              }}
            >
              {msg.content}
              {msg.streaming && (
                <span
                  style={{
                    display: "inline-block",
                    width: 6,
                    height: 14,
                    background: "var(--cs-accent)",
                    marginLeft: 2,
                    borderRadius: 1,
                    animation: "blink 1s step-end infinite",
                  }}
                />
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Quick questions */}
      {messages.length <= 1 && (
        <div style={{ padding: "0 16px 12px", display: "flex", gap: 6, flexWrap: "wrap" }}>
          {quickQuestions.map((q) => (
            <button
              key={q}
              onClick={() => { setInput(q); inputRef.current?.focus(); }}
              style={{
                padding: "4px 10px",
                borderRadius: 6,
                border: "1px solid var(--cs-border)",
                background: "transparent",
                color: "var(--cs-text-muted)",
                fontSize: 11,
                cursor: "pointer",
                transition: "all 0.15s",
              }}
              onMouseEnter={(e) => { (e.target as HTMLElement).style.borderColor = "rgba(0,212,170,0.4)"; }}
              onMouseLeave={(e) => { (e.target as HTMLElement).style.borderColor = "var(--cs-border)"; }}
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{ padding: "12px 16px", borderTop: "1px solid var(--cs-border)", display: "flex", gap: 8 }}>
        <textarea
          id="assistant-input"
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about security vulnerabilities, fixes, or patterns..."
          rows={2}
          style={{
            flex: 1,
            resize: "none",
            background: "var(--cs-bg)",
            border: "1px solid var(--cs-border)",
            borderRadius: 8,
            padding: "8px 12px",
            color: "var(--cs-text)",
            fontSize: 13,
            fontFamily: "inherit",
            outline: "none",
            lineHeight: 1.5,
          }}
          onFocus={(e) => { (e.target as HTMLElement).style.borderColor = "var(--cs-accent)"; }}
          onBlur={(e) => { (e.target as HTMLElement).style.borderColor = "var(--cs-border)"; }}
        />
        <button
          id="assistant-send-btn"
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="btn-primary"
          style={{ padding: "8px 14px", fontSize: 13, alignSelf: "flex-end", opacity: loading || !input.trim() ? 0.5 : 1 }}
        >
          {loading ? "…" : "→"}
        </button>
      </div>
    </div>
  );
}
