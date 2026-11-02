"use client";

import { useEffect, useRef, useState } from "react";

type StreamConfig = {
  mock: boolean;
  systemId: string;
  cameraId: string;
  accessToken: string;
  relayUrl: string;
  useRelayPrefix: boolean;
};

/** Reproductor de video en vivo usando la librería oficial de Nx (WebRTC). */
export default function WebRtcPlayer({ cameraId }: { cameraId: string }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [message, setMessage] = useState<string>("Conectando…");

  useEffect(() => {
    let cancelled = false;
    const cleanups: (() => void)[] = [];

    (async () => {
      const res = await fetch(`/api/cameras/${cameraId}/stream`);
      if (!res.ok) {
        setMessage(`No se pudo obtener la configuración del stream (${res.status}).`);
        return;
      }
      const cfg: StreamConfig = await res.json();
      if (cfg.mock) {
        setMessage("Modo simulado: configura NX_URL en el backend para ver video real.");
        return;
      }

      // Import dinámico: la librería usa APIs del navegador.
      const { StreamManager, TargetStream } = await import("@networkoptix/webrtc-stream-manager");
      if (cancelled) return;

      try {
        StreamManager.getInstance();
      } catch {
        StreamManager.configure({
          relayUrl: cfg.relayUrl,
          useRelayPrefix: cfg.useRelayPrefix,
          maxBehind: 5,
          useUnreliableDataChannel: true,
        });
      }
      const manager = StreamManager.getInstance();
      const connection = manager.connect({
        systemId: cfg.systemId,
        cameraId: cfg.cameraId,
        accessToken: cfg.accessToken,
        targetStream: TargetStream.AUTO,
      });

      cleanups.push(
        connection.on("track", ({ streams }) => {
          const video = videoRef.current;
          if (!video || !streams[0]) return;
          video.srcObject = streams[0];
          video.muted = true;
          void video.play().catch(() => undefined);
          setMessage("");
        }),
        connection.on("error", (err) => {
          setMessage(`Error de conexión: ${String(err)}`);
        }),
        // La librería identifica la conexión como "systemId:cameraId".
        () => manager.disconnect(`${cfg.systemId}:${cfg.cameraId}`),
      );
    })().catch((err) => setMessage(`Error: ${String(err)}`));

    return () => {
      cancelled = true;
      cleanups.forEach((fn) => fn());
    };
  }, [cameraId]);

  return (
    <div>
      {message && <div className="notice">{message}</div>}
      <video ref={videoRef} className="player" playsInline autoPlay muted />
    </div>
  );
}
