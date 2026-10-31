import { afterEach, describe, expect, it } from "vitest";

import { getApiBaseUrl } from "@/lib/config";

describe("getApiBaseUrl", () => {
  const original = process.env.NEXT_PUBLIC_API_URL;
  afterEach(() => {
    process.env.NEXT_PUBLIC_API_URL = original;
  });

  it("falls back to localhost when unset", () => {
    delete process.env.NEXT_PUBLIC_API_URL;
    expect(getApiBaseUrl()).toBe("http://localhost:8000");
  });

  it("uses NEXT_PUBLIC_API_URL when set", () => {
    process.env.NEXT_PUBLIC_API_URL = "https://api.example.com";
    expect(getApiBaseUrl()).toBe("https://api.example.com");
  });
});

describe("getWsUrl", () => {
  it("converts http(s) base URL to ws(s)", async () => {
    const { getWsUrl } = await import("@/lib/config");
    process.env.NEXT_PUBLIC_API_URL = "https://api.example.com/";
    expect(getWsUrl("/ws/interview")).toBe("wss://api.example.com/ws/interview");
    process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000";
    expect(getWsUrl("/ws/interview")).toBe("ws://localhost:8000/ws/interview");
  });
});
