import { NextResponse } from "next/server";
import { getPlaceDetails, searchPlaceIds } from "@/lib/googlePlaces";
import { describeFetchError } from "@/lib/errorUtils";

const MAX_RESULTS = 10;

export async function POST(request: Request) {
  const apiKey = process.env.GOOGLE_PLACES_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { error: "GOOGLE_PLACES_API_KEYが設定されていません。.env.localを確認してください。" },
      { status: 500 }
    );
  }

  const body = await request.json().catch(() => null);
  const region = typeof body?.region === "string" ? body.region.trim() : "";
  const industry = typeof body?.industry === "string" ? body.industry.trim() : "";

  if (!region || !industry) {
    return NextResponse.json({ error: "地域と業種を入力してください。" }, { status: 400 });
  }

  try {
    const query = `${industry} ${region}`;
    const placeIds = await searchPlaceIds(query, apiKey);

    const details = await Promise.all(placeIds.map((id) => getPlaceDetails(id, apiKey)));

    const shopsWithoutWebsite = details.filter(
      (shop): shop is NonNullable<typeof shop> => shop !== null && !shop.website
    );

    return NextResponse.json({ shops: shopsWithoutWebsite.slice(0, MAX_RESULTS) });
  } catch (error) {
    console.error(error);
    return NextResponse.json({ error: describeFetchError(error, "検索") }, { status: 500 });
  }
}
