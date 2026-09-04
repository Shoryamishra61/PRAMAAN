const timestampFormatter = new Intl.DateTimeFormat("en-IN", {
  dateStyle: "medium",
  timeStyle: "short",
});

export function formatMoney(
  amountMinor: number | null,
  currency = "INR",
  empty = "No record",
): string {
  if (amountMinor === null) return empty;
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amountMinor / 100);
}

export function formatTimestamp(value: string | null): string {
  if (!value) return "Not available";
  const timestamp = new Date(value);
  return Number.isNaN(timestamp.getTime())
    ? "Invalid timestamp"
    : timestampFormatter.format(timestamp);
}

export function humanizeToken(value: string | null, empty = "None"): string {
  if (!value) return empty;
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}
