import { api, formatTime, type Camera, type NxEvent, type ObjectTrack } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function AnalyticsPage() {
  const [cameras, objects, events] = await Promise.all([
    api<Camera[]>("/api/cameras"),
    api<ObjectTrack[]>("/api/analytics/objects?limit=25"),
    api<NxEvent[]>("/api/events"),
  ]);
  const camName = (id?: string | null) => cameras.find((c) => c.id === id)?.name ?? id ?? "—";

  const counts = objects.reduce<Record<string, number>>((acc, o) => {
    const type = o.objectTypeId.replace("nx.base.", "");
    acc[type] = (acc[type] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <>
      <h1>Analíticas</h1>
      <div className="grid">
        {Object.entries(counts).map(([type, n]) => (
          <div key={type} className="card">
            <div className="muted">{type}</div>
            <div style={{ fontSize: "1.8rem", fontWeight: 700 }}>{n}</div>
          </div>
        ))}
      </div>

      <h2>Eventos</h2>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Hora</th><th>Tipo</th><th>Cámara</th><th>Descripción</th></tr></thead>
          <tbody>
            {events.map((e, i) => (
              <tr key={i}>
                <td>{formatTime(e.timestampMs)}</td>
                <td>{e.eventType}</td>
                <td>{camName(e.deviceId)}</td>
                <td>{e.caption}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2>Objetos detectados</h2>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Hora</th><th>Tipo</th><th>Cámara</th></tr></thead>
          <tbody>
            {objects.map((o) => (
              <tr key={o.id}>
                <td>{formatTime(o.firstAppearanceTimeMs)}</td>
                <td>{o.objectTypeId.replace("nx.base.", "")}</td>
                <td>{camName(o.deviceId)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
