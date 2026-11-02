# Análisis del entorno — Plataforma web de analíticas de video con Nx Witness + curso online

Fecha: 2 de noviembre de 2026

## 1. Objetivo

Construir una aplicación **web** que se conecte al VMS **Nx Witness / Nx Meta** para:

1. Ver video en vivo y grabado desde el navegador.
2. Consultar y visualizar analíticas (objetos detectados, eventos, reglas).
3. Ejecutar modelos de IA propios sobre las cámaras y devolver resultados al VMS.
4. Servir como **plataforma de curso**: módulos teóricos + laboratorios prácticos donde cada alumno opera el VMS y las analíticas desde la web.

---

## 2. Entorno de desarrollo actual (este sandbox)

| Recurso | Estado | Impacto |
|---|---|---|
| CPU / RAM / disco | 4 vCPU, 15 GB RAM, ~30 GB libres | Suficiente para frontend, backend y pruebas de IA ligeras |
| GPU | **No hay** | Inferencia solo en CPU (modelos pequeños: YOLO nano/small en ONNX) |
| Node.js / npm | v22 / 10.9 | OK para React/Next.js y backend Node |
| Python | 3.13 + `onnxruntime` 1.29 | OK para workers de IA; falta `opencv` (se instala por pip) |
| ffmpeg | 6.1 | OK para simular cámaras RTSP con videos de prueba |
| PostgreSQL / Redis | 16 / 7 instalados | OK para usuarios del curso, progreso, colas |
| Docker | CLI instalado, **daemon no disponible** | No se pueden levantar contenedores aquí |
| Git | 2.43; el directorio de trabajo **no es un repositorio** | Hay que crear/enlazar un repo para no perder el trabajo |
| Red: npm, PyPI, Docker Hub | Accesibles | Se pueden instalar dependencias |
| Red: networkoptix.com, meta.nxvms.com, support.networkoptix.com | **Bloqueados** | No se pueden descargar instaladores ni docs de Nx desde aquí |
| Paquete `@networkoptix/webrtc-stream-manager` | Accesible en npm (v0.1.29) | Se puede usar para el reproductor WebRTC |

**Conclusión:** este sandbox sirve para **desarrollar la app web y los workers de IA**, pero **no puede alojar el servidor Nx**. Se necesita un servidor Nx real (VM en la nube u on‑premise) accesible desde la app.

---

## 3. Plataforma Nx: lo relevante para el proyecto

### 3.1 Versiones y licencias
- Rama actual: **Gen 6** (6.0.x estable; 6.1 con motor de reglas renovado, layouts y enlaces compartidos vía Nx Cloud).
- **Nx Meta** (plataforma para desarrolladores): descarga gratuita del servidor y cliente + licencias de prueba; API y SDK gratuitos. Es la opción recomendada para el entorno del curso.
- **Nx AI Manager** viene incluido en Nx Witness Enterprise desde Media Server 6.1.1+ y se licencia por canal.
- Las licencias de Nx Witness comercial se gestionan con ventas/integrador; para producción hay que presupuestar canales.

### 3.2 APIs disponibles
| Necesidad | Mecanismo Nx | Notas |
|---|---|---|
| Autenticación local | REST `/rest/v3|v4/login/sessions` → token Bearer | Usar desde el backend, nunca exponer credenciales en el navegador |
| Acceso remoto | Nx Cloud (OAuth2 + relay) | Útil si los alumnos están fuera de la red del servidor |
| Cámaras / dispositivos | `/rest/v4/devices` | Altas, estado, configuración |
| Video en vivo/grabado | **WebRTC** (recomendado; librería `webrtc-stream-manager`) | El cliente web oficial usa WebRTC desde 6.0 |
| Alternativas de video | HLS, `/media/<id>.webm/.mp4`, MJPEG, miniaturas | HLS tiene mucha latencia y hay reportes de inestabilidad con muchos clientes |
| Objetos detectados | `/rest/v4/analytics/objectTracks` y `.../{id}/bestShotImage` | Sustituye al antiguo `/ec2/analyticsLookupObjectTracks` |
| Registro de eventos | `/rest/v4/events/log` | Filtrable por cámara, tiempo, atributos |
| Enviar eventos al VMS | Generic Event (`createEvent`) por HTTP | Permite que nuestra IA dispare reglas en Nx |
| Recibir eventos del VMS | Motor de reglas → acción "HTTP request" (webhook) | Una regla por tipo de evento |
| IA integrada en servidor | **Metadata SDK** (plugins C++), Nx AI Manager, plugins de terceros (p. ej. CVEDIA‑RT) | Los plugins dibujan cajas y atributos en el propio VMS |

