export interface BarItem {
  label: string;
  value: number;
  detail?: string;
}

interface BarListProps {
  items: BarItem[];
  countLabel?: string;
  emptyMessage?: string;
  note?: string;
}

function countText(value: number, label?: string): string {
  const formattedValue = value.toLocaleString();
  if (!label) {
    return formattedValue;
  }
  const suffix =
    value === 1 || label.endsWith("s") || label.endsWith(".")
      ? label
      : `${label}s`;
  return `${formattedValue} ${suffix}`;
}

export function BarList({
  items,
  countLabel,
  emptyMessage = "No ranked values yet.",
  note,
}: BarListProps) {
  if (!items.length) {
    return <p className="muted-copy">{emptyMessage}</p>;
  }

  const max = Math.max(...items.map((item) => item.value), 1);

  return (
    <>
      {note && <p className="bar-list-note">{note}</p>}
      <ol className="bar-list">
        {items.map((item) => {
          const width = `${Math.max((item.value / max) * 100, 4)}%`;
          const valueText = countText(item.value, countLabel);
          return (
            <li key={`${item.label}-${item.value}`}>
              <div className="bar-row-header">
                <strong>{item.label}</strong>
                <span aria-label={valueText} title={valueText}>
                  {valueText}
                </span>
              </div>
              <div className="bar-track" aria-hidden="true">
                <span style={{ width }} />
              </div>
              {item.detail && <small>{item.detail}</small>}
            </li>
          );
        })}
      </ol>
    </>
  );
}
