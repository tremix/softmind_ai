import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "SoftMind AI — Curso de video con analíticas e IA",
  description: "Plataforma de formación en gestión de video con Nx Witness, analíticas e inteligencia artificial.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>
        <header className="top">
          <Link href="/" className="brand">SoftMind AI</Link>
          <Link href="/">Curso</Link>
          <Link href="/camaras">Cámaras</Link>
          <Link href="/analiticas">Analíticas</Link>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
