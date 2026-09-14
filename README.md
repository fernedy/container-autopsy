<div align="center">

[🇬🇧 English](README.md) · [🇪🇸 Español](README.es.md)

</div>

<div align="center">

# ⚰️ container-autopsy

**Your container died. Find out WHY, not just THAT it did.**

![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-0-00A884?style=flat-square)
![Docker](https://img.shields.io/badge/runs%20in-docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)

**Zero dependencies · One file · AI First, human-approved**

</div>

---

`docker ps -a` tells you a container **exited (137)**. It doesn't tell you that the kernel OOM-killed it at 2 a.m., after a memory leak your logs warned you about three times. Recruiters, teammates and **AI agents** debugging your stack at 3 a.m. deserve better.

**container-autopsy** is a forensic tool for dead containers. It collects the evidence (exit code, OOM state, restart count, uptime before death, last log lines), runs a deterministic rule engine over it and hands you a **markdown autopsy report**: cause of death, contributing evidence, and the exact fix.

## ⚡ Quickstart

```bash
# one container, no install (mounts your docker socket, read-only usage)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  ghcr.io/fernedy/container-autopsy:latest my-dead-container
```

or clone and run:

```bash
git clone https://github.com/fernedy/container-autopsy.git
cd container-autopsy
python container_autopsy.py my-dead-container
```

Sample output:

```markdown
## ⚰️ Autopsy report — `my-app`

| Evidence | Value |
|---|---|
| Image | `python:3.12-slim` |
| Status | exited |
| Exit code | **137** |
| OOMKilled | True |
| Restarts | 4 |
| Uptime before death | 0:05:30 |

### 🕯️ Cause of death
**🗡️ SIGKILL (128+9)** — Killed forcibly. Almost always the kernel OOM killer (see OOMKilled) or a docker stop -f timeout.

### 🔎 Contributing evidence
- **🧠 OOMKilled — the container exceeded its memory limit** — Raise the memory limit (--memory / compose mem_limit) or fix the leak...
- **🔁 Restart storm — restarted 4 times** — Fix the root cause below before it burns your restart budget...

### 📜 Last log lines
```
2026-09-13T10:05:29Z ERROR: Cannot allocate memory
```
```

## 🤖 AI First, human-approved

Add `--ai` and your **local** agent CLI (e.g. [opencode](https://opencode.ai)) gets the finished report and appends a second opinion: most likely root cause, one command to confirm it, one command to fix it.

- **Opt-in**: without the flag, nothing leaves your machine. Ever.
- **Local**: no API keys, no cloud calls, no telemetry.
- **Human in the loop**: the deterministic report is the source of truth; the AI only annotates it.

```bash
python container_autopsy.py my-app --ai
```

## 🚀 The viral part — share your autopsies

Add `--share` and the report ends with a paste-ready block:

```markdown
### my-app — 💥 exit-1 🔴
![autopsy badge](https://img.shields.io/badge/container_autopsy-exit--137-D93F3F?style=flat-square&logo=docker)

Forensics by [container-autopsy](https://github.com/fernedy/container-autopsy) — know WHY your container died, not just THAT it died.
```

Post your post-mortem with the badge. A wall of autopsy badges is an incident timeline.

## 🧰 All the knobs

```bash
python container_autopsy.py <container>          # full autopsy (markdown)
python container_autopsy.py <container> --json   # raw evidence, machine-readable
python container_autopsy.py <container> --tail 100   # collect more log lines
python container_autopsy.py <container> --ai     # + local AI second opinion
python container_autopsy.py <container> --share  # + shareable badge block
```

It also works on **running** containers (a health check with the cause of death replaced by an "alive" verdict).

## 🐳 Run it in Docker (the point of the project)

```bash
git clone https://github.com/fernedy/container-autopsy.git
cd container-autopsy
docker compose build
docker compose run --rm autopsy my-dead-container
```

The image is `python:3.12-alpine` + the Docker CLI. The socket is mounted read-only in spirit: the tool only ever calls `inspect` and `logs` — it never starts, stops or removes anything.

## 📊 How the diagnosis works

Deterministic rules, not vibes: a 9-entry exit-code table (137 → SIGKILL/OOM, 139 → segfault, 143 → SIGTERM…), 10 log-pattern rules (OOM traces, refused connections, tracebacks, Go panics, health-check failures…), restart-storm detection and uptime analysis. Full methodology in [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

## ✅ Tested

```bash
python -m unittest discover -v
```

The suite mocks Docker entirely — CI runs on Python 3.8, 3.10 and 3.12 with no Docker daemon. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## 🤝 Contributing

New exit codes, new log patterns, new evidence sources. See [CONTRIBUTING.md](CONTRIBUTING.md). Dogfooding rule: **PRs must not lower this repo's Glow Score.**

## 📜 License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

Built AI-first by [Fernedy Arias](https://github.com/fernedy) · Tech Explorer

*If container-autopsy solved a mystery for you, drop a ⭐ and share the report.*

</div>
