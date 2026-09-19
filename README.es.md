<div align="center">

[🇬🇧 English](README.md) · [🇪🇸 Español](README.es.md)

</div>

<div align="center">

# ⚰️ container-autopsy

**Tu contenedor murió. Descubre POR QUÉ, no solo QUE murió.**

![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-0-00A884?style=flat-square)
![Docker](https://img.shields.io/badge/runs%20in-docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)

**Cero dependencias · Un archivo · AI First, con aprobación humana**

</div>

---

`docker ps -a` te dice que un contenedor **exited (137)**. No te dice que el kernel lo mató por OOM a las 2 a.m., después de que tus logs advirtieran tres veces sobre una fuga de memoria. Ese exit code a las 3 a.m. me tocó verlo en persona una vez de más.

**container-autopsy** es una herramienta forense para contenedores muertos. Recolecta la evidencia (exit code, estado de OOM, contador de restarts, uptime antes de la muerte, últimas líneas de log), le aplica un motor de reglas determinista y te entrega un **informe de autopsia en markdown**: causa de muerte, evidencia contribuyente y el fix exacto.

## ⚡ Inicio rápido

```bash
# un contenedor, sin instalar nada (monta tu docker socket, uso de solo lectura)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  ghcr.io/fernedy/container-autopsy:latest mi-contenedor-muerto
```

o clona y ejecuta:

```bash
git clone https://github.com/fernedy/container-autopsy.git
cd container-autopsy
python container_autopsy.py mi-contenedor-muerto
```

Ejemplo de salida:

```markdown
## ⚰️ Autopsy report — `my-app`

| Evidence | Value |
|---|---|
| Exit code | **137** |
| OOMKilled | True |
| Restarts | 4 |

### 🕯️ Cause of death
**🗡️ SIGKILL (128+9)** — Killed forcibly. Almost always the kernel OOM killer...

### 📜 Last log lines
```
2026-09-13T10:05:29Z ERROR: Cannot allocate memory
```
```

## 🤖 AI First, con aprobación humana

Agrega `--ai` y tu agent CLI **local** (ej. [opencode](https://opencode.ai)) recibe el informe terminado y añade una segunda opinión: causa raíz más probable, un comando para confirmarla y un comando para corregirla.

- **Opt-in**: sin la bandera, nada sale de tu máquina. Nunca.
- **Local**: sin API keys, sin llamadas a la nube, sin telemetría.
- **Human-in-the-loop**: el informe determinista es la fuente de verdad; la IA solo lo anota.

```bash
python container_autopsy.py my-app --ai
```

## 📣 Comparte tus autopsias

Agrega `--share` y el informe termina con un bloque listo para pegar:

```markdown
### my-app — 💥 exit-137 🔴
![autopsy badge](https://img.shields.io/badge/container_autopsy-exit--137-D93F3F?style=flat-square&logo=docker)

Forensics by [container-autopsy](https://github.com/fernedy/container-autopsy) — know WHY your container died, not just THAT it died.
```

Publica tu post-mortem con el badge. Una pared de badges de autopsia es una línea de tiempo de incidentes.

## 🧰 Todas las opciones

```bash
python container_autopsy.py <contenedor>          # autopsia completa (markdown)
python container_autopsy.py <contenedor> --json   # evidencia cruda, legible por máquinas
python container_autopsy.py <contenedor> --tail 100   # recolecta más líneas de log
python container_autopsy.py <contenedor> --ai     # + segunda opinión IA local
python container_autopsy.py <contenedor> --share  # + bloque de badge compartible
```

También funciona sobre contenedores **en ejecución** (un chequeo de salud, con la causa de muerte reemplazada por un veredicto «vivo»).

## 🐳 Ejecútalo en Docker (la gracia del proyecto)

```bash
git clone https://github.com/fernedy/container-autopsy.git
cd container-autopsy
docker compose build
docker compose run --rm autopsy mi-contenedor-muerto
```

La imagen es `python:3.12-alpine` + el CLI de Docker. El socket se usa en espíritu de solo lectura: la herramienta solo llama `inspect` y `logs` — nunca arranca, detiene ni elimina nada.

## 📊 Cómo funciona el diagnóstico

Reglas deterministas, no vibras: tabla de 9 exit codes (137 → SIGKILL/OOM, 139 → segfault, 143 → SIGTERM…), 10 reglas de patrones de log (trazas de OOM, conexiones rechazadas, tracebacks, panics de Go, fallos de health check…), detección de tormentas de restarts y análisis de uptime. Metodología completa en [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

## ✅ Tests

```bash
python -m unittest discover -v
```

La suite simula Docker por completo — el CI corre en Python 3.8, 3.10 y 3.12 sin daemon de Docker. Ver [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## 🤝 Contribuir

Nuevos exit codes, nuevos patrones de log, nuevas fuentes de evidencia. Ver [CONTRIBUTING.md](CONTRIBUTING.md). Regla de dogfooding: **los PRs no deben bajar el Glow Score de este repo.**

## 📜 Licencia

MIT — ver [LICENSE](LICENSE).

---

<div align="center">

Construido AI-first por [Fernedy Arias](https://github.com/fernedy) · Tech Explorer

*Si container-autopsy resolvió un misterio para ti, deja un ⭐ y comparte el informe.*

</div>
