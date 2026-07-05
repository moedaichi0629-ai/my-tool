import { splitToListItems } from "@/lib/textUtils";
import type { GeneratedSite, ShopSummary } from "@/types";

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function listItemsHtml(text: string): string {
  return splitToListItems(text)
    .map((line) => `<li>${escapeHtml(line)}</li>`)
    .join("\n");
}

export function buildStandaloneHtml(shop: ShopSummary, site: GeneratedSite): string {
  const openingHoursHtml = shop.openingHours
    ? `<ul class="hours">${shop.openingHours.map((line) => `<li>${escapeHtml(line)}</li>`).join("")}</ul>`
    : "";

  const mapLinkHtml = shop.mapUrl
    ? `<p><a href="${escapeHtml(shop.mapUrl)}" target="_blank" rel="noopener noreferrer">Googleマップで見る</a></p>`
    : "";

  const telHtml = shop.phoneNumber
    ? `<a class="tel-button" href="tel:${escapeHtml(shop.phoneNumber)}">${escapeHtml(shop.phoneNumber)} に電話する</a>`
    : "";

  return `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${escapeHtml(shop.name)}</title>
<style>
  body { font-family: "Hiragino Sans", "Yu Gothic", sans-serif; margin: 0; color: #1a1a1a; background: #fff; }
  .hero { padding: 60px 20px; background: #eef3fc; text-align: center; }
  .hero h1 { font-size: 28px; line-height: 1.5; color: #1a2b4c; margin: 0; }
  main { max-width: 720px; margin: 0 auto; padding: 0 20px 60px; }
  section { padding: 28px 0; border-top: 1px solid #e2e2e2; }
  section h2 { font-size: 15px; color: #888; letter-spacing: 0.03em; margin: 0 0 12px; }
  ul { padding-left: 20px; margin: 0; }
  li { margin-bottom: 6px; }
  .hours { list-style: none; padding-left: 0; color: #555; }
  .contact { background: #f7f8fa; }
  .tel-button { display: inline-block; margin-top: 12px; padding: 12px 24px; border-radius: 8px; background: #1a9e5c; color: #fff; font-weight: 700; text-decoration: none; }
  a { color: #2d6cdf; }
</style>
</head>
<body>
  <div class="hero">
    <h1>${escapeHtml(site.catchCopy)}</h1>
  </div>
  <main>
    <section>
      <h2>店舗紹介</h2>
      <p>${escapeHtml(site.introduction)}</p>
    </section>
    <section>
      <h2>選ばれる理由</h2>
      <ul>${listItemsHtml(site.reasons)}</ul>
    </section>
    <section>
      <h2>サービス内容</h2>
      <ul>${listItemsHtml(site.services)}</ul>
    </section>
    <section>
      <h2>営業時間</h2>
      <p>${escapeHtml(site.businessHours)}</p>
      ${openingHoursHtml}
    </section>
    <section>
      <h2>アクセス</h2>
      <p>${escapeHtml(site.access)}</p>
      <p>${escapeHtml(shop.address)}</p>
      ${mapLinkHtml}
    </section>
    <section class="contact">
      <h2>お問い合わせ</h2>
      <p>${escapeHtml(site.contactCta)}</p>
      ${telHtml}
    </section>
  </main>
</body>
</html>
`;
}
