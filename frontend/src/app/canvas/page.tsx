"use client";

import { useState } from "react";

const nodes = [
  { id: "researcher", label: "Researcher", x: 50, y: 80, status: "completed", inputs: ["project_brief"], outputs: ["requirements", "tech_research", "feasibility_report"] },
  { id: "architect", label: "Architect", x: 250, y: 80, status: "completed", inputs: ["requirements", "tech_research", "feasibility_report"], outputs: ["architecture_spec", "task_breakdown", "risk_assessment", "tech_selection"] },
  { id: "gate1", label: "Pre-Dev Gate", x: 450, y: 80, status: "passed", inputs: ["architecture_spec", "task_breakdown"], outputs: [] },
  { id: "frontend", label: "Frontend Dev", x: 650, y: 30, status: "completed", inputs: ["architecture_spec", "task_breakdown"], outputs: ["code"] },
  { id: "backend", label: "Backend Dev", x: 650, y: 130, status: "completed", inputs: ["architecture_spec", "task_breakdown"], outputs: ["code"] },
  { id: "qa", label: "QA", x: 850, y: 80, status: "completed", inputs: ["code", "requirements"], outputs: ["test_report"] },
  { id: "sentinel", label: "Sentinel", x: 1050, y: 80, status: "completed", inputs: ["code", "test_report"], outputs: ["security_report"] },
  { id: "gate2", label: "Pre-Deploy Gate", x: 1250, y: 80, status: "passed", inputs: ["test_report", "security_report"], outputs: [] },
  { id: "deploy", label: "Deploy", x: 1450, y: 80, status: "completed", inputs: ["code", "security_report"], outputs: ["deploy_status"] },
];

export default function Canvas() {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  return (
    <div className="flex flex-col h-full">
      <header className="h-12 border-b border-zinc-800 flex items-center px-4 justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Visual Canvas</span>
          <span className="text-xs text-zinc-500">— Pipeline Workflow</span>
        </div>
        <div className="flex gap-2">
          <button className="px-3 py-1 text-xs bg-zinc-800 border border-zinc-700 rounded hover:bg-zinc-700 transition">Zoom In</button>
          <button className="px-3 py-1 text-xs bg-zinc-800 border border-zinc-700 rounded hover:bg-zinc-700 transition">Zoom Out</button>
          <button className="px-3 py-1 text-xs bg-zinc-800 border border-zinc-700 rounded hover:bg-zinc-700 transition">Fit</button>
        </div>
      </header>

      <div className="flex-1 relative overflow-auto bg-zinc-950">
        {/* Canvas */}
        <svg className="w-full h-full" viewBox="0 0 1600 250">
          {/* Edges */}
          <line x1="150" y1="80" x2="250" y2="80" stroke="#3f3f46" strokeWidth="2" markerEnd="url(#arrow)" />
          <line x1="350" y1="80" x2="450" y2="80" stroke="#3f3f46" strokeWidth="2" markerEnd="url(#arrow)" />
          <line x1="550" y1="80" x2="650" y2="30" stroke="#3f3f46" strokeWidth="2" markerEnd="url(#arrow)" />
          <line x1="550" y1="80" x2="650" y2="130" stroke="#3f3f46" strokeWidth="2" markerEnd="url(#arrow)" />
          <line x1="750" y1="30" x2="850" y2="80" stroke="#3f3f46" strokeWidth="2" markerEnd="url(#arrow)" />
          <line x1="750" y1="130" x2="850" y2="80" stroke="#3f3f46" strokeWidth="2" markerEnd="url(#arrow)" />
          <line x1="950" y1="80" x2="1050" y2="80" stroke="#3f3f46" strokeWidth="2" markerEnd="url(#arrow)" />
          <line x1="1150" y1="80" x2="1250" y2="80" stroke="#3f3f46" strokeWidth="2" markerEnd="url(#arrow)" />
          <line x1="1350" y1="80" x2="1450" y2="80" stroke="#3f3f46" strokeWidth="2" markerEnd="url(#arrow)" />

          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-auto">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#3f3f46" />
            </marker>
          </defs>

          {/* Nodes */}
          {nodes.map((node) => (
            <g key={node.id} onClick={() => setSelectedNode(node.id)} className="cursor-pointer">
              <rect
                x={node.x}
                y={node.y - 25}
                width={100}
                height={50}
                rx={8}
                className={`${
                  node.status === "completed"
                    ? "fill-emerald-900/30 stroke-emerald-600/50"
                    : node.status === "passed"
                    ? "fill-violet-900/30 stroke-violet-600/50"
                    : "fill-zinc-800 stroke-zinc-700"
                } ${selectedNode === node.id ? "stroke-2" : "stroke-1"}`}
              />
              <text x={node.x + 50} y={node.y - 5} textAnchor="middle" className="fill-zinc-200 text-[11px] font-medium">
                {node.label}
              </text>
              <text x={node.x + 50} y={node.y + 10} textAnchor="middle" className="fill-zinc-500 text-[9px]">
                {node.status}
              </text>
            </g>
          ))}
        </svg>
      </div>

      {/* Node Details Panel */}
      {selectedNode && (
        <div className="h-48 border-t border-zinc-800 bg-zinc-900 p-4 overflow-auto">
          <h3 className="text-sm font-medium mb-2">
            {nodes.find((n) => n.id === selectedNode)?.label}
          </h3>
          {(() => {
            const node = nodes.find((n) => n.id === selectedNode);
            if (!node) return null;
            return (
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <div className="text-zinc-500 mb-1">Inputs</div>
                  {node.inputs.map((inp) => (
                    <div key={inp} className="bg-zinc-800 rounded px-2 py-1 mb-1">{inp}</div>
                  ))}
                </div>
                <div>
                  <div className="text-zinc-500 mb-1">Outputs</div>
                  {node.outputs.map((out) => (
                    <div key={out} className="bg-zinc-800 rounded px-2 py-1 mb-1">{out}</div>
                  ))}
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}
