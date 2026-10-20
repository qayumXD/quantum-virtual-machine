import fs from 'fs';
import path from 'path';
import Link from 'next/link';
import { BookOpen, Cpu, Sparkles, Terminal, Code2, ArrowRight } from 'lucide-react';

interface DocItem {
  slug: string;
  title: string;
  category: string;
  description: string;
}

export default function DocsIndex() {
  const docsDir = path.join(process.cwd(), 'docs-content');
  const files = fs.existsSync(docsDir) ? fs.readdirSync(docsDir).filter(f => f.endsWith('.md')) : [];

  // Group definitions
  const categories: { name: string; icon: any; prefix: string[]; description: string }[] = [
    {
      name: 'System Architecture & Core',
      icon: Cpu,
      prefix: ['000', '100'],
      description: 'High-level overview, architecture diagrams, and design philosophy of QVM.'
    },
    {
      name: 'IR & Transpilation',
      icon: Code2,
      prefix: ['200', '300', '400', '450'],
      description: 'OpenQASM 3 parsing, canonical intermediate representation, and hardware routing.'
    },
    {
      name: 'Simulation & Noise Modeling',
      icon: Terminal,
      prefix: ['500', '550', '600'],
      description: 'Exact statevector evolution, Matrix Product States (MPS), and Kraus noise channels.'
    },
    {
      name: 'Tutorials & Quantum Algorithms',
      icon: Sparkles,
      prefix: ['700', '710', '720', '730', '740', '750'],
      description: 'Step-by-step tutorials from Bell states to Grover search, teleportation, and VQE.'
    },
    {
      name: 'Web API & Integration',
      icon: BookOpen,
      prefix: ['800', '810'],
      description: 'FastAPI REST reference for /run, request schemas, response formats, and web UI.'
    }
  ];

  const docsByPrefix = files.reduce((acc, file) => {
    const slug = file.replace('.md', '');
    const prefixMatch = slug.match(/^(\d+)_/);
    const prefix = prefixMatch ? prefixMatch[1] : '999';
    const title = slug.replace(/^\d+_/, '').replace(/_/g, ' ');
    acc[prefix] = { slug, title, file };
    return acc;
  }, {} as Record<string, { slug: string; title: string; file: string }>);

  return (
    <div className="min-h-full w-full bg-bg-base p-6 md:p-12 overflow-y-auto">
      <div className="max-w-5xl mx-auto space-y-10">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium bg-accent/10 text-accent border border-accent/20 mb-3">
            <span>Documentation &amp; Tutorials</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-text-main tracking-tight">
            Quantum Virtual Machine (QVM) Docs
          </h1>
          <p className="text-text-muted mt-2 text-base max-w-3xl leading-relaxed">
            Welcome to the official technical documentation, architecture guides, REST API reference, and practical quantum algorithm tutorials for the Quantum Virtual Machine.
          </p>
        </div>

        <div className="grid gap-8">
          {categories.map((cat) => {
            const Icon = cat.icon;
            const items = cat.prefix
              .map(p => docsByPrefix[p])
              .filter(Boolean);

            if (items.length === 0) return null;

            return (
              <section key={cat.name} className="border border-border-color rounded-xl bg-bg-panel/40 p-6">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 rounded-lg bg-bg-panel border border-border-color text-accent">
                    <Icon size={20} />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-text-main">{cat.name}</h2>
                    <p className="text-xs text-text-muted">{cat.description}</p>
                  </div>
                </div>

                <div className="grid sm:grid-cols-2 gap-3 mt-4">
                  {items.map(item => (
                    <Link
                      key={item.slug}
                      href={`/docs/${item.slug}`}
                      className="group flex items-center justify-between p-3.5 rounded-lg border border-border-color bg-bg-panel hover:border-accent hover:bg-bg-panel/80 transition-all duration-150"
                    >
                      <span className="font-medium text-sm text-text-main group-hover:text-accent transition-colors">
                        {item.title}
                      </span>
                      <ArrowRight size={16} className="text-text-muted group-hover:text-accent group-hover:translate-x-0.5 transition-all" />
                    </Link>
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      </div>
    </div>
  );
}
