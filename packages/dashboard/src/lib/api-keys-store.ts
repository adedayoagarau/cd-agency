const STORAGE_KEY = "cd-agency-api-keys";

export interface StoredKeys {
  anthropic?: string;
  openai?: string;
  openrouter?: string;
}

export function getStoredKeys(): StoredKeys {
  if (typeof window === "undefined") return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

export function setStoredKeys(keys: Partial<StoredKeys>): void {
  if (typeof window === "undefined") return;
  const existing = getStoredKeys();
  const merged = { ...existing, ...keys };
  Object.keys(merged).forEach((k) => {
    if (!merged[k as keyof StoredKeys]) delete merged[k as keyof StoredKeys];
  });
  localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
}

export function removeStoredKey(provider: keyof StoredKeys): void {
  const keys = getStoredKeys();
  delete keys[provider];
  localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));
}

export function hasAnthropicKey(): boolean {
  return !!getStoredKeys().anthropic;
}

export function maskKey(key: string): string {
  if (key.length <= 10) return "••••••••";
  return key.slice(0, 6) + "••••" + key.slice(-4);
}
