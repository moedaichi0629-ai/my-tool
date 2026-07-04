import { NextResponse } from "next/server";
import { generateSiteCopy } from "@/lib/openaiClient";
import { describeFetchError } from "@/lib/errorUtils";
import type { ShopSummary } from "@/types";

function isValidShop(value: unknown): value is ShopSummary {
  if (!value || typeof value !== "object") return false;
  const shop = value as Record<string, unknown>;
  return typeof shop.placeId === "string" && typeof shop.name === "string";
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const shop = body?.shop;

  if (!isValidShop(shop)) {
    return NextResponse.json({ error: "店舗情報が不正です。" }, { status: 400 });
  }

  try {
    const site = await generateSiteCopy(shop);
    return NextResponse.json({ site });
  } catch (error) {
    console.error(error);
    return NextResponse.json({ error: describeFetchError(error, "生成") }, { status: 500 });
  }
}
