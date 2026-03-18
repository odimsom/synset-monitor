# Changelog

All notable changes to **SynsetMonitor** will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-18

### Added
- **Initial Release** of SynsetMonitor.
- Light-weight FastAPI backend parsing host system metrics using `psutil`.
- Single-page Vanilla HTML/JS Dashboard with a minimalist Dark aesthetic.
- Endpoints for hardware metrics: CPU (usage/temp), RAM, Disk, System Load, Active Processes count, Uptime, and Real-time Network I/O.
- Endpoint for Docker integrations reading `/var/run/docker.sock` to extract active containers, states, images, mapped ports, and uptime.
- Endpoint for reading recent Syslog/Messages lines for event tracking.
- Interactive Dashboard UI components natively pulling data and auto-refreshing every 10 seconds.
- Dockerfile y `docker-compose.yml` for simplified deployment supporting Dokploy usage with host-network mappings.
