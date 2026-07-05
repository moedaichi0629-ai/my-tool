// Googleビジネスプロフィールの「ウェブサイト」欄には、予約サイトやSNSのリンクが
// 登録されているケースが多い。これらは店舗独自の公式サイトとは言えないため、
// 既知のドメインに一致する場合は「公式サイトなし」として扱う。
const NON_OFFICIAL_DOMAINS = [
  "hotpepper.jp",
  "beauty.hotpepper.jp",
  "tabelog.com",
  "gnavi.co.jp",
  "r.gnavi.co.jp",
  "retty.me",
  "epark.jp",
  "instagram.com",
  "facebook.com",
  "fb.com",
  "twitter.com",
  "x.com",
  "line.me",
  "lin.ee",
  "linktr.ee",
  "g.page",
  "goo.gl",
  "maps.app.goo.gl",
];

export function isOfficialWebsite(url: string | null): boolean {
  if (!url) return false;

  let hostname: string;
  try {
    hostname = new URL(url).hostname.replace(/^www\./, "");
  } catch {
    // URLとして解析できない場合は、誤って「公式サイトなし」と扱わないよう保守的に判定する
    return true;
  }

  return !NON_OFFICIAL_DOMAINS.some(
    (domain) => hostname === domain || hostname.endsWith(`.${domain}`)
  );
}
