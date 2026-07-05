import { NextResponse } from "next/server";
import { saveShopToSheet } from "@/lib/googleSheets";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const shopName = body?.shopName;
  const mapUrl = body?.mapUrl ?? null;
  const region = body?.region;
  const industry = body?.industry;

  if (typeof shopName !== "string" || typeof region !== "string" || typeof industry !== "string") {
    return NextResponse.json({ error: "保存に必要な情報が不足しています。" }, { status: 400 });
  }

  try {
    await saveShopToSheet({ shopName, mapUrl, region, industry });
    return NextResponse.json({ ok: true });
  } catch (error) {
    console.error(error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "スプレッドシートへの保存に失敗しました。" },
      { status: 500 }
    );
  }
}
