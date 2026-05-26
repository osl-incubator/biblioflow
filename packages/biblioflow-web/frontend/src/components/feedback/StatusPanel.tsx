import type { ReactNode } from "react";

interface StatusPanelProps {
  title: string;
  children: ReactNode;
  tone?: "default" | "success" | "warning" | "info";
}

export function StatusPanel({
  title,
  children,
  tone = "default",
}: StatusPanelProps) {
  return (
    <section className={`status-panel status-panel-${tone}`} aria-label={title}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}
