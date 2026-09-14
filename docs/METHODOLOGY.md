# Methodology — how an autopsy works

container-autopsy is deterministic first and AI second. The same evidence always produces the same report; the AI mode only annotates it.

## 1. Evidence collection

Everything is read-only, pulled straight from the Docker Engine API via the CLI:

| Evidence | Source | Why it matters |
|---|---|---|
| `ExitCode` | `docker inspect .State` | The single strongest signal of *how* the process ended |
| `OOMKilled` | `docker inspect .State` | Distinguishes "kernel killed it" from "app crashed" |
| `RestartCount` | `docker inspect` | A high count means a chronic, not accidental, death |
| `StartedAt` / `FinishedAt` | `docker inspect .State` | Uptime before death separates fast-crash loops from long-running failures |
| Last N log lines | `docker logs --tail --timestamps` | The app's own account of its final moments |

## 2. Deterministic verdicts

### Exit-code table

| Code | Meaning | Typical cause |
|------|---------|---------------|
| 0 | Clean exit | Entrypoint finished its job; nothing keeping the container alive |
| 1 | Application error | Uncaught exception; traceback usually in the last logs |
| 2 | Shell/CLI misuse | Bad arguments to CMD/ENTRYPOINT |
| 125 | Docker daemon error | `docker run` itself failed |
| 126 | Not executable | Missing execute bit / permissions |
| 127 | Command not found | Binary missing from image or PATH |
| 137 | SIGKILL (128+9) | Kernel OOM killer or `docker stop -f` timeout |
| 139 | SIGSEGV (128+11) | Native-code segfault |
| 143 | SIGTERM (128+15) | Orchestrated stop or reschedule |

### Log-pattern rules

Ten regex rules over the collected logs: out-of-memory traces, refused/reset connections, timeouts, permission errors, missing files, Python tracebacks, Go panics, fatal errors, health-check failures. Only the highest-priority match is reported; the exit code covers the rest.

## 3. AI mode is opt-in and local

`--ai` pipes the finished report to a local agent CLI (opencode). If the CLI is missing, the report is still complete — the AI section is an enhancement, never a dependency. No API keys, no cloud calls.

## 4. Shareable by design

`--share` emits a badge + attribution block. The badge encodes the exit code, so a wall of badges doubles as an incident timeline.
