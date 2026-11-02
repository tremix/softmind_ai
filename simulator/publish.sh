#!/bin/sh
# Publica cada video de ./videos como una cámara RTSP en bucle:
#   videos/entrada.mp4 -> rtsp://<host>:8554/entrada
# En Nx: añade la cámara manualmente con esa URL RTSP.
set -eu
RTSP_HOST="${RTSP_HOST:-mediamtx}"
VIDEOS_DIR="${VIDEOS_DIR:-/videos}"

found=0
for f in "$VIDEOS_DIR"/*.mp4; do
  [ -e "$f" ] || continue
  found=1
  name="$(basename "$f" .mp4)"
  echo "Publicando $f en rtsp://$RTSP_HOST:8554/$name"
  ffmpeg -hide_banner -loglevel warning -re -stream_loop -1 -i "$f" \
    -c:v libx264 -preset veryfast -tune zerolatency -g 30 -an \
    -f rtsp -rtsp_transport tcp "rtsp://$RTSP_HOST:8554/$name" &
done

if [ "$found" -eq 0 ]; then
  echo "No hay videos .mp4 en $VIDEOS_DIR; publicando patrón de prueba en /test"
  ffmpeg -hide_banner -loglevel warning -re -f lavfi -i testsrc2=size=1280x720:rate=15 \
    -c:v libx264 -preset veryfast -tune zerolatency -g 30 \
    -f rtsp -rtsp_transport tcp "rtsp://$RTSP_HOST:8554/test" &
fi
wait
