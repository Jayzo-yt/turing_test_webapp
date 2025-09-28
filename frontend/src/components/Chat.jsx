import React, { useState, useRef } from "react";

export default function Chat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const ws = useRef(null);
  const [connected, setConnected] = useState(false);

  React.useEffect(() => {
    ws.current = new window.WebSocket("ws://127.0.0.1:8000/ws/chat");
    ws.current.onopen = () => setConnected(true);
    ws.current.onclose = () => setConnected(false);
    ws.current.onmessage = (event) => {
      setMessages((prev) => {
        if (prev.length > 0 && prev[prev.length - 1].from === "bot") {
          return [
            ...prev.slice(0, -1),
            { from: "bot", text: event.data }
          ];
        } else {
          return [...prev, { from: "bot", text: event.data }];
        }
      });
    };
    return () => {
      ws.current && ws.current.close();
    };
  }, []);

  const sendMessage = (e) => {
    e.preventDefault();
    if (input.trim() && ws.current && connected) {
      setMessages((prev) => [...prev, { from: "user", text: input }]);
      ws.current.send(input);
      setInput("");
    }
  };

  return (
    <div className="max-w-xl mx-auto mt-8 p-4 bg-white dark:bg-zinc-900 rounded shadow">
      <h2 className="text-lg font-bold mb-2">Turing Chat</h2>
      <div className="h-64 overflow-y-auto border p-2 mb-2 bg-gray-50 dark:bg-zinc-800 rounded">
        {messages.map((msg, idx) => (
          <div key={idx} className={msg.from === "user" ? "text-right" : "text-left"}>
            <span className={msg.from === "user" ? "text-blue-600" : "text-green-600"}>
              {msg.from === "user" ? "You: " : "Bot: "}
              {msg.text}
            </span>
          </div>
        ))}
      </div>
      <form onSubmit={sendMessage} className="flex gap-2">
        <input
          className="flex-1 border rounded px-2 py-1 dark:bg-zinc-700 dark:text-white"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={!connected}
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-1 rounded disabled:opacity-50"
          disabled={!connected || !input.trim()}
        >
          Send
        </button>
      </form>
      {!connected && <div className="text-red-500 mt-2">Connecting to chat server...</div>}
    </div>
  );
}
