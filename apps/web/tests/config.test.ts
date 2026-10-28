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
