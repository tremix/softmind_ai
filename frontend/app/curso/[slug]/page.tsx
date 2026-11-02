import Link from "next/link";
import { notFound } from "next/navigation";
import { api, type CourseModule } from "@/lib/api";

export const dynamic = "force-dynamic";

const LAB_LINKS: Record<string, { href: string; label: string }> = {
  camaras: { href: "/camaras", label: "Abrir laboratorio de cámaras" },
  analiticas: { href: "/analiticas", label: "Abrir laboratorio de analíticas" },
  eventos: { href: "/analiticas", label: "Abrir laboratorio de eventos" },
  ia: { href: "/analiticas", label: "Ver resultados del worker de IA" },
};

export default async function ModulePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  let mod: CourseModule;
  try {
    mod = await api<CourseModule>(`/api/course/modules/${slug}`);
  } catch {
    notFound();
  }
  const lab = mod.lab ? LAB_LINKS[mod.lab] : null;
  return (
    <>
      <p><Link href="/">← Volver al curso</Link></p>
      <span className="badge">Módulo {mod.order} · {mod.level}</span>
      <h1>{mod.title}</h1>
      <p>{mod.summary}</p>
      <div className="notice">El contenido teórico de este módulo está pendiente de redactar.</div>
      {lab && <p><Link href={lab.href}>{lab.label} →</Link></p>}
    </>
  );
}
