import type { ReactNode } from "react";

interface StatusPanelProps {
  title: string;
  children: ReactNode;
}

export function StatusPanel({ title, children }: StatusPanelProps) {
  return (
    <section className="status-panel" aria-label={title}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}
