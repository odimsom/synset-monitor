# Changelog

All notable changes to **SynsetMonitor** will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-03-18
### Added
- **Red Avanzada Module**: New dashboard tab built for deep network connection layer telemetry.
- **TCP States Tracker**: Live tracking of ESTABLISHED, LISTEN, and TIME_WAIT socket states to detect web server connection leaks.
- **Hardware Network Health**: Metrics capturing Dropped Packets (IN/OUT) and Corrupt Error Packets (IN/OUT) directly from `psutil` NIC stats.
- **Network Smart Alerts**: Real-time push notifications for TCP exhaustion (`TIME_WAIT` > 1000) and severe packet collisions or firewall drops triggers.

## [1.2.0] - 2026-03-18
### Added
- **Servicios y Docker Module**: New dashboard tab focusing on container statuses and API Service Level Agreement (SLA).
- **HTTP Health Checks**: Automated heartbeat engine fetching and timing remote endpoints configured via `.env` `TARGET_SERVICES`.
- **Deep Storage Metrics**: Disk Latency and IOPS measuring for predicting write/read bottlenecks.
- **Docker Restart Tracking**: Intelligent metric keeping track of Crash Loops (Restarts > 5 trigger critical alert).
- **Smart Alerts Interface**: Slide-in notification system dynamically triggered by system faults (OOMKilled, High IOWait, High Swap, Exit 1 containers, CPU lags).
- **Deep System Module**: New dashboard tab displaying CPU Steal Time, IO Wait limits, Swap Ins/Outs and memory pressure.
- Sidebar Dashboard Navigation preventing re-loads for independent modules.
- Refactored frontend structure allowing independent scaling of logic.

### Changed
- Refactored `index.html` into a modular application using Vanilla JS.
- Default `.env.example` includes `TARGET_SERVICES` fallback.

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