> Los endpoints exactos cambian entre versiones (v3/v4). Validar siempre contra la documentación de API integrada en el servidor que se instale.

---

## 4. Arquitectura propuesta

```
 Navegador (alumno / instructor)
   ├─ App del curso (React / Next.js): módulos, quizzes, progreso
   └─ Consola VMS web: reproductor WebRTC, línea de tiempo, objetos, eventos
            │ HTTPS / WebSocket
            ▼
 Backend (BFF) — Node.js o Python FastAPI
   ├─ Autenticación del curso y mapeo alumno → usuario Nx
   ├─ Proxy hacia la REST API de Nx (oculta tokens, resuelve CORS y certificados)
   ├─ Receptor de webhooks de reglas Nx
   └─ PostgreSQL (curso, progreso, laboratorios) + Redis (colas, sesiones)
            │
            ├──────────────► Servidor Nx Meta / Nx Witness (VM con GPU opcional)
            │                  ├─ Cámaras simuladas (RTSP con ffmpeg/mediamtx + videos de prueba)
            │                  ├─ Plugins de analítica (Metadata SDK / Nx AI Manager)
            │                  └─ Grabación y base de objetos
            │
            └──────────────► Worker de IA (Python + ONNX Runtime / YOLO)
                               ├─ Lee RTSP desde Nx
                               └─ Devuelve resultados como Generic Events o vía plugin
```

**Por qué un backend intermedio:** el servidor Nx usa por defecto certificados autofirmados y el puerto 7001; llamar directamente desde el navegador provoca errores de CORS/TLS y obliga a exponer credenciales.

---

## 5. Entorno de laboratorio para el curso

