import Link from "next/link";
import { api, type CourseModule } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CoursePage() {
  const modules = await api<CourseModule[]>("/api/course/modules");
  return (
    <>
      <h1>Gestión de video con analíticas e IA</h1>
      <p className="muted">
        Curso práctico sobre Nx Witness: cámaras, grabación, reglas, analíticas y modelos de IA, todo desde la web.
      </p>
      <div className="grid">
        {modules.map((m) => (
          <Link key={m.slug} href={`/curso/${m.slug}`} className="card">
            <span className="badge">Módulo {m.order} · {m.level}</span>
            <h3>{m.title}</h3>
            <p className="muted">{m.summary}</p>
          </Link>
        ))}
      </div>
    </>
  );
}
