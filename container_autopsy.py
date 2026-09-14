#!/usr/bin/env python3
"""
container-autopsy — find out WHY your container died, not just THAT it died.

Zero dependencies (beyond a Docker CLI). Collects forensic evidence from a dead
container (exit code, OOM state, restart count, last log lines), runs a
deterministic rule engine over it and renders a markdown autopsy report you can
paste anywhere. Optional --ai mode asks your local agent CLI for a diagnosis.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

__version__ = "1.0.0"

# --- Known exit codes (docker + shell conventions) --------------------------
EXIT_CODES = {
    0: ("🌱 Clean exit", "The process exited on purpose. Check if this was expected — maybe the entrypoint finished its job and has nothing left to do. Add a long-running process (or a supervisor) if the container should stay up."),
    1: ("💥 Application error", "A generic uncaught error. Scroll to the last log lines: the traceback is usually right there."),
    2: ("💥 Misuse of shell / CLI", "The command was invoked incorrectly. Verify the CMD/ENTRYPOINT arguments and flags."),
    125: ("🐳 Docker daemon error", "Docker itself failed to run the container. Check the daemon logs and the container spec."),
    126: ("🔒 Command not executable", "The command exists but lacks the execute bit or permissions. RUN chmod +x or fix the entrypoint."),
    127: ("🔍 Command not found", "The entrypoint binary is missing from the image. Check PATH and that the binary was installed in this image, not a build stage you dropped."),
    137: ("🗡️ SIGKILL (128+9)", "Killed forcibly. Almost always the kernel OOM killer (see OOMKilled) or a docker stop -f timeout."),
    139: ("☠️ Segfault (128+11)", "The process dereferenced bad memory. Look for native extensions (C/Rust) or a broken base image."),
    143: ("🛑 SIGTERM (128+15)", "Gracefully terminated. Usually a docker stop / orchestrator reschedule. If unexpected, check liveness probes and shutdown hooks."),
}

LOG_PATTERNS = [
    (re.compile(r"out of memory|oom|cannot allocate memory|memorylimit|killed process", re.I),
     "🧠 Out-of-memory traces in logs", "The app logged memory pressure before dying. Raise the memory limit or fix the leak: reduce batch sizes, stream instead of loading, add a heap cap matching the container limit."),
    (re.compile(r"connection refused|econnrefused", re.I),
     "🔌 Dependency refused connection", "A downstream service (DB, cache, API) was not reachable. Check service order/healthchecks in compose, or add retry-with-backoff at startup."),
    (re.compile(r"econnreset|connection reset", re.I),
     "🔌 Dependency reset connection", "A peer closed the socket abruptly. Inspect timeouts, keep-alives and proxies between the two services."),
    (re.compile(r"timeout|etimedout", re.I),
     "⏱️ Timeout in logs", "An upstream call hung past the deadline. Add explicit timeouts and circuit breakers."),
    (re.compile(r"permission denied|eperm|eacces", re.I),
     "🔒 Permission denied in logs", "Filesystem or socket permissions. If running as non-root, chown the volume or relax the capability."),
    (re.compile(r"no such file|enoent", re.I),
     "📁 Missing file in logs", "A path referenced at runtime does not exist. Check volume mounts and that build steps produced the artifact."),
    (re.compile(r"traceback \(most recent call last\)", re.I),
     "🐍 Python traceback", "An unhandled Python exception. The last frames above the exit point name the failing module."),
    (re.compile(r"panic:|runtime error", re.I),
     "🟦 Go panic", "A Go runtime panic. The stack trace pinpoints the goroutine and line."),
    (re.compile(r"fatal|unhandled", re.I),
     "🚨 Fatal error in logs", "A fatal error was logged right before death."),
    (re.compile(r"health ?check failed|unhealthy", re.I),
     "🩺 Health check failures", "The orchestrator considered the container unhealthy and killed it. Review the probe command, endpoint and grace period."),
]


def sh(args):
    """Run a docker CLI command, returning (ok, stdout, stderr)."""
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=60)
        return p.returncode == 0, p.stdout, p.stderr
    except FileNotFoundError:
        sys.exit("error: docker CLI not found in PATH. Install Docker or run this tool in its official image.")
    except subprocess.TimeoutExpired:
        return False, "", "docker command timed out"


def _parse_ts(ts):
    """Parse docker timestamps ('...000000000Z', 9-digit nanos) on Python 3.8+."""
    try:
        return datetime.fromisoformat(ts[:19])
    except (ValueError, TypeError):
        return None


def collect(container, tail):
    """Gather forensic evidence from a container."""
    ok, out, err = sh(["docker", "inspect", container])
    if not ok:
        sys.exit("error: cannot inspect '%s': %s" % (container, err.strip() or "not found"))
    info = json.loads(out)[0]

    state = info.get("State", {})
    _, logs, _ = sh(["docker", "logs", "--tail", str(tail), "--timestamps", container])

    started = state.get("StartedAt", "")
    finished = state.get("FinishedAt", "")
    uptime = None
    try:
        if started and finished and not finished.startswith("0001"):
            t0 = _parse_ts(started)
            t1 = _parse_ts(finished)
            if t0 and t1:
                uptime = str(t1 - t0).split(".")[0]
    except ValueError:
        pass

    return {
        "container": info.get("Name", container).lstrip("/"),
        "image": info.get("Config", {}).get("Image", "?"),
        "status": state.get("Status", "?"),
        "running": state.get("Running", False),
        "exit_code": state.get("ExitCode"),
        "oom_killed": state.get("OOMKilled", False),
        "error": state.get("Error") or None,
        "restart_count": info.get("RestartCount", 0),
        "started_at": started,
        "finished_at": finished if not finished.startswith("0001") else None,
        "uptime": uptime,
        "logs": logs.strip().splitlines()[-tail:],
    }


def analyze(data):
    """Deterministic rule engine -> list of findings (title, fix)."""
    findings = []
    if data["oom_killed"]:
        findings.append(("🧠 OOMKilled — the container exceeded its memory limit",
                         "Raise the memory limit (--memory / compose mem_limit) or fix the leak. Consider setting a JVM/node heap cap ~75% of the container limit so the runtime dies before the kernel kills you."))
    if data["restart_count"] >= 3:
        findings.append(("🔁 Restart storm — restarted %d times" % data["restart_count"],
                         "The container keeps dying and being revived. Fix the root cause below before it burns your restart budget (CrashLoopBackOff on Kubernetes)."))
    for pattern, title, fix in LOG_PATTERNS:
        hits = [l for l in data["logs"] if pattern.search(l)]
        if hits:
            findings.append((title, fix))
            break  # one log-level finding is enough; exit code covers the rest
    return findings


def verdict(data):
    if data["running"]:
        return ("🟢 Alive", "The container is running. Autopsies are for the dead — but here is its current health anyway.")
    base = EXIT_CODES.get(data["exit_code"], ("❓ Unknown exit code %s" % data["exit_code"], "Not a standard exit code. Check the app's own exit conventions."))
    return base


def render_markdown(data, findings, cause, fix):
    lines = [
        "## ⚰️ Autopsy report — `%s`" % data["container"],
        "",
        "| Evidence | Value |",
        "|---|---|",
        "| Image | `%s` |" % data["image"],
        "| Status | %s |" % data["status"],
        "| Exit code | **%s** |" % data["exit_code"],
        "| OOMKilled | %s |" % data["oom_killed"],
        "| Restarts | %s |" % data["restart_count"],
        "| Uptime before death | %s |" % (data["uptime"] or "n/a"),
        "| Finished at | %s |" % ((data["finished_at"] or "")[:19] or "n/a"),
        "",
        "### 🕯️ Cause of death",
        "**%s** — %s" % (cause, fix),
    ]
    if findings:
        lines += ["", "### 🔎 Contributing evidence"]
        for title, ffix in findings:
            lines += ["- **%s** — %s" % (title, ffix)]
    if data["logs"]:
        lines += ["", "### 📜 Last log lines", "```", *data["logs"], "```"]
    return "\n".join(lines) + "\n"


def share_block(data, cause):
    emoji = "🟢" if data["running"] else "🔴"
    label = ("running" if data["running"] else "exit-%s" % data["exit_code"])
    color = "00A884" if data["running"] else "D93F3F"
    return (
        "### %s — %s %s\n"
        "![autopsy badge](https://img.shields.io/badge/container_autopsy-%s-%s?style=flat-square&logo=docker)\n\n"
        "Forensics by [container-autopsy](https://github.com/fernedy/container-autopsy) — "
        "know WHY your container died, not just THAT it died.\n"
        % (data["container"], cause.split(" ")[0], emoji, label, color)
    )


def ai_diagnose(report):
    """Optional: ask a local agent CLI (opencode) to enrich the report."""
    exe = "opencode"
    if not any(os.access(os.path.join(p, exe), os.X_OK) for p in os.environ.get("PATH", "").split(os.pathsep)):
        return "_[ai] opencode not found in PATH — skipping AI diagnosis (everything else works without it)._"
    prompt = ("You are an SRE. Given this container autopsy report, add a short section "
              "'### 🤖 AI second opinion' with: the most likely root cause, one command to "
              "confirm it, and one command to fix it. Be concise.\n\n" + report)
    ok, out, err = sh([exe, "run", prompt])
    if not ok:
        return "_[ai] local agent failed: %s_" % (err.strip() or "unknown error")
    return out.strip()


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="container-autopsy",
        description="Find out WHY your container died, not just THAT it died.")
    ap.add_argument("container", help="container name or id to autopsy (dead or alive)")
    ap.add_argument("--tail", type=int, default=40, help="number of log lines to collect (default 40)")
    ap.add_argument("--json", action="store_true", help="output raw evidence as JSON")
    ap.add_argument("--ai", action="store_true", help="add an AI second opinion via your local agent CLI (opencode)")
    ap.add_argument("--share", action="store_true", help="print a shareable markdown block with a badge")
    ap.add_argument("--version", action="version", version="%(prog)s " + __version__)
    args = ap.parse_args(argv)

    data = collect(args.container, args.tail)

    if args.json:
        print(json.dumps(data, indent=2))
        return 0

    cause, fix = verdict(data)
    findings = analyze(data)
    report = render_markdown(data, findings, cause, fix)

    if args.ai:
        report += "\n" + ai_diagnose(report) + "\n"
    print(report)
    if args.share:
        print(share_block(data, cause))
    return 0


if __name__ == "__main__":
    sys.exit(main())
