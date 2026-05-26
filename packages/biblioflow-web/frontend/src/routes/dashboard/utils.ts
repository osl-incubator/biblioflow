import type { BarItem } from "../../components/common/BarList";
import type { BibliographicRecord } from "../../api/types";

export function valueToString(value: unknown): string {
  if (Array.isArray(value)) {
    return value.length ? value.map((item) => String(item)).join("; ") : "—";
  }
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  return String(value);
}

export function valueToNumber(value: unknown): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function firstValue(
  row: Record<string, unknown>,
  keys: string[],
  fallback = "—",
): string {
  for (const key of keys) {
    const value = row[key];
    if (value !== null && value !== undefined && value !== "") {
      return valueToString(value);
    }
  }
  return fallback;
}

export function rowsToBars(
  rows: Record<string, unknown>[] | undefined,
  labelKeys: string[],
  valueKeys: string[],
): BarItem[] {
  return (rows ?? []).map((row) => ({
    label: firstValue(row, labelKeys),
    value: valueToNumber(
      valueKeys.map((key) => row[key]).find((value) => value !== undefined),
    ),
  }));
}

export function formatDate(value: string | undefined | null): string {
  if (!value) {
    return "—";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}

export function summarizeRecord(record: BibliographicRecord): string {
  const title = firstValue(record, [
    "title",
    "document_title",
    "article_title",
  ]);
  const year = firstValue(record, ["publication_year", "year"], "n.d.");
  const source = firstValue(record, [
    "source_title",
    "journal",
    "container_title",
  ]);
  return `${title} (${year}) — ${source}`;
}

export function dynamicColumns(
  rows: Record<string, unknown>[],
  maxColumns = 8,
) {
  const keys = Array.from(
    rows.reduce((accumulator, row) => {
      Object.keys(row).forEach((key) => accumulator.add(key));
      return accumulator;
    }, new Set<string>()),
  ).slice(0, maxColumns);

  return keys.map((key) => ({
    key,
    header: key.replaceAll("_", " "),
  }));
}
