export interface BarItem {
  label: string;
  value: number;
  detail?: string;
}

interface BarListProps {
  items: BarItem[];
  emptyMessage?: string;
}

export function BarList({
  items,
  emptyMessage = "No ranked values yet.",
}: BarListProps) {
  if (!items.length) {
    return <p className="muted-copy">{emptyMessage}</p>;
  }

  const max = Math.max(...items.map((item) => item.value), 1);

  return (
    <ol className="bar-list">
      {items.map((item) => {
        const width = `${Math.max((item.value / max) * 100, 4)}%`;
        return (
          <li key={`${item.label}-${item.value}`}>
            <div className="bar-row-header">
              <strong>{item.label}</strong>
              <span>{item.value.toLocaleString()}</span>
            </div>
            <div className="bar-track" aria-hidden="true">
              <span style={{ width }} />
            </div>
            {item.detail && <small>{item.detail}</small>}
          </li>
        );
      })}
    </ol>
  );
}
