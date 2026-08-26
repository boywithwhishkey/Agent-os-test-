import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return value;
  }
}

export function formatRelativeTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value).getTime();
  if (Number.isNaN(date)) return value;
  const diffSeconds = Math.round((date - Date.now()) / 1000);
  const divisions: [Intl.RelativeTimeFormatUnit, number][] = [
    ["second", 60],
    ["minute", 60],
    ["hour", 24],
    ["day", 7],
    ["week", 4.34],
    ["month", 12],
    ["year", Infinity],
  ];
  let duration = diffSeconds;
  const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });
  for (const [unit, amount] of divisions) {
    if (Math.abs(duration) < amount) return rtf.format(Math.round(duration), unit);
    duration /= amount;
  }
  return rtf.format(Math.round(duration), "year");
}

export function truncate(value: string, length = 80): string {
  return value.length > length ? `${value.slice(0, length)}…` : value;
}
