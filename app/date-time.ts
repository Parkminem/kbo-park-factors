export function formatSeoulDateTime(value: string): string {
  return new Date(value).toLocaleString("ko-KR", { timeZone: "Asia/Seoul" });
}
