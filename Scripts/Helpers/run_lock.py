"""
Cross-process run lock: only one test run at a time may drive the (single, shared) tester.

The lock is a JSON file next to the reports. It records the owner's PID, host, user and start time;
a lock whose process no longer exists is treated as stale and taken over. API-only and mock runs
do not touch the tester and therefore do not take the lock.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import getpass
import json
import os
from pathlib import Path
import socket
import time

LOCK_FILE = Path(__file__).resolve().parent.parent.parent / "Reports" / ".tester_run.lock"


@dataclass
class LockInfo:
    pid: int
    host: str
    user: str
    started: str
    command: str


class RunLockedError(RuntimeError):
    def __init__(self, holder: LockInfo):
        super().__init__(
            f"Another test run is using the tester: PID {holder.pid} by {holder.user} on {holder.host} "
            f"since {holder.started} ({holder.command}). Wait for it to finish, or delete "
            f"{LOCK_FILE} if that run is gone."
        )
        self.holder = holder


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        exit_code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return exit_code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def read_holder(path: Path = LOCK_FILE) -> LockInfo | None:
    try:
        return LockInfo(**json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError):
        return None


def is_active(holder: LockInfo) -> bool:
    """False only when the holder is provably gone (a dead process on this PC)."""
    return holder.host != socket.gethostname() or _pid_alive(holder.pid)


def acquire(command: str, path: Path = LOCK_FILE) -> LockInfo:
    """Takes the lock or raises RunLockedError. Stale locks (dead or local-but-gone PID) are replaced."""
    path.parent.mkdir(parents=True, exist_ok=True)
    me = LockInfo(pid=os.getpid(), host=socket.gethostname(), user=getpass.getuser(),
                  started=time.strftime("%Y-%m-%d %H:%M:%S"), command=command[:200])
    for _ in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            holder = read_holder(path)
            if holder and not is_active(holder):
                path.unlink(missing_ok=True)  # stale lock of a crashed run on this PC
                continue
            if holder is None:
                path.unlink(missing_ok=True)  # unreadable / half-written lock
                continue
            raise RunLockedError(holder) from None
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(asdict(me), f)
        return me
    raise RunLockedError(read_holder(path) or me)


def release(path: Path = LOCK_FILE) -> None:
    holder = read_holder(path)
    if holder and holder.pid == os.getpid() and holder.host == socket.gethostname():
        path.unlink(missing_ok=True)
