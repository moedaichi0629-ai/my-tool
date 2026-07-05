const SEARCH_HISTORY_KEY = "hp-tataki:search-history";
const GENERATION_HISTORY_KEY = "hp-tataki:generation-history";
const MAX_HISTORY_ITEMS = 30;

export interface SearchHistoryEntry {
  id: string;
  region: string;
  industry: string;
  resultCount: number;
}

export interface GenerationHistoryEntry {
  id: string;
  placeId: string;
  shopName: string;
  region: string;
  industry: string;
  type: "site" | "pitch";
}

function readList<T>(key: string): T[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T[]) : [];
  } catch {
    return [];
  }
}

function writeList<T>(key: string, list: T[]): T[] {
  const trimmed = list.slice(0, MAX_HISTORY_ITEMS);
  window.localStorage.setItem(key, JSON.stringify(trimmed));
  return trimmed;
}

function createId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function getSearchHistory(): SearchHistoryEntry[] {
  return readList<SearchHistoryEntry>(SEARCH_HISTORY_KEY);
}

export function addSearchHistory(
  entry: Omit<SearchHistoryEntry, "id">
): SearchHistoryEntry[] {
  const newEntry: SearchHistoryEntry = { ...entry, id: createId() };
  const rest = readList<SearchHistoryEntry>(SEARCH_HISTORY_KEY).filter(
    (item) => !(item.region === entry.region && item.industry === entry.industry)
  );
  return writeList(SEARCH_HISTORY_KEY, [newEntry, ...rest]);
}

export function getGenerationHistory(): GenerationHistoryEntry[] {
  return readList<GenerationHistoryEntry>(GENERATION_HISTORY_KEY);
}

export function addGenerationHistory(
  entry: Omit<GenerationHistoryEntry, "id">
): GenerationHistoryEntry[] {
  const newEntry: GenerationHistoryEntry = { ...entry, id: createId() };
  const rest = readList<GenerationHistoryEntry>(GENERATION_HISTORY_KEY).filter(
    (item) => !(item.placeId === entry.placeId && item.type === entry.type)
  );
  return writeList(GENERATION_HISTORY_KEY, [newEntry, ...rest]);
}
