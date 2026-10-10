"""Tests for container-autopsy. All docker interactions are mocked — no Docker needed."""

import json
import unittest
from unittest import mock

import container_autopsy as ca


def fake_inspect(exit_code=137, oom=True, running=False, restarts=0, name="my-app"):
    return [{
        "Name": "/" + name,
        "Config": {"Image": "python:3.12-slim"},
        "State": {
            "Status": "running" if running else "exited",
            "Running": running,
            "ExitCode": exit_code,
            "OOMKilled": oom,
            "Error": "",
            "StartedAt": "2026-09-13T10:00:00.000000000Z",
            "FinishedAt": "2026-09-13T10:05:30.000000000Z" if not running else "0001-01-01T00:00:00Z",
        },
        "RestartCount": restarts,
    }]


class FakeRunner:
    """Patch target for ca.sh that replays canned docker responses."""

    def __init__(self, inspect, logs=""):
        self.inspect = inspect
        self.logs = logs
        self.calls = []

    def __call__(self, args):
        self.calls.append(args)
        if args[:2] == ["docker", "inspect"]:
            return True, json.dumps(self.inspect), ""
        if args[:2] == ["docker", "logs"]:
            return True, self.logs, ""
        return True, "", ""


class TestCollect(unittest.TestCase):
    def test_collect_parses_state(self):
        fr = FakeRunner(fake_inspect(exit_code=137, oom=True, restarts=2), logs="2026-09-13T10:05:29 boom\n")
        with mock.patch.object(ca, "sh", fr):
            data = ca.collect("my-app", 40)
        self.assertEqual(data["container"], "my-app")
        self.assertEqual(data["exit_code"], 137)
        self.assertTrue(data["oom_killed"])
        self.assertEqual(data["restart_count"], 2)
        self.assertEqual(data["uptime"], "0:05:30")
        self.assertIn("boom", data["logs"][0])

    def test_collect_running_container_has_no_finished_at(self):
        fr = FakeRunner(fake_inspect(running=True))
        with mock.patch.object(ca, "sh", fr):
            data = ca.collect("my-app", 10)
        self.assertIsNone(data["finished_at"])
        self.assertIsNone(data["uptime"])


class TestAnalyze(unittest.TestCase):
    def test_oom_produces_finding(self):
        findings = ca.analyze({"oom_killed": True, "restart_count": 0, "logs": []})
        self.assertTrue(any("OOMKilled" in t for t, _ in findings))

    def test_restart_storm_detected(self):
        findings = ca.analyze({"oom_killed": False, "restart_count": 5, "logs": []})
        self.assertTrue(any("Restart storm" in t for t, _ in findings))

    def test_log_pattern_memory(self):
        findings = ca.analyze({"oom_killed": False, "restart_count": 0,
                               "logs": ["ERROR: Cannot allocate memory"]})
        self.assertTrue(any("Out-of-memory" in t for t, _ in findings))

    def test_log_pattern_dependency(self):
        findings = ca.analyze({"oom_killed": False, "restart_count": 0,
                               "logs": ["pg_isready: connection refused"]})
        self.assertTrue(any("refused" in t for t, _ in findings))

    def test_no_findings_on_clean_exit(self):
        findings = ca.analyze({"oom_killed": False, "restart_count": 0, "logs": []})
        self.assertEqual(findings, [])


class TestVerdict(unittest.TestCase):
    def test_known_exit_code(self):
        cause, fix = ca.verdict({"running": False, "exit_code": 137})
        self.assertIn("SIGKILL", cause)

    def test_running_container(self):
        cause, _ = ca.verdict({"running": True, "exit_code": 0})
        self.assertIn("Alive", cause)

    def test_unknown_exit_code(self):
        cause, _ = ca.verdict({"running": False, "exit_code": 42})
        self.assertIn("42", cause)


class TestRender(unittest.TestCase):
    def test_markdown_report_contains_sections(self):
        data = ca.collect.__wrapped__ if hasattr(ca.collect, "__wrapped__") else None
        evidence = {"container": "api", "image": "api:1", "status": "exited", "exit_code": 1,
                    "oom_killed": False, "restart_count": 1, "uptime": "0:01:00",
                    "finished_at": "2026-09-13T10:01:00Z", "logs": ["Traceback (most recent call last)"]}
        findings = ca.analyze(evidence)
        report = ca.render_markdown(evidence, findings, "💥 Application error", "fix it")
        self.assertIn("Autopsy report", report)
        self.assertIn("Cause of death", report)
        self.assertIn("Traceback", report)
        self.assertIn("api:1", report)

    def test_share_block_contains_badge(self):
        block = ca.share_block({"container": "api", "running": False, "exit_code": 1}, "💥 Application error")
        self.assertIn("img.shields.io", block)
        self.assertIn("exit-1", block)
        self.assertIn("container-autopsy", block)


class TestCli(unittest.TestCase):
    def test_json_output(self):
        fr = FakeRunner(fake_inspect())
        with mock.patch.object(ca, "sh", fr):
            rc = ca.main(["my-app", "--json"])
        self.assertEqual(rc, 0)

    def test_version(self):
        with self.assertRaises(SystemExit) as cm:
            ca.main(["--version"])
        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
