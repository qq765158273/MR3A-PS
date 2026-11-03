"""Connect Maa's AgentClient to the existing MR3A AgentServer entry point."""

from pathlib import Path
import subprocess
import sys

from maa.agent_client import AgentClient


class MR3AAgent:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.client = None
        self.process = None
        self.log_file = None

    def __enter__(self):
        self.client = AgentClient.create_tcp()
        self.client.set_timeout(20000)
        identifier = self.client.identifier
        if not identifier:
            raise RuntimeError("Failed to create MR3A AgentClient identifier")
        log_path = self.project_root / "psauto/debug/mr3a-agent.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_file = log_path.open("ab")
        try:
            self.process = subprocess.Popen(
                [sys.executable, "-c", "from agent.main import agent; agent()", identifier],
                cwd=self.project_root,
                stdin=subprocess.DEVNULL,
                stdout=self.log_file,
                stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except BaseException:
            self.log_file.close()
            raise
        return self.client

    def __exit__(self, exc_type, exc, traceback):
        if self.client is not None and self.client.connected:
            self.client.disconnect()
        if self.process is not None:
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
        if self.log_file is not None:
            self.log_file.close()