| Componente | Recomendación mínima |
|---|---|
| Servidor Nx | VM Ubuntu 22.04/24.04, 8 vCPU, 16–32 GB RAM, 500 GB disco. GPU NVIDIA (T4 o similar) si la IA corre en servidor |
| Cámaras | 8–16 cámaras simuladas con videos públicos (tráfico, retail, parking). Evita depender de hardware y de datos personales reales |
| Usuarios | Un usuario Nx por alumno con permisos limitados, o un servidor/sitio por grupo |
| Acceso | Dominio + certificado válido (Let's Encrypt) delante del backend; Nx Cloud o TURN si hay alumnos fuera de la red |
| Concurrencia | Medir cuántos streams WebRTC simultáneos aguanta el servidor; preferir subflujo de baja resolución para alumnos |

---

## 6. Propuesta de estructura del curso

1. Fundamentos de videovigilancia IP (RTSP, ONVIF, códecs, almacenamiento).
2. Nx Witness: arquitectura, servidor, cliente, licencias.
3. Gestión de cámaras, grabación y layouts desde la web.
4. Motor de eventos y reglas (Gen 6).
5. Analíticas: detección de objetos, búsqueda de objetos, best shots.
6. IA aplicada: modelos YOLO/ONNX, entrenamiento básico, métricas.
7. Integración: REST API, webhooks, Generic Events.
8. Desarrollo de plugins con Metadata SDK (nivel avanzado).
9. Privacidad y normativa (RGPD / leyes locales de protección de datos).
10. Proyecto final: caso de uso completo (aforo, intrusión, conteo de vehículos…).

---

## 7. Riesgos y puntos a resolver

| Riesgo | Mitigación |
|---|---|
| Diferencias de API entre versiones de Nx | Fijar una versión del servidor para todo el curso |
| CORS / certificados autofirmados | Backend proxy + certificado válido |
| WebRTC detrás de NAT | Nx Cloud o servidor TURN |
| Inferencia lenta sin GPU | Modelos ligeros, FPS bajos, o VM con GPU |
| Carga con muchos alumnos simultáneos | Subflujos, límite de streams por alumno, pruebas de carga |
| Licencias por canal (producción) | Nx Meta para el curso; presupuestar licencias si se pasa a producción |
| Datos personales en video | Usar solo videos públicos o con consentimiento; anonimización |
| Este sandbox no puede alojar Nx ni contenedores | Servidor Nx externo; repo Git para conservar el código |

---

## 8. Próximos pasos

1. Registrarse en el portal de desarrolladores **Nx Meta** y descargar servidor + SDK.
2. Provisionar la VM del servidor Nx y cargar 4–8 cámaras simuladas.
3. Decidir stack: **Next.js + FastAPI** (recomendado, por el ecosistema de IA en Python) o todo Node.js.
4. Crear repositorio Git y esqueleto: login, proxy Nx, reproductor WebRTC, lista de cámaras.
5. Prototipo de analítica: worker YOLO (ONNX) → Generic Event → regla Nx → visualización en la web.
6. Diseñar contenido del módulo 1 y el primer laboratorio.

---

## Fuentes
- [Play back video using WebRTC (Network Optix)](https://support.networkoptix.com/hc/en-us/articles/32894602219671-Play-back-video-using-WebRTC)
- [@networkoptix/webrtc-stream-manager (npm)](https://www.npmjs.com/package/%40networkoptix%2Fwebrtc-stream-manager)
- [networkoptix/web_packages (GitHub)](https://www.github.com/networkoptix/web_packages)
- [Low latency streaming with multiple clients](https://support.networkoptix.com/hc/en-us/community/posts/4404205099415-Low-latency-streaming-with-multiple-clients)
- [Memory leak when using HLS streams](https://support.networkoptix.com/hc/en-us/community/posts/33376016101271-Memory-leak-when-using-HLS-streams)
- [Retrieve analytics events without legacy /ec2 endpoints](https://support.networkoptix.com/hc/en-us/community/posts/34068457995031-How-to-Retrieve-Analytics-Events-Without-Using-Legacy-ec2-Endpoints)
- [Get NX events to third party application](https://support.networkoptix.com/hc/en-us/community/posts/38042722050455-Get-NX-events-to-third-party-application)
- [Generic Event (Nx help)](https://s3.amazonaws.com/resources.vmsproxy.com/nx_4.1_help/generic_event.htm)
- [Capturing Objects from Video — Metadata SDK](https://support.networkoptix.com/hc/en-us/articles/41596073508119)
- [Integración de analíticas con Nx Meta](https://support.networkoptix.com/hc/en-us/articles/41595975514391)
- [Get Started with Nx Meta](https://www.networkoptix.com/nx-meta/get-started-with-meta)
- [Nx AI Manager en Nx Witness Enterprise](https://www.networkoptix.com/blog/nx-ai-manager-is-now-available-in-nx-witness-enterprise)
- [New & Improved Event Rules in Gen 6](https://www.networkoptix.com/blog/new-and-improved-event-rules-overview)
- [Nx Witness Enterprise 6.1 (ISCS)](https://www.iscs.com.au/nx-witness-enterprise-6/)
- [Nx Witness Release Notes](https://www.networkoptix.com/all-nx-witness-release-notes)
- [CVEDIA-RT para Nx Witness](https://docs.cvedia.com/vms/nx_witness.html)
