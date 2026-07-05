"use client";

import { useState, type FormEvent } from "react";
import styles from "./page.module.css";
import { splitToListItems } from "@/lib/textUtils";
import type { GeneratedSite, ShopSummary } from "@/types";

type GenerationState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "done"; site: GeneratedSite }
  | { status: "error"; message: string };

type PitchState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "done"; pitch: string }
  | { status: "error"; message: string };

export default function Home() {
  const [region, setRegion] = useState("");
  const [industry, setIndustry] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [shops, setShops] = useState<ShopSummary[]>([]);
  const [generations, setGenerations] = useState<Record<string, GenerationState>>({});
  const [pitches, setPitches] = useState<Record<string, PitchState>>({});

  const handleSearch = async (e: FormEvent) => {
    e.preventDefault();
    setSearching(true);
    setSearchError(null);
    setShops([]);
    setGenerations({});
    setPitches({});

    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ region, industry }),
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error ?? "検索に失敗しました。");
      }

      setShops(data.shops as ShopSummary[]);
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : "検索に失敗しました。");
    } finally {
      setSearching(false);
      setHasSearched(true);
    }
  };

  const handleGenerate = async (shop: ShopSummary) => {
    setGenerations((prev) => ({ ...prev, [shop.placeId]: { status: "loading" } }));

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ shop }),
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error ?? "生成に失敗しました。");
      }

      setGenerations((prev) => ({
        ...prev,
        [shop.placeId]: { status: "done", site: data.site as GeneratedSite },
      }));
    } catch (error) {
      setGenerations((prev) => ({
        ...prev,
        [shop.placeId]: {
          status: "error",
          message: error instanceof Error ? error.message : "生成に失敗しました。",
        },
      }));
    }
  };

  const handleGeneratePitch = async (shop: ShopSummary) => {
    setPitches((prev) => ({ ...prev, [shop.placeId]: { status: "loading" } }));

    try {
      const res = await fetch("/api/sales-pitch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ shop }),
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error ?? "営業文の生成に失敗しました。");
      }

      setPitches((prev) => ({
        ...prev,
        [shop.placeId]: { status: "done", pitch: data.pitch as string },
      }));
    } catch (error) {
      setPitches((prev) => ({
        ...prev,
        [shop.placeId]: {
          status: "error",
          message: error instanceof Error ? error.message : "営業文の生成に失敗しました。",
        },
      }));
    }
  };

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <h1>HPたたき台ジェネレーター</h1>
        <p className={styles.lead}>
          地域と業種を指定して、Googleマップ上で公式ホームページが未設定の可能性がある店舗を検索します（最大10件）。
          店舗ごとにボタンを押すと、AIが1ページホームページ風のプレビューを生成します。
        </p>

        <form className={styles.searchForm} onSubmit={handleSearch}>
          <label className={styles.field}>
            <span>地域</span>
            <input
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              placeholder="例: 広島市"
              required
            />
          </label>
          <label className={styles.field}>
            <span>業種</span>
            <input
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              placeholder="例: 美容室"
              required
            />
          </label>
          <button type="submit" disabled={searching}>
            {searching ? "検索中..." : "検索する"}
          </button>
        </form>

        {searchError && <p className={styles.error}>{searchError}</p>}

        {!searching && hasSearched && !searchError && (
          <p className={styles.resultCount}>
            Googleマップ上で公式ホームページが未設定の可能性がある店舗が {shops.length} 件見つかりました（最大10件表示）。
          </p>
        )}

        <ul className={styles.shopList}>
          {shops.map((shop) => {
            const generation = generations[shop.placeId] ?? { status: "idle" };
            const pitch = pitches[shop.placeId] ?? { status: "idle" };

            return (
              <li key={shop.placeId} className={styles.shopCard}>
                <h2>{shop.name}</h2>
                <dl className={styles.shopMeta}>
                  <dt>住所</dt>
                  <dd>{shop.address || "不明"}</dd>

                  <dt>電話番号</dt>
                  <dd>{shop.phoneNumber ?? "不明"}</dd>

                  <dt>営業時間</dt>
                  <dd>
                    {shop.openingHours ? (
                      <ul className={styles.hoursList}>
                        {shop.openingHours.map((line) => (
                          <li key={line}>{line}</li>
                        ))}
                      </ul>
                    ) : (
                      "不明"
                    )}
                  </dd>

                  <dt>評価</dt>
                  <dd>{shop.rating ?? "不明"}</dd>

                  <dt>Googleマップ</dt>
                  <dd>
                    {shop.mapUrl ? (
                      <>
                        <a href={shop.mapUrl} target="_blank" rel="noopener noreferrer">
                          地図で見る
                        </a>
                        <p className={styles.mapUrlText}>{shop.mapUrl}</p>
                      </>
                    ) : (
                      "不明"
                    )}
                  </dd>
                </dl>

                <button
                  type="button"
                  className={styles.generateButton}
                  onClick={() => handleGenerate(shop)}
                  disabled={generation.status === "loading"}
                >
                  {generation.status === "loading" ? "生成中..." : "HPたたき台を作成"}
                </button>

                {generation.status === "error" && (
                  <p className={styles.error}>{generation.message}</p>
                )}

                {generation.status === "done" && (
                  <>
                    <div className={styles.sitePreview}>
                      <p className={styles.previewLabel}>HPプレビュー</p>

                      <section className={styles.heroSection}>
                        <h3 className={styles.heroCatch}>{generation.site.catchCopy}</h3>
                      </section>

                      <section className={styles.previewSection}>
                        <h4>店舗紹介</h4>
                        <p>{generation.site.introduction}</p>
                      </section>

                      <section className={styles.previewSection}>
                        <h4>選ばれる理由</h4>
                        <ul className={styles.previewList}>
                          {splitToListItems(generation.site.reasons).map((line) => (
                            <li key={line}>{line}</li>
                          ))}
                        </ul>
                      </section>

                      <section className={styles.previewSection}>
                        <h4>サービス内容</h4>
                        <ul className={styles.previewList}>
                          {splitToListItems(generation.site.services).map((line) => (
                            <li key={line}>{line}</li>
                          ))}
                        </ul>
                      </section>

                      <section className={styles.previewSection}>
                        <h4>営業時間</h4>
                        <p>{generation.site.businessHours}</p>
                        {shop.openingHours && (
                          <ul className={styles.hoursList}>
                            {shop.openingHours.map((line) => (
                              <li key={line}>{line}</li>
                            ))}
                          </ul>
                        )}
                      </section>

                      <section className={styles.previewSection}>
                        <h4>アクセス</h4>
                        <p>{generation.site.access}</p>
                        <p className={styles.previewAddress}>{shop.address}</p>
                        {shop.mapUrl && (
                          <>
                            <a href={shop.mapUrl} target="_blank" rel="noopener noreferrer">
                              Googleマップで見る
                            </a>
                            <p className={styles.mapUrlText}>{shop.mapUrl}</p>
                          </>
                        )}
                      </section>

                      <section className={`${styles.previewSection} ${styles.contactSection}`}>
                        <h4>お問い合わせ</h4>
                        <p>{generation.site.contactCta}</p>
                        {shop.phoneNumber && (
                          <a className={styles.telButton} href={`tel:${shop.phoneNumber}`}>
                            {shop.phoneNumber} に電話する
                          </a>
                        )}
                      </section>
                    </div>

                    <button
                      type="button"
                      className={styles.pitchButton}
                      onClick={() => handleGeneratePitch(shop)}
                      disabled={pitch.status === "loading"}
                    >
                      {pitch.status === "loading" ? "作成中..." : "営業文を作成"}
                    </button>

                    {pitch.status === "error" && <p className={styles.error}>{pitch.message}</p>}

                    {pitch.status === "done" && (
                      <article className={styles.pitchBox}>
                        <p className={styles.previewLabel}>営業提案文（下書き）</p>
                        <p className={styles.preLine}>{pitch.pitch}</p>
                      </article>
                    )}
                  </>
                )}
              </li>
            );
          })}
        </ul>
      </main>
    </div>
  );
}
