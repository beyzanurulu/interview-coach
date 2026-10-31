const DEFAULT_API_URL = "http://localhost:8000";

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL;
}

export function getWsUrl(path: string): string {
  return getApiBaseUrl().replace(/\/$/, "").replace(/^http/, "ws") + path;
}
