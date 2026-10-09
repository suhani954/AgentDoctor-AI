function normalizeServerDate(value) {
  if (!value || typeof value !== "string") {
    return value;
  }

  const hasTimezone = /([zZ]|[+-]\d{2}:\d{2})$/.test(value);
  return hasTimezone ? value : `${value}Z`;
}

export function formatIndiaDateTime(value, fallback = "Unknown time") {
  if (!value) return fallback;

  const date = new Date(normalizeServerDate(value));

  if (Number.isNaN(date.getTime())) {
    return fallback;
  }

  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "medium",
    timeZone: "Asia/Kolkata",
  }).format(date);
}
