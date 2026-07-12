import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { Book, Code2 } from "lucide-react";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains-mono" });

export const metadata: Metadata = {
  title: "QVM Simulator",
  description: "Educational Quantum Virtual Machine",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="dark">
      <body className={`${inter.variable} ${jetbrainsMono.variable} antialiased flex flex-col h-screen overflow-hidden`}>
        
        {/* Global Header */}
        <header className="h-12 bg-bg-panel border-b border-border-color flex items-center justify-between px-4 shrink-0">
          <div className="flex items-center gap-6">
            <div className="font-semibold text-[15px] flex items-center gap-2">
              <Code2 size={18} className="text-accent" />
              <span>QVM v0.4.0</span>
            </div>
            <nav className="flex items-center gap-4 text-sm font-medium">
              <Link href="/" className="text-text-muted hover:text-text-main transition-colors">Workspace</Link>
              <Link href="/history" className="text-text-muted hover:text-text-main transition-colors">History</Link>
              <Link href="/docs" className="text-text-muted hover:text-text-main transition-colors flex items-center gap-1.5">
                <Book size={14} /> Documentation
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <a href="https://github.com/qayumXD/quantum-virtual-machine" target="_blank" rel="noreferrer" className="text-text-muted hover:text-text-main transition-colors font-mono text-sm">
              [GitHub]
            </a>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 overflow-hidden flex">
          {children}
        </main>

        {/* Global Footer */}
        <footer className="h-8 bg-bg-panel border-t border-border-color flex items-center justify-between px-4 text-xs text-text-muted shrink-0">
          <div className="flex gap-4">
            <span>Status: Operational</span>
            <span>API: render.com</span>
          </div>
          <div>
            &copy; {new Date().getFullYear()} QVM Project. All rights reserved.
          </div>
        </footer>

      </body>
    </html>
  );
}
