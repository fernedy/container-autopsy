# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/) and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-09-14

### Added
- Forensic evidence collection from Docker containers: exit code, OOMKilled, restart count, uptime, last log lines (`collect`).
- Deterministic rule engine: exit-code table (0, 1, 2, 125–143) and 10 log-pattern findings (`analyze`).
- Markdown autopsy report with evidence table, cause of death and last logs (`render_markdown`).
- `--json` machine-readable output.
- `--share` shareable badge block.
- `--ai` optional local second opinion via agent CLI (opencode). No cloud, no API keys.
- Official Docker image (Dockerfile + docker-compose.yml) so the tool can autopsy siblings via the docker socket.
- CI on Python 3.8 / 3.10 / 3.12, mocked test suite (no Docker required).
