'use client';

import React, { useEffect, useRef, useState } from 'react';

interface MermaidProps {
  chart: string;
}

let mermaidInstance: any = null;

export default function Mermaid({ chart }: MermaidProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [isRendered, setIsRendered] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;

    async function renderChart() {
      try {
        setError(null);
        if (!mermaidInstance) {
          const mermaidModule = await import('mermaid');
          mermaidInstance = mermaidModule.default;
          mermaidInstance.initialize({
            startOnLoad: false,
            theme: 'dark',
            securityLevel: 'strict',
            fontFamily: 'var(--font-sans)',
            themeVariables: {
              darkMode: true,
              background: '#161b22',
              primaryColor: '#1f6feb',
              primaryTextColor: '#c9d1d9',
              primaryBorderColor: '#30363d',
              lineColor: '#58a6ff',
              secondaryColor: '#21262d',
              tertiaryColor: '#0d1117',
            },
          });
        }

        const id = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
        const { svg } = await mermaidInstance.render(id, chart.trim());
        if (isMounted) {
          setSvgContent(svg);
          setIsRendered(true);
        }
      } catch (err: any) {
        if (isMounted) {
          console.warn('Mermaid rendering failed:', err);
          setError(err?.message || 'Failed to render Mermaid diagram.');
        }
      }
    }

    renderChart();

    return () => {
      isMounted = false;
    };
  }, [chart]);

  if (error) {
    return (
      <div className="my-4 p-4 border border-red-500/40 rounded-lg bg-red-950/20 text-sm">
        <div className="flex items-center gap-2 font-medium text-red-400 mb-2">
          <span>⚠️ Diagram Rendering Error</span>
        </div>
        <p className="text-text-muted text-xs mb-3">{error}</p>
        <pre className="p-3 bg-bg-base border border-border-color rounded text-xs overflow-x-auto text-text-main font-mono">
          {chart}
        </pre>
      </div>
    );
  }

  if (!isRendered) {
    return (
      <div className="my-4 p-6 border border-border-color rounded-lg bg-bg-panel text-center text-text-muted text-sm flex items-center justify-center gap-2">
        <span className="inline-block animate-pulse">Rendering diagram...</span>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="my-6 p-4 border border-border-color rounded-lg bg-bg-panel overflow-x-auto flex justify-center"
      dangerouslySetInnerHTML={{ __html: svgContent }}
    />
  );
}
