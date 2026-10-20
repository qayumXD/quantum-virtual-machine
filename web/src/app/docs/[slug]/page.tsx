import fs from 'fs';
import path from 'path';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import Link from 'next/link';
import { ArrowLeft, BookOpen, ExternalLink } from 'lucide-react';
import 'katex/dist/katex.min.css';
import CodeBlock from '../components/CodeBlock';

// Required for Static Export to know which pages to generate
export async function generateStaticParams() {
  const docsDir = path.join(process.cwd(), 'docs-content');
  if (!fs.existsSync(docsDir)) return [];
  const files = fs.readdirSync(docsDir).filter(f => f.endsWith('.md'));
  return files.map(file => ({
    slug: file.replace('.md', ''),
  }));
}

export default async function DocPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const filePath = path.join(process.cwd(), 'docs-content', `${slug}.md`);
  let content = "# Document Not Found\n\nThe requested documentation article could not be located.";
  
  if (fs.existsSync(filePath)) {
    content = fs.readFileSync(filePath, 'utf8');
  }

  const cleanTitle = slug.replace(/^\d+_/, '').replace(/_/g, ' ');

  return (
    <div className="flex flex-col h-full w-full bg-bg-base">
      <header className="h-14 border-b border-border-color bg-bg-panel/90 backdrop-blur sticky top-0 z-10 flex items-center justify-between px-6 shrink-0">
        <div className="flex items-center gap-3">
          <Link
            href="/docs"
            className="text-text-muted hover:text-text-main flex items-center gap-1.5 text-sm font-medium transition-colors"
          >
            <ArrowLeft size={16} />
            <span>Docs</span>
          </Link>
          <span className="text-border-color">/</span>
          <span className="text-sm font-semibold text-text-main truncate max-w-xs md:max-w-md">
            {cleanTitle}
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs text-text-muted">
          <Link
            href="/"
            className="hidden sm:flex items-center gap-1 hover:text-accent transition-colors"
          >
            <span>QVM Dashboard</span>
            <ExternalLink size={12} />
          </Link>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-4 py-8 sm:px-8 md:px-12">
        <article className="prose">
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[rehypeKatex]}
            components={{
              code({ node, inline, className, children, ...props }: any) {
                return (
                  <CodeBlock inline={inline} className={className}>
                    {children}
                  </CodeBlock>
                );
              },
              table({ children }: any) {
                return (
                  <div className="table-container">
                    <table>{children}</table>
                  </div>
                );
              },
              a({ node, href, children, ...props }: any) {
                const isExternal = href?.startsWith('http://') || href?.startsWith('https://');
                return (
                  <a
                    href={href}
                    target={isExternal ? '_blank' : undefined}
                    rel={isExternal ? 'noopener noreferrer' : undefined}
                    className="text-accent hover:text-accent-hover underline inline-flex items-center gap-0.5"
                    {...props}
                  >
                    <span>{children}</span>
                    {isExternal && <ExternalLink size={12} className="inline ml-0.5 opacity-80" />}
                  </a>
                );
              },
              blockquote({ children }: any) {
                return (
                  <blockquote className="border-l-4 border-accent pl-4 py-1 italic text-text-muted my-4 bg-bg-panel/40 rounded-r">
                    {children}
                  </blockquote>
                );
              }
            }}
          >
            {content}
          </ReactMarkdown>
        </article>
      </main>
    </div>
  );
}
