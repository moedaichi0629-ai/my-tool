import { readFileSync } from "fs";
import { join } from "path";
import { google } from "googleapis";

const MAX_SHEET_TITLE_LENGTH = 100;
const HEADER_ROW = ["店舗名", "GoogleマップURL", "地域", "業種", "保存日時"];

interface ServiceAccountCredentials {
  client_email: string;
  private_key: string;
}

function getSpreadsheetId(): string {
  const id = process.env.GOOGLE_SHEETS_SPREADSHEET_ID;
  if (!id) {
    throw new Error("GOOGLE_SHEETS_SPREADSHEET_IDが設定されていません。.env.localを確認してください。");
  }
  return id;
}

function parseCredentials(raw: string, sourceLabel: string): ServiceAccountCredentials {
  const parsed = JSON.parse(raw) as Partial<ServiceAccountCredentials>;
  if (!parsed.client_email || !parsed.private_key) {
    throw new Error(`サービスアカウントの認証情報（${sourceLabel}）の形式が正しくありません。`);
  }
  return { client_email: parsed.client_email, private_key: parsed.private_key };
}

function loadCredentials(): ServiceAccountCredentials {
  // Vercelなどのサーバーレス環境ではファイルを配置できないため、JSON文字列を直接環境変数で渡す方式を優先する
  const inlineJson = process.env.GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON;
  if (inlineJson) {
    return parseCredentials(inlineJson, "GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON");
  }

  const relativePath = process.env.GOOGLE_SHEETS_CREDENTIALS_FILE;
  if (!relativePath) {
    throw new Error(
      "GOOGLE_SHEETS_SERVICE_ACCOUNT_JSONまたはGOOGLE_SHEETS_CREDENTIALS_FILEが設定されていません。.env.localを確認してください。"
    );
  }

  const filePath = join(/* turbopackIgnore: true */ process.cwd(), relativePath);
  let raw: string;
  try {
    raw = readFileSync(filePath, "utf-8");
  } catch {
    throw new Error(
      `サービスアカウントのJSONキーファイルが見つかりません（${relativePath}）。ダウンロードしたファイルを配置したか確認してください。`
    );
  }

  return parseCredentials(raw, relativePath);
}

function getAuth() {
  const credentials = loadCredentials();

  return new google.auth.JWT({
    email: credentials.client_email,
    key: credentials.private_key,
    scopes: ["https://www.googleapis.com/auth/spreadsheets"],
  });
}

function buildSheetTitle(region: string, industry: string): string {
  const raw = `${region}_${industry}`;
  const sanitized = raw.replace(/[:\\/?*[\]]/g, "_");
  return sanitized.slice(0, MAX_SHEET_TITLE_LENGTH);
}

async function ensureSheetExists(
  sheets: ReturnType<typeof google.sheets>,
  spreadsheetId: string,
  sheetTitle: string
): Promise<void> {
  const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId });
  const existingTitles = (spreadsheet.data.sheets ?? []).map((sheet) => sheet.properties?.title);

  if (existingTitles.includes(sheetTitle)) {
    return;
  }

  await sheets.spreadsheets.batchUpdate({
    spreadsheetId,
    requestBody: {
      requests: [{ addSheet: { properties: { title: sheetTitle } } }],
    },
  });

  await sheets.spreadsheets.values.append({
    spreadsheetId,
    range: `'${sheetTitle}'!A1`,
    valueInputOption: "RAW",
    requestBody: { values: [HEADER_ROW] },
  });
}

export async function saveShopToSheet(params: {
  shopName: string;
  mapUrl: string | null;
  region: string;
  industry: string;
}): Promise<void> {
  const spreadsheetId = getSpreadsheetId();
  const auth = getAuth();
  const sheets = google.sheets({ version: "v4", auth });
  const sheetTitle = buildSheetTitle(params.region, params.industry);

  await ensureSheetExists(sheets, spreadsheetId, sheetTitle);

  await sheets.spreadsheets.values.append({
    spreadsheetId,
    range: `'${sheetTitle}'!A1`,
    valueInputOption: "RAW",
    requestBody: {
      values: [
        [
          params.shopName,
          params.mapUrl ?? "",
          params.region,
          params.industry,
          new Date().toLocaleString("ja-JP"),
        ],
      ],
    },
  });
}
