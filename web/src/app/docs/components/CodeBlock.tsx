'use client';

import React, { useState } from 'react';
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';
import bash from 'highlight.js/lib/languages/bash';
import json from 'highlight.js/lib/languages/json';
import yaml from 'highlight.js/lib/languages/yaml';
import markdown from 'highlight.js/lib/languages/markdown';
import typescript from 'highlight.js/lib/languages/typescript';
import javascript from 'highlight.js/lib/languages/javascript';
import Mermaid from './Mermaid';
import { Check, Copy } from 'lucide-react';

// Register key languages
hljs.registerLanguage('python', python);
hljs.registerLanguage('py', python);
hljs.registerLanguage('bash', bash);
hljs.registerLanguage('sh', bash);
hljs.registerLanguage('shell', bash);
hljs.registerLanguage('json', json);
hljs.registerLanguage('yaml', yaml);
hljs.registerLanguage('yml', yaml);
hljs.registerLanguage('markdown', markdown);
hljs.registerLanguage('md', markdown);
hljs.registerLanguage('typescript', typescript);
hljs.registerLanguage('ts', typescript);
hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('js', javascript);

// Basic QASM highlighter configuration (using Python/C-like syntax tokens)
hljs.registerLanguage('qasm', (hljsInstance) => ({
  name: 'OpenQASM',
  keywords: {
    keyword: 'OPENQASM include qreg creg qubit bit gate defcal measure reset barrier if else while for in return',
    type: 'qubit bit angle duration stretch int uint float bool complex',
    literal: 'pi true false',
    built_in: 'h x y z s sdg t tdg sx sxdg id rx ry rz p rxx rzz cp swap cx cz ccx mcx'
  },
  contains: [
    hljsInstance.C_LINE_COMMENT_MODE,
    hljsInstance.C_BLOCK_COMMENT_MODE,
    hljsInstance.QUOTE_STRING_MODE,
    hljsInstance.NUMBER_MODE,
  ]
}));

interface CodeBlockProps {
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
}

export default function CodeBlock({ inline, className, children }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1].toLowerCase() : '';
  const rawCode = String(children || '').replace(/\n$/, '');

  if (inline) {
    return (
      <code className="bg-bg-panel px-1.5 py-0.5 rounded font-mono text-sm border border-border-color text-accent">
        {children}
      </code>
    );
  }

  if (language === 'mermaid') {
    return <Mermaid chart={rawCode} />;
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(rawCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code: ', err);
    }
  };

  let highlightedHtml: string = '';
  try {
    if (language && hljs.getLanguage(language)) {
      highlightedHtml = hljs.highlight(rawCode, { language, ignoreIllegals: true }).value;
    } else {
      highlightedHtml = hljs.highlightAuto(rawCode).value;
    }
  } catch {
    highlightedHtml = '';
  }

  return (
    <div className="relative my-4 rounded-lg border border-border-color bg-code-bg overflow-hidden group">
      <div className="flex items-center justify-between px-4 py-1.5 bg-bg-panel/70 border-b border-border-color text-xs font-mono text-text-muted select-none">
        <span className="uppercase tracking-wider font-semibold">{language || 'text'}</span>
        <button
          onClick={handleCopy}
          aria-label="Copy code to clipboard"
          className="flex items-center gap-1.5 py-1 px-2 rounded hover:bg-border-color/60 text-text-muted hover:text-text-main transition-colors cursor-pointer"
        >
          {copied ? (
            <>
              <Check size={14} className="text-green-400" />
              <span className="text-green-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy size={14} />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-4 overflow-x-auto text-sm font-mono leading-relaxed text-text-main">
        {highlightedHtml ? (
          <code dangerouslySetInnerHTML={{ __html: highlightedHtml }} />
        ) : (
          <code>{rawCode}</code>
        )}
      </pre>
    </div>
  );
}
