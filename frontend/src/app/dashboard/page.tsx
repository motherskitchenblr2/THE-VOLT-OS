"use client";

import { useState } from "react";

const panels = [
  { id: "pipeline", title: "Pipeline Progress", icon: "🔄" },
  { id: "agents", title: "Agent Status", icon: "🤖" },
  { id: "cost", title: "Cost Monitor", icon: "💰" },
  { id: "tokens", title: "Token Usage", icon: "📊" },
  { id: "latency", title: "Latency", icon: "⚡" },
  { id: "security", title: "Security Score", icon: "🛡️" },
  { id: "audit", title: "Audit Log", icon: "📋" },
  { id: "memory", title: "Memory Usage", icon: "🧠" },
  { id: "builds", title: "Build Status", icon: "🏗️" },
  { id: "deploys", title: "Deployments", icon: "🚀" },
  { id: "artifacts", title: "Artifacts", icon: "📦" },
  { id: "errors", title: "Error History", icon: "⚠️" },
];

const agentStatus = [
  { name: "Researcher", status: "idle", model: "claude-sonnet-4", tasks: 3, cost: "$0.45" },
  { name: "Architect", status: "idle", model: "claude-sonnet-4", tasks: 2, cost: "$0.82" },
  { name: "Frontend Dev", status: "idle", model: "claude-sonnet-4", tasks: 1, cost: "$1.20" },
  { name: "Backend Dev", status: "idle", model: "claude-sonnet-4", tasks: 1, cost: "$1.15" },
  { name: "QA", status: "idle", model: "gpt-4o", tasks: 1, cost: "$0.38" },
  { name: "Memory Manager", status: "idle", model: "gpt-4o", tasks: 5, cost: "$0.12" },
  { name: "Sentinel", status: "idle", model: "gpt-4o", tasks: 2, cost: "$0.28" },
];

const pipelineStages = [
  { name: "Discovery", status: "completed", agent: "Researcher" },
  { name: "Research", status: "completed", agent: "Researcher" },
  { name: "Architecture", status: "completed", agent: "Architect" },
  { name: "Planning", status: "completed", agent: "Architect" },
  { name: "Pre-Dev Gate", status: "passed", agent: "System" },
  { name: "Frontend Dev", status: "completed", agent: "Frontend Dev" },
  { name: "Backend Dev", status: "completed", agent: "Backend Dev" },
  { name: "Testing", status: "completed", agent: "QA" },
  { name: "Security", status: "completed", agent: "Sentinel" },
  { name: "Pre-Deploy Gate", status: "passed", agent: "System" },
  { name: "Deployment", status: "completed", agent: "Infra" },
];

export default function Dashboard() {
  const [activePanel, setActivePanel] = useState("agents");

  return (
    <div className="flex flex-col h-full">
      {/* Global Status Bar */}
      <header className="h-12 border-b border-zinc-800 flex items-center px-4 justify-between">
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium">Mission Control</span>
          <span className="text-xs text-zinc-500">project: restaurant-app</span>
        </div>
        <div className="flex items-center gap-4 text-xs text-zinc-400">
          <span>⏱️ 14:32 elapsed</span>
          <span>💰 $4.40 total</span>
          <span>✅ 11/11 stages</span>
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
        </div>
      </header>

      {/* Panel Grid */}
      <div className="flex-1 p-4 overflow-auto">
        {/* Top row: Pipeline + Agent Status */}
        <div className="grid grid-cols-12 gap-4 mb-4">
          {/* Pipeline */}
          <div className="col-span-8 bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <h3 className="text-sm font-medium mb-3">Pipeline Progress</h3>
            <div className="flex gap-1">
              {pipelineStages.map((stage, i) => (
                <div key={i} className="flex-1 group">
                  <div
                    className={`h-8 rounded flex items-center justify-center text-[10px] font-medium ${
                      stage.status === "completed"
                        ? "bg-emerald-600/20 text-emerald-400 border border-emerald-600/30"
                        : stage.status === "passed"
                        ? "bg-violet-600/20 text-violet-400 border border-violet-600/30"
                        : stage.status === "running"
                        ? "bg-amber-600/20 text-amber-400 border border-amber-600/30 animate-pulse"
                        : "bg-zinc-800 text-zinc-500 border border-zinc-700"
                    }`}
                  >
                    {stage.name}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="col-span-4 grid grid-cols-2 gap-2">
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-3">
              <div className="text-[10px] text-zinc-500 uppercase">Tokens</div>
              <div className="text-lg font-bold">12.4K</div>
            </div>
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-3">
              <div className="text-[10px] text-zinc-500 uppercase">Cost</div>
              <div className="text-lg font-bold">$4.40</div>
            </div>
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-3">
              <div className="text-[10px] text-zinc-500 uppercase">Latency</div>
              <div className="text-lg font-bold">1.2s</div>
            </div>
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-3">
              <div className="text-[10px] text-zinc-500 uppercase">Security</div>
              <div className="text-lg font-bold text-emerald-400">A+</div>
            </div>
          </div>
        </div>

        {/* Agent Status Grid */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <h3 className="text-sm font-medium mb-3">Agent Status</h3>
          <div className="grid grid-cols-7 gap-2">
            {agentStatus.map((agent) => (
              <div key={agent.name} className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-3 text-center">
                <div className="text-[10px] text-zinc-500 mb-1">{agent.name}</div>
                <div className={`w-2 h-2 rounded-full mx-auto mb-1 ${
                  agent.status === "running" ? "bg-amber-500 animate-pulse" : "bg-zinc-600"
                }`}></div>
                <div className="text-[10px] text-zinc-400">{agent.model}</div>
                <div className="text-[10px] text-zinc-500 mt-1">{agent.tasks} tasks</div>
                <div className="text-[10px] text-zinc-500">{agent.cost}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
