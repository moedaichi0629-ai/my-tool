import type { ShopSummary } from "@/types";

const PLACES_API_BASE = "https://maps.googleapis.com/maps/api/place";

interface TextSearchResponse {
  results?: { place_id?: string }[];
  status: string;
  error_message?: string;
  next_page_token?: string;
}

interface PlaceDetailsResponse {
  result?: {
    name?: string;
    formatted_address?: string;
    formatted_phone_number?: string;
    opening_hours?: { weekday_text?: string[] };
    rating?: number;
    url?: string;
    website?: string;
  };
  status: string;
  error_message?: string;
}

// Text Search はステータス OK / ZERO_RESULTS 以外はエラーとして扱う
function assertOkStatus(status: string, errorMessage: string | undefined, context: string) {
  if (status !== "OK" && status !== "ZERO_RESULTS") {
    throw new Error(`${context}: ${status}${errorMessage ? ` (${errorMessage})` : ""}`);
  }
}

export async function searchPlaceIds(query: string, apiKey: string): Promise<string[]> {
  const url = new URL(`${PLACES_API_BASE}/textsearch/json`);
  url.searchParams.set("query", query);
  url.searchParams.set("language", "ja");
  url.searchParams.set("region", "jp");
  url.searchParams.set("key", apiKey);

  const res = await fetch(url.toString());
  const data = (await res.json()) as TextSearchResponse;

  assertOkStatus(data.status, data.error_message, "Google Places Text Search に失敗しました");

  return (data.results ?? [])
    .map((r) => r.place_id)
    .filter((id): id is string => Boolean(id));
}

export async function getPlaceDetails(
  placeId: string,
  apiKey: string
): Promise<ShopSummary | null> {
  const fields = [
    "name",
    "formatted_address",
    "formatted_phone_number",
    "opening_hours",
    "rating",
    "url",
    "website",
  ].join(",");

  const url = new URL(`${PLACES_API_BASE}/details/json`);
  url.searchParams.set("place_id", placeId);
  url.searchParams.set("fields", fields);
  url.searchParams.set("language", "ja");
  url.searchParams.set("key", apiKey);

  const res = await fetch(url.toString());
  const data = (await res.json()) as PlaceDetailsResponse;

  if (data.status !== "OK" || !data.result) {
    return null;
  }

  const result = data.result;

  return {
    placeId,
    name: result.name ?? "名称不明",
    address: result.formatted_address ?? "",
    phoneNumber: result.formatted_phone_number ?? null,
    openingHours: result.opening_hours?.weekday_text ?? null,
    rating: result.rating ?? null,
    mapUrl: result.url ?? null,
    website: result.website ?? null,
  };
}
