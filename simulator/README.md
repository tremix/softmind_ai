# Simulador de cámaras

Convierte videos `.mp4` en cámaras RTSP para el laboratorio, sin hardware ni datos personales.

1. Copia videos de dominio público a `simulator/videos/` (p. ej. `parking.mp4`).
2. `docker compose --profile simulator up`
3. Cada video queda en `rtsp://<host>:8554/<nombre>`. Sin videos se publica un patrón de prueba en `/test`.
4. En Nx, añade la cámara con esa URL (Añadir dispositivo → URL RTSP).

Los videos no se suben al repositorio (ver `.gitignore`).
