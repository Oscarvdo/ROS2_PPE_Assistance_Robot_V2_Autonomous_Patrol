from __future__ import annotations

import queue
import subprocess
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class AlertResult:
    message: str
    succeeded: bool
    detail: str = ""


class VoiceAlert(ABC):
    @abstractmethod
    def submit(self, message: str) -> bool:
        raise NotImplementedError

    def close(self) -> None:
        pass


class MockVoiceAlert(VoiceAlert):
    def __init__(self) -> None:
        self.messages: list[str] = []

    def submit(self, message: str) -> bool:
        self.messages.append(message)
        return True


class EspeakVoiceAlert(VoiceAlert):
    """Single-worker, bounded asynchronous voice queue."""

    def __init__(self, command: str = "espeak-ng", queue_size: int = 4) -> None:
        self.command = command
        self.results: list[AlertResult] = []
        self._queue: queue.Queue[str | None] = queue.Queue(maxsize=queue_size)
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def submit(self, message: str) -> bool:
        try:
            self._queue.put_nowait(message)
            return True
        except queue.Full:
            self.results.append(AlertResult(message, False, "voice queue full"))
            return False

    def _run(self) -> None:
        while True:
            message = self._queue.get()
            if message is None:
                self._queue.task_done()
                return
            try:
                completed = subprocess.run(
                    [self.command, message],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                self.results.append(AlertResult(
                    message,
                    completed.returncode == 0,
                    completed.stderr.strip(),
                ))
            except (OSError, subprocess.TimeoutExpired) as exc:
                self.results.append(AlertResult(message, False, str(exc)))
            finally:
                self._queue.task_done()

    def close(self) -> None:
        self._queue.put(None)
        self._worker.join(timeout=2)
