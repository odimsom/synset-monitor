# SynsetMonitor

SynsetMonitor es un dashboard de monitoreo de servidores minimalista, integrado en una sola aplicación con Python (FastAPI) y Vanilla JS.
Ofrece métricas de CPU, RAM, Almacenamiento, Contenedores Docker activos y los últimos registros del sistema.

## Requisitos Previos

- Docker
- Docker Compose

## Despliegue Local o en Dokploy (usando Docker Compose)

1. Clona el repositorio:
   ```bash
   git clone <URL_DEL_REPO>
   cd synset-monitor
   ```

2. Configura las variables de entorno basándote en el archivo de ejemplo:
   ```bash
   cp .env.example .env
   ```
   **Importante:** Edita `.env` para cambiar tus credenciales.

3. Despliega la aplicación con `docker-compose`:
   ```bash
   docker-compose up -d --build
   ```

## Notas Rápidas

- **Network Mode**: Está utilizando `network_mode: host` para que FastAPI esté expuesto directamente en los puertos del host y tenga máxima visibilidad. Si esto conflictúa con tus reglas, puedes cambiarlo para unirse a `dokploy-network` en `docker-compose.yml`.
- **Volúmenes**: Necesita acceso a `/proc`, `/sys` y `/var/run/docker.sock` para leer el estado del host de forma precisa, por eso se montan como read-only.
- **Seguridad**: El JWT protege toda la ruta `/metrics/*` y solo expone `/login`. Cambia tu `JWT_SECRET` en producción.
