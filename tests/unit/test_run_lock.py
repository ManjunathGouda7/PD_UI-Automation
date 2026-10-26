"""Unit tests for the one-run-at-a-time tester lock."""
from dataclasses import asdict
import json
import os
import socket

import pytest

from Scripts.Helpers import run_lock


def _write_holder(path, pid, host=None):
    holder = run_lock.LockInfo(pid=pid, host=host or socket.gethostname(), user="someone",
                               started="2026-01-01 00:00:00", command="pytest")
    path.write_text(json.dumps(asdict(holder)), encoding="utf-8")


def test_acquire_and_release(tmp_path):
    lock = tmp_path / "x.lock"
    me = run_lock.acquire("pytest -m smoke", path=lock)
    assert me.pid == os.getpid() and lock.exists()
    run_lock.release(path=lock)
    assert not lock.exists()


def test_live_holder_blocks_second_run(tmp_path):
    lock = tmp_path / "x.lock"
    _write_holder(lock, os.getppid())  # parent process is alive
    with pytest.raises(run_lock.RunLockedError, match="Another test run is using the tester"):
        run_lock.acquire("pytest", path=lock)


def test_stale_lock_of_dead_process_is_taken_over(tmp_path):
    lock = tmp_path / "x.lock"
    _write_holder(lock, 999_999)  # no such process
    me = run_lock.acquire("pytest", path=lock)
    assert run_lock.read_holder(lock).pid == me.pid


def test_lock_from_another_pc_is_respected(tmp_path):
    lock = tmp_path / "x.lock"
    _write_holder(lock, 999_999, host="OTHER-BENCH-PC")  # cannot check a remote PID: keep it
    with pytest.raises(run_lock.RunLockedError):
        run_lock.acquire("pytest", path=lock)


def test_corrupt_lock_file_is_replaced(tmp_path):
    lock = tmp_path / "x.lock"
    lock.write_text("{not json", encoding="utf-8")
    assert run_lock.acquire("pytest", path=lock).pid == os.getpid()


def test_release_does_not_remove_someone_elses_lock(tmp_path):
    lock = tmp_path / "x.lock"
    _write_holder(lock, os.getppid())
    run_lock.release(path=lock)
    assert lock.exists()
