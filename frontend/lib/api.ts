// Llamadas al backend desde componentes de servidor (se ejecutan en Next.js, no en el navegador).
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export type Camera = {
  id: string;
  name: string;
  status: string;
  vendor: string;
  model: string;
  url: string;
};

export type CourseModule = {
  slug: string;
  title: string;
  level: string;
  summary: string;
  lab: string | null;
  order: number;
};

export type ObjectTrack = {
  id: string;
  deviceId: string;
  objectTypeId: string;
  firstAppearanceTimeMs: number;
  lastAppearanceTimeMs: number;
  attributes?: { name: string; value: string }[];
};

export type NxEvent = {
  eventType: string;
  deviceId?: string | null;
  timestampMs: number;
  caption?: string;
  description?: string;
};

export async function api<T>(path: string): Promise<T> {
  const res = await fetch(`${BACKEND_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Error ${res.status} al llamar a ${path}`);
  }
  return res.json() as Promise<T>;
}

export function formatTime(ms: number): string {
  return new Date(ms).toLocaleString("es-ES");
}
