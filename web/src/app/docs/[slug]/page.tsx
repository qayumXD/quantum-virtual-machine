import fs from 'fs';
import path from 'path';
import ReactMarkdown from 'react-markdown';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

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
  let content = "Documentation file not found.";
  
  if (fs.existsSync(filePath)) {
    content = fs.readFileSync(filePath, 'utf8');
  }

  return (
    <div className="flex flex-col h-full w-full">
      <div className="h-12 border-b border-border-color bg-bg-panel flex items-center px-4 shrink-0">
        <Link href="/docs" className="text-text-muted hover:text-text-main flex items-center gap-1 text-sm font-medium transition-colors">
          <ArrowLeft size={16} /> Back to Docs Index
        </Link>
      </div>
      <div className="flex-1 overflow-y-auto p-8">
        <div className="prose">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
