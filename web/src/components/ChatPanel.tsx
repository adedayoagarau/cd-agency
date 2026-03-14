import { useState, useRef, useEffect } from "react";
import { useStore } from "../store";
import { chatWithAgent } from "../api";

export function ChatPanel() {
  const {
    selectedAgent, messages, addMessage, clearMessages,
    loading, setLoading, addTokens, setError,
  } = useStore();
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight);
  }, [messages]);

  const send = async () => {
    if (!input.trim() || !selectedAgent || loading) return;
    const userMsg = { role: "user" as const, content: input.trim() };
    addMessage(userMsg);
    setInput("");
    setLoading(true);
    setError("");

    try {
      const allMsgs = [...messages, userMsg];
      const res = await chatWithAgent(selectedAgent.slug, allMsgs);
      addMessage({ role: "assistant", content: res.content });
      addTokens(res.input_tokens + res.output_tokens);
    } catch (err: any) {
      setError(err.message);
      addMessage({ role: "assistant", content: `Error: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="panel chat-panel">
      <div className="chat-messages" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="empty-state">
            {selectedAgent
              ? `Start a conversation with ${selectedAgent.name}`
              : "Select an agent from the sidebar to begin"}
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`chat-msg chat-msg-${msg.role}`}>
            <div className="chat-msg-role">
              {msg.role === "user" ? "You" : selectedAgent?.name || "Agent"}
            </div>
            <div className="chat-msg-content">{msg.content}</div>
          </div>
        ))}
        {loading && <div className="chat-msg chat-msg-loading">Thinking...</div>}
      </div>
      <div className="chat-input-bar">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={selectedAgent ? "Type a message..." : "Select an agent first"}
          disabled={!selectedAgent || loading}
          rows={2}
          className="chat-input"
        />
        <div className="chat-actions">
          <button className="btn btn-sm" onClick={clearMessages}>Clear</button>
          <button
            className="btn btn-sm btn-primary"
            onClick={send}
            disabled={!input.trim() || !selectedAgent || loading}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
