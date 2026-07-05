const SEARCH_HISTORY_KEY = "hp-tataki:search-history";
const GENERATION_HISTORY_KEY = "hp-tataki:generation-history";
const MAX_HISTORY_ITEMS = 30;

export interface SearchHistoryEntry {
  id: string;
  region: string;
  industry: string;
  resultCount: number;
}

export interface GeneratedSiteContent {
  catchCopy: string;
  introduction: string;
  reasons: string;
  services: string;
  businessHours: string;
  access: string;
  contactCta: string;
}

export type GenerationHistoryEntry =
  | {
      id: string;
      placeId: string;
      shopName: string;
      region: string;
      industry: string;
      type: "site";
      site: GeneratedSiteContent;
    }
  | {
      id: string;
      placeId: string;
      shopName: string;
      region: string;
      industry: string;
      type: "pitch";
      pitch: string;
    };

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

function dedupeByKey<T>(list: T[], keyOf: (item: T) => string): T[] {
  const seen = new Set<string>();
  const result: T[] = [];
  for (const item of list) {
    const key = keyOf(item);
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(item);
  }
  return result;
}

const searchHistoryKey = (entry: Pick<SearchHistoryEntry, "region" | "industry">) =>
  `${entry.region}|${entry.industry}`;

const generationHistoryKey = (entry: Pick<GenerationHistoryEntry, "placeId" | "type">) =>
  `${entry.placeId}|${entry.type}`;

export function getSearchHistory(): SearchHistoryEntry[] {
  const list = readList<SearchHistoryEntry>(SEARCH_HISTORY_KEY);
  const deduped = dedupeByKey(list, searchHistoryKey);
  return deduped.length === list.length ? deduped : writeList(SEARCH_HISTORY_KEY, deduped);
}

export function addSearchHistory(
  entry: Omit<SearchHistoryEntry, "id">
): SearchHistoryEntry[] {
  const newEntry: SearchHistoryEntry = { ...entry, id: createId() };
  const rest = getSearchHistory().filter(
    (item) => searchHistoryKey(item) !== searchHistoryKey(entry)
  );
  return writeList(SEARCH_HISTORY_KEY, [newEntry, ...rest]);
}

function isValidGenerationEntry(entry: GenerationHistoryEntry): boolean {
  if (entry.type === "site") return typeof entry.site === "object" && entry.site !== null;
  if (entry.type === "pitch") return typeof entry.pitch === "string";
  return false;
}

export function getGenerationHistory(): GenerationHistoryEntry[] {
  const raw = readList<GenerationHistoryEntry>(GENERATION_HISTORY_KEY);
  const deduped = dedupeByKey(raw.filter(isValidGenerationEntry), generationHistoryKey);
  return deduped.length === raw.length ? deduped : writeList(GENERATION_HISTORY_KEY, deduped);
}

export function addGenerationHistory(
  entry:
    | Omit<Extract<GenerationHistoryEntry, { type: "site" }>, "id">
    | Omit<Extract<GenerationHistoryEntry, { type: "pitch" }>, "id">
): GenerationHistoryEntry[] {
  const newEntry = { ...entry, id: createId() } as GenerationHistoryEntry;
  const rest = getGenerationHistory().filter(
    (item) => generationHistoryKey(item) !== generationHistoryKey(entry)
  );
  return writeList(GENERATION_HISTORY_KEY, [newEntry, ...rest]);
}
