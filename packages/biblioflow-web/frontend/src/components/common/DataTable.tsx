import type { ReactNode } from "react";

export interface DataTableColumn<T extends object> {
  key: string;
  header: string;
  render?: (row: T) => ReactNode;
}

interface DataTableProps<T extends object> {
  rows: T[];
  columns: DataTableColumn<T>[];
  emptyMessage?: string;
  caption?: string;
}

function formatCell(value: unknown): string {
  if (Array.isArray(value)) {
    return value.length ? value.map((item) => String(item)).join("; ") : "—";
  }
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function cellValue<T extends object>(row: T, key: string): unknown {
  return (row as Record<string, unknown>)[key];
}

export function DataTable<T extends object>({
  rows,
  columns,
  emptyMessage = "No rows to display.",
  caption,
}: DataTableProps<T>) {
  if (!rows.length) {
    return <p className="muted-copy">{emptyMessage}</p>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        {caption && <caption>{caption}</caption>}
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr
              key={String(
                cellValue(row, "id") ??
                  cellValue(row, "dataset_id") ??
                  cellValue(row, "upload_id") ??
                  rowIndex,
              )}
            >
              {columns.map((column) => (
                <td key={column.key}>
                  {column.render
                    ? column.render(row)
                    : formatCell(cellValue(row, column.key))}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
