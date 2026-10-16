export interface Calibration {
  value_um: number | null; source: string; conflict: boolean; candidates: Record<string, number>;
}
export interface ImageInfo {
  filename: string; series_index: number; series_count: number; source_axes: string; axes: string;
  shape: number[]; dtype: string; bit_depth: number; dimensions: Record<string, number>;
  channel_labels: string[]; calibration: Record<string, Calibration>; warnings: string[];
  needs_axis_confirmation: boolean; acquisition: Record<string, string>; decoded_bytes: number;
}
export interface ImageRecord { id: string; sha256: string; info: ImageInfo; options: object }
export interface Runtime { apiUrl: string; token: string }
declare global { interface Window { organelleScope?: { runtime(): Promise<Runtime> } } }

export async function runtime(): Promise<Runtime> {
  if (window.organelleScope) return window.organelleScope.runtime();
  return { apiUrl: "http://127.0.0.1:8000", token: "development-only" };
}
export async function request(path: string, options: RequestInit = {}): Promise<Response> {
  const config = await runtime();
  const response = await fetch(config.apiUrl + path, { ...options, headers: {
    ...options.headers, "X-Session-Token": config.token
  }});
  if (!response.ok) {
    let message = `${response.status}: request failed`;
    try { const body = await response.json(); message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail); } catch { /* preserve status */ }
    throw new Error(message);
  }
  return response;
}
export async function json<T>(path: string, options: RequestInit = {}): Promise<T> {
  return (await request(path, options)).json() as Promise<T>;
}
