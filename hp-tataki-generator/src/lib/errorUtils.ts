function getCauseCode(error: unknown): string | undefined {
  if (error instanceof Error && "cause" in error) {
    const cause = (error as { cause?: unknown }).cause;
    if (cause && typeof cause === "object" && "code" in cause) {
      const code = (cause as { code?: unknown }).code;
      if (typeof code === "string") return code;
    }
  }
  return undefined;
}

// Node/undiciのfetchは中身のない"fetch failed"しか返さないため、cause.codeから原因を推測する
export function describeFetchError(error: unknown, actionLabel: string): string {
  if (error instanceof Error && error.message === "fetch failed") {
    const code = getCauseCode(error);
    const hint =
      code === "ENOTFOUND" || code === "EAI_AGAIN"
        ? "（インターネット接続、またはDNSの問題の可能性があります）"
        : code === "ECONNREFUSED"
          ? "（通信が拒否されました。プロキシやファイアウォールの可能性があります）"
          : code === "CERT_HAS_EXPIRED" || code?.includes("CERT")
            ? "（SSL証明書の検証に失敗しました。ウイルス対策ソフトのHTTPS検査機能が原因の可能性があります）"
            : "";
    return `${actionLabel}中にネットワークエラーが発生しました${code ? `（コード: ${code}）` : ""}。${hint} インターネット接続、プロキシ、ウイルス対策ソフトの設定をご確認ください。`;
  }

  return error instanceof Error
    ? error.message
    : `${actionLabel}中にエラーが発生しました。`;
}
