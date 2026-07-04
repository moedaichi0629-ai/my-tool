import OpenAI from "openai";
import type { GeneratedSite, ShopSummary } from "@/types";

const SYSTEM_PROMPT = `あなたはプロのウェブコピーライターです。渡された店舗情報をもとに、1ページ完結型ホームページの「たたき台」となる文章を日本語で作成してください。

制約:
- Googleの口コミ文や写真の説明をそのまま転載・要約引用しない。店舗情報（店名・住所・営業時間・評価点など）を参考に、あくまで独自の文章として書き起こすこと。
- 実在しない実績・資格・受賞歴などを断定的に書かない。
- 出力は必ず指定のJSON形式のみで返すこと。前後に説明文やMarkdownの装飾を付けないこと。`;

function buildUserPrompt(shop: ShopSummary): string {
  return `以下の店舗情報をもとに、1ページホームページのたたき台を作成してください。

店舗名: ${shop.name}
住所: ${shop.address || "不明"}
電話番号: ${shop.phoneNumber ?? "不明"}
営業時間: ${shop.openingHours?.join(" / ") ?? "不明"}
Google評価: ${shop.rating ?? "不明"}

次のJSON形式で出力してください（キー名は必ずそのまま使うこと）:
{
  "catchCopy": "キャッチコピー（1〜2文）",
  "introduction": "店舗紹介文（3〜5文程度）",
  "reasons": "選ばれる理由。改行区切りで3項目程度",
  "services": "想定されるサービス内容。改行区切りで3〜5項目程度",
  "businessHours": "営業時間の案内文",
  "access": "住所をもとにしたアクセス案内文",
  "contactCta": "予約・お問い合わせを促す文章"
}`;
}

function getClient(): OpenAI {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error("OPENAI_API_KEYが設定されていません。.env.localを確認してください。");
  }
  return new OpenAI({ apiKey });
}

function getModel(): string {
  return process.env.OPENAI_MODEL || "gpt-4o-mini";
}

export async function generateSiteCopy(shop: ShopSummary): Promise<GeneratedSite> {
  const client = getClient();

  const completion = await client.chat.completions.create({
    model: getModel(),
    messages: [
      { role: "system", content: SYSTEM_PROMPT },
      { role: "user", content: buildUserPrompt(shop) },
    ],
    response_format: { type: "json_object" },
    temperature: 0.7,
  });

  const content = completion.choices[0]?.message?.content;
  if (!content) {
    throw new Error("OpenAIからの応答が空でした。");
  }

  return JSON.parse(content) as GeneratedSite;
}

const SALES_PITCH_SYSTEM_PROMPT = `あなたは、Web制作の提案を行う営業担当者向けに、店舗オーナーへ送る提案文の下書きを作成するアシスタントです。

制約:
- 「ホームページがない」「HPを持っていない」のように断定しない。必ず「Googleマップ上で公式ホームページが未設定の可能性が見受けられました」のような、可能性・推測の表現にとどめること。
- 上から目線や決めつけ、不安を煽るような表現を避け、丁寧で失礼のない言葉遣いにすること。
- Googleの口コミ文や写真の内容をそのまま引用しない。
- 実在しない実績・取引実績・料金・キャンペーンなどを断定的に書かない。
- 送り主の会社名や氏名は決め打ちせず、「[会社名]」「[担当者名]」のようなプレースホルダーのままにすること。
- 出力はプレーンテキストの提案文のみ。JSON形式にしない。前後に説明文を付けない。`;

function buildSalesPitchPrompt(shop: ShopSummary): string {
  return `以下の店舗に向けて、Webサイト制作のご提案メールの下書きを日本語で作成してください。

店舗名: ${shop.name}
住所: ${shop.address || "不明"}
業種の手がかりになりそうな情報: 店舗名や住所から推測できる範囲で構いません

構成の目安:
1. 挨拶と名乗り（プレースホルダー使用）
2. Googleマップを拝見した旨と、公式ホームページが未設定の可能性がある点への言及（断定しない）
3. ホームページを持つことで期待できるメリットを簡潔に
4. 簡単な打ち合わせ・返信を促す一文
5. 結びの挨拶（プレースホルダー使用）

400文字程度で、丁寧だが堅苦しすぎない文章にしてください。`;
}

export async function generateSalesPitch(shop: ShopSummary): Promise<string> {
  const client = getClient();

  const completion = await client.chat.completions.create({
    model: getModel(),
    messages: [
      { role: "system", content: SALES_PITCH_SYSTEM_PROMPT },
      { role: "user", content: buildSalesPitchPrompt(shop) },
    ],
    temperature: 0.7,
  });

  const content = completion.choices[0]?.message?.content;
  if (!content) {
    throw new Error("OpenAIからの応答が空でした。");
  }

  return content.trim();
}
