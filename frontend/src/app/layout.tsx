import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "VOLT OS — AI Workforce Platform",
  description: "Modular AI Operating System for autonomous software engineering",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-zinc-950 text-zinc-100 antialiased`}>
        <div className="flex h-screen">
          {/* Sidebar */}
          <aside className="w-16 border-r border-zinc-800 flex flex-col items-center py-4 gap-4">
            <div className="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center text-sm font-bold">V</div>
            <nav className="flex flex-col gap-3 mt-4">
              <a href="/" className="w-10 h-10 rounded-lg hover:bg-zinc-800 flex items-center justify-center text-zinc-400 hover:text-zinc-100 transition" title="Workspace">💬</a>
              <a href="/dashboard" className="w-10 h-10 rounded-lg hover:bg-zinc-800 flex items-center justify-center text-zinc-400 hover:text-zinc-100 transition" title="Dashboard">📊</a>
              <a href="/canvas" className="w-10 h-10 rounded-lg hover:bg-zinc-800 flex items-center justify-center text-zinc-400 hover:text-zinc-100 transition" title="Canvas">🔀</a>
              <a href="/ide" className="w-10 h-10 rounded-lg hover:bg-zinc-800 flex items-center justify-center text-zinc-400 hover:text-zinc-100 transition" title="IDE">⌨️</a>
            </nav>
          </aside>

          {/* Main content */}
          <main className="flex-1 overflow-hidden">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
