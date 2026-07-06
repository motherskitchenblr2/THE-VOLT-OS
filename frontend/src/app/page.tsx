"use client";

import { useState } from "react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function Workspace() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "VOLT OS ready. Describe your project and I'll activate the right agents.\n\nExamples:\n- \"Build a Flutter restaurant app with offline sync\"\n- \"Create a SaaS dashboard with user auth and billing\"\n- \"Generate a REST API for inventory management\"",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsProcessing(true);

    // Simulate agent response
    setTimeout(() => {
      const agentMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Analyzing your request...\n\n**Activating agents:**\n- 🔍 Researcher — gathering requirements\n- 🏗️ Architect — designing system\n- 💻 Frontend Dev — generating code\n- ⚙️ Backend Dev — building APIs\n- 🧪 QA — testing outputs\n- 🛡️ Sentinel — security review\n\n**Pipeline:** Discovery → Research → Architecture → Planning → [Gate] → Dev → Test → Security → [Gate] → Deploy\n\nProject created. Check Mission Control for real-time progress.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, agentMsg]);
      setIsProcessing(false);
    }, 1500);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="h-12 border-b border-zinc-800 flex items-center px-4 justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">AI Workspace</span>
          <span className="text-xs text-zinc-500">— Command Center</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span className="text-xs text-zinc-400">7 agents ready</span>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-2xl rounded-xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-violet-600/20 border border-violet-600/30"
                  : "bg-zinc-800/50 border border-zinc-700/50"
              }`}
            >
              <pre className="whitespace-pre-wrap font-sans">{msg.content}</pre>
            </div>
          </div>
        ))}
        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-xl px-4 py-3 text-sm">
              <span className="animate-pulse">Agents processing...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-zinc-800 p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe your project..."
            className="flex-1 bg-zinc-800/50 border border-zinc-700/50 rounded-lg px-4 py-2.5 text-sm placeholder-zinc-500 focus:outline-none focus:border-violet-500/50"
            disabled={isProcessing}
          />
          <button
            type="submit"
            disabled={isProcessing}
            className="px-4 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:bg-zinc-700 rounded-lg text-sm font-medium transition"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
