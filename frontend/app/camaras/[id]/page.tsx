import Link from "next/link";
import { notFound } from "next/navigation";
import { api, formatTime, type Camera, type ObjectTrack } from "@/lib/api";
import WebRtcPlayer from "@/components/WebRtcPlayer";

export const dynamic = "force-dynamic";

export default async function CameraPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let camera: Camera;
  try {
    camera = await api<Camera>(`/api/cameras/${id}`);
  } catch {
    notFound();
  }
  const objects = await api<ObjectTrack[]>(`/api/analytics/objects?deviceId=${id}&limit=10`);

  return (
    <>
      <p><Link href="/camaras">← Todas las cámaras</Link></p>
      <h1>{camera.name}</h1>
      <span className={`badge status-${camera.status}`}>{camera.status}</span>
      <div style={{ marginTop: 16 }}>
        <WebRtcPlayer cameraId={camera.id} />
      </div>
      <h2>Últimos objetos detectados</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Tipo</th><th>Primera aparición</th><th>Atributos</th></tr>
          </thead>
          <tbody>
            {objects.map((o) => (
              <tr key={o.id}>
                <td>{o.objectTypeId.replace("nx.base.", "")}</td>
                <td>{formatTime(o.firstAppearanceTimeMs)}</td>
                <td>{(o.attributes ?? []).map((a) => `${a.name}: ${a.value}`).join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
