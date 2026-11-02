import Link from "next/link";
import { api, type Camera } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CamerasPage() {
  const cameras = await api<Camera[]>("/api/cameras");
  return (
    <>
      <h1>Cámaras</h1>
      <div className="grid">
        {cameras.map((c) => (
          <Link key={c.id} href={`/camaras/${c.id}`} className="card">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img className="thumb" src={`/api/cameras/${c.id}/thumbnail`} alt={`Miniatura de ${c.name}`} />
            <h3>{c.name}</h3>
            <span className={`badge status-${c.status}`}>{c.status}</span>{" "}
            <span className="muted">{c.vendor} {c.model}</span>
          </Link>
        ))}
      </div>
    </>
  );
}
