// AIが改行区切りで返す箇条書き文字列を、先頭の記号（・-*など）を除いた配列に変換する
export function splitToListItems(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim().replace(/^[・\-*•]\s*/, ""))
    .filter((line) => line.length > 0);
}
