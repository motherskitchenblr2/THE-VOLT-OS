"use client";

import { useState } from "react";

const fileTree = [
  { name: "src", type: "folder", children: [
    { name: "app", type: "folder", children: [
      { name: "page.tsx", type: "file", lang: "typescript" },
      { name: "layout.tsx", type: "file", lang: "typescript" },
    ]},
    { name: "components", type: "folder", children: [
      { name: "Header.tsx", type: "file", lang: "typescript" },
      { name: "Sidebar.tsx", type: "file", lang: "typescript" },
    ]},
    { name: "lib", type: "folder", children: [
      { name: "api.ts", type: "file", lang: "typescript" },
    ]},
  ]},
  { name: "package.json", type: "file", lang: "json" },
  { name: "tsconfig.json", type: "file", lang: "json" },
  { name: "Dockerfile", type: "file", lang: "dockerfile" },
];

const sampleCode = `import { NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function POST(request: Request) {
  const body = await request.json()

  const order = await prisma.order.create({
    data: {
      restaurantId: body.restaurantId,
      items: body.items,
      status: 'PENDING',
      total: body.total,
    },
  })

  return NextResponse.json(order)
}`;

function FileTreeNode({ node, depth = 0 }: { node: any; depth?: number }) {
  const [open, setOpen] = useState(node.type === "folder");

  return (
    <div>
      <div
        className={`flex items-center gap-1 px-2 py-0.5 text-xs hover:bg-zinc-800 cursor-pointer`}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        onClick={() => node.type === "folder" && setOpen(!open)}
      >
        <span className="text-zinc-500">{node.type === "folder" ? (open ? "▼" : "▶") : "  "}</span>
        <span>{node.type === "folder" ? "📁" : "📄"}</span>
        <span className="text-zinc-300">{node.name}</span>
      </div>
      {open && node.children?.map((child: any) => (
        <FileTreeNode key={child.name} node={child} depth={depth + 1} />
      ))}
    </div>
  );
}

export default function IDE() {
  const [activeFile, setActiveFile] = useState("src/app/page.tsx");

  return (
    <div className="flex flex-col h-full">
      <header className="h-12 border-b border-zinc-800 flex items-center px-4 justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Browser IDE</span>
          <span className="text-xs text-zinc-500">— restaurant-app</span>
        </div>
        <div className="flex gap-2">
          <button className="px-3 py-1 text-xs bg-zinc-800 border border-zinc-700 rounded hover:bg-zinc-700 transition">▶ Run</button>
          <button className="px-3 py-1 text-xs bg-zinc-800 border border-zinc-700 rounded hover:bg-zinc-700 transition">🔍 Preview</button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* File Explorer */}
        <div className="w-56 border-r border-zinc-800 bg-zinc-900 overflow-auto">
          <div className="px-2 py-2 text-[10px] text-zinc-500 uppercase tracking-wider">Explorer</div>
          {fileTree.map((node) => (
            <FileTreeNode key={node.name} node={node} />
          ))}
        </div>

        {/* Editor */}
        <div className="flex-1 flex flex-col">
          {/* Tabs */}
          <div className="h-9 border-b border-zinc-800 flex items-center px-2 gap-1">
            <div className="px-3 py-1 text-xs bg-zinc-800 rounded-t border border-zinc-700 border-b-0 text-zinc-200">
              page.tsx
            </div>
          </div>

          {/* Code Editor */}
          <div className="flex-1 overflow-auto bg-zinc-950 p-4">
            <pre className="text-xs leading-5 font-mono">
              {sampleCode.split("\n").map((line, i) => (
                <div key={i} className="flex">
                  <span className="w-8 text-right pr-4 text-zinc-600 select-none">{i + 1}</span>
                  <span className={
                    line.includes("import") || line.includes("export")
                      ? "text-violet-400"
                      : line.includes("const") || line.includes("await")
                      ? "text-amber-400"
                      : line.includes("//") || line.includes("'")
                      ? "text-emerald-400"
                      : "text-zinc-300"
                  }>
                    {line}
                  </span>
                </div>
              ))}
            </pre>
          </div>

          {/* Terminal */}
          <div className="h-32 border-t border-zinc-800 bg-zinc-900 p-3 overflow-auto">
            <div className="text-[10px] text-zinc-500 uppercase mb-2">Terminal</div>
            <div className="font-mono text-xs space-y-1">
              <div className="text-zinc-500">$ npm run dev</div>
              <div className="text-emerald-400">✓ Ready on http://localhost:3000</div>
              <div className="text-zinc-500">$ npm test</div>
              <div className="text-emerald-400">✓ 42 tests passed</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
