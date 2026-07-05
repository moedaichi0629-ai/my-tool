"use client";

import { useEffect, useState, type FormEvent } from "react";
import styles from "./page.module.css";
import { splitToListItems } from "@/lib/textUtils";
import { buildStandaloneHtml } from "@/lib/exportHtml";
import {
  addGenerationHistory,
  addSearchHistory,
  getGenerationHistory,
  getSearchHistory,
  type GenerationHistoryEntry,
  type SearchHistoryEntry,
} from "@/lib/history";
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

type SheetSaveState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "done" }
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
  const [sheetSaves, setSheetSaves] = useState<Record<string, SheetSaveState>>({});
  const [searchHistory, setSearchHistory] = useState<SearchHistoryEntry[]>([]);
  const [generationHistory, setGenerationHistory] = useState<GenerationHistoryEntry[]>([]);

  useEffect(() => {
    setSearchHistory(getSearchHistory());
    setGenerationHistory(getGenerationHistory());
  }, []);

  const handleSearch = async (e: FormEvent) => {
    e.preventDefault();
    setSearching(true);
    setSearchError(null);
    setShops([]);
    setGenerations({});
    setPitches({});
    setSheetSaves({});

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

      const foundShops = data.shops as ShopSummary[];
      setShops(foundShops);
      setSearchHistory(
        addSearchHistory({ region, industry, resultCount: foundShops.length })
      );
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
      setGenerationHistory(
        addGenerationHistory({
          placeId: shop.placeId,
          shopName: shop.name,
          region,
          industry,
          type: "site",
        })
      );
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
      setGenerationHistory(
        addGenerationHistory({
          placeId: shop.placeId,
          shopName: shop.name,
          region,
          industry,
          type: "pitch",
        })
      );
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

  const handleSaveToSheet = async (shop: ShopSummary) => {
    setSheetSaves((prev) => ({ ...prev, [shop.placeId]: { status: "loading" } }));

    try {
      const res = await fetch("/api/save-to-sheet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ shopName: shop.name, mapUrl: shop.mapUrl, region, industry }),
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error ?? "スプレッドシートへの保存に失敗しました。");
      }

      setSheetSaves((prev) => ({ ...prev, [shop.placeId]: { status: "done" } }));
    } catch (error) {
      setSheetSaves((prev) => ({
        ...prev,
        [shop.placeId]: {
          status: "error",
          message: error instanceof Error ? error.message : "スプレッドシートへの保存に失敗しました。",
        },
      }));
    }
  };

  const handleDownloadHtml = (shop: ShopSummary, site: GeneratedSite) => {
    const html = buildStandaloneHtml(shop, site);
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${shop.name}-hp.html`;
    link.click();
    URL.revokeObjectURL(url);
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
            const sheetSave = sheetSaves[shop.placeId] ?? { status: "idle" };

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

                <div className={styles.actionRow}>
                  <button
                    type="button"
                    className={styles.generateButton}
                    onClick={() => handleGenerate(shop)}
                    disabled={generation.status === "loading"}
                  >
                    {generation.status === "loading" ? "生成中..." : "HPたたき台を作成"}
                  </button>

                  <button
                    type="button"
                    className={styles.sheetButton}
                    onClick={() => handleSaveToSheet(shop)}
                    disabled={sheetSave.status === "loading"}
                  >
                    {sheetSave.status === "loading" ? "保存中..." : "スプレッドシートに保存"}
                  </button>
                </div>

                {sheetSave.status === "error" && <p className={styles.error}>{sheetSave.message}</p>}
                {sheetSave.status === "done" && (
                  <p className={styles.sheetSavedNote}>スプレッドシートに保存しました。</p>
                )}

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

                    <div className={styles.actionRow}>
                      <button
                        type="button"
                        className={styles.pitchButton}
                        onClick={() => handleGeneratePitch(shop)}
                        disabled={pitch.status === "loading"}
                      >
                        {pitch.status === "loading" ? "作成中..." : "営業文を作成"}
                      </button>

                      <button
                        type="button"
                        className={styles.pitchButton}
                        onClick={() => handleDownloadHtml(shop, generation.site)}
                      >
                        HTMLでダウンロード
                      </button>
                    </div>

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

        <section className={styles.historySection}>
          <h2>検索履歴</h2>
          {searchHistory.length === 0 ? (
            <p className={styles.historyEmpty}>まだ検索履歴がありません。</p>
          ) : (
            <ul className={styles.historyList}>
              {searchHistory.map((entry) => (
                <li key={entry.id}>
                  <span className={styles.historyMain}>
                    {entry.region} × {entry.industry}
                  </span>
                  <span className={styles.historyMeta}>
                    {entry.resultCount}件 / {new Date(entry.timestamp).toLocaleString("ja-JP")}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className={styles.historySection}>
          <h2>生成履歴</h2>
          {generationHistory.length === 0 ? (
            <p className={styles.historyEmpty}>まだ生成履歴がありません。</p>
          ) : (
            <ul className={styles.historyList}>
              {generationHistory.map((entry) => (
                <li key={entry.id}>
                  <span className={styles.historyMain}>
                    {entry.shopName}（{entry.type === "site" ? "HPたたき台" : "営業文"}）
                  </span>
                  <span className={styles.historyMeta}>
                    {entry.region} × {entry.industry} / {new Date(entry.timestamp).toLocaleString("ja-JP")}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
