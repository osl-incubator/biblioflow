import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  children?: ReactNode;
  action?: ReactNode;
  icon?: string;
}

export function EmptyState({
  title,
  children,
  action,
  icon = "⌁",
}: EmptyStateProps) {
  return (
    <div className="empty-state">
      <span className="empty-state-icon" aria-hidden="true">
        {icon}
      </span>
      <div>
        <h2>{title}</h2>
        {children && <div className="empty-state-copy">{children}</div>}
        {action && <div className="empty-state-action">{action}</div>}
      </div>
    </div>
  );
}
