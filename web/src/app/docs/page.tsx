import fs from 'fs';
import path from 'path';
import Link from 'next/link';

export default function DocsIndex() {
  const docsDir = path.join(process.cwd(), 'docs-content');
  const files = fs.existsSync(docsDir) ? fs.readdirSync(docsDir).filter(f => f.endsWith('.md')) : [];
  
  return (
    <div className="p-8 max-w-4xl mx-auto w-full h-full overflow-y-auto">
      <h1 className="text-3xl font-bold mb-6 text-text-main border-b border-border-color pb-2">QVM Documentation</h1>
      <p className="text-text-muted mb-8">Select a document below to read the system architecture and theory.</p>
      
      <div className="grid gap-3">
        {files.sort().map(file => {
          const slug = file.replace('.md', '');
          const title = slug.replace(/^\d+_/, '').replace(/_/g, ' ');
          return (
            <Link key={slug} href={`/docs/${slug}`} className="p-4 border border-border-color rounded bg-bg-panel hover:border-accent transition-colors">
              <span className="font-medium text-accent">{title}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
