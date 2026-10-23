import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from calibrate.service import CalibrateService

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2030, 6, 3, 9, 0)
INVENTORY = [
    {"id": "MIC-01", "name": "Microscopio 1"},
    {"id": "MIC-02", "name": "Microscopio 2"},
]


def test_new_service_on_same_db_sees_active_and_cancelled(tmp_path):
    db = tmp_path / "calibrate.db"
    first = CalibrateService(db, INVENTORY, now=lambda: NOW)
    first.init()
    keep = first.book("MIC-01", "Ana Perez", "2030-06-10 10:00", "2030-06-10 11:00")
    drop = first.book("MIC-02", "Luis Gomez", "2030-06-10 10:00", "2030-06-10 11:00")
    first.cancel(drop.id)

    second = CalibrateService(db, INVENTORY, now=lambda: NOW)   # simulated restart
    second.init()
    active = second.list()
    everything = second.list(include_cancelled=True)

    assert [r.id for r in active] == [keep.id]
    assert {r.id: r.status for r in everything} == {keep.id: "ACTIVE", drop.id: "CANCELLED"}


def test_booked_slot_still_blocks_after_restart(tmp_path):
    db = tmp_path / "calibrate.db"
    first = CalibrateService(db, INVENTORY, now=lambda: NOW)
    first.init()
    first.book("MIC-01", "Ana Perez", "2030-06-10 10:00", "2030-06-10 11:00")

    second = CalibrateService(db, INVENTORY, now=lambda: NOW)
    assert second.blocking("MIC-01", "2030-06-10 10:30", "2030-06-10 11:30") != []


# --- Two separate CLI processes (real clock, so dates are relative to today) ---

def run_cli(db, *args):
    env = dict(os.environ, CALIBRATE_DB=str(db), PYTHONPATH=str(ROOT / "src"))
    return subprocess.run(
        [sys.executable, "-m", "calibrate.cli", *args],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )


def test_persistence_across_separate_cli_runs(tmp_path):
    db = tmp_path / "cli.db"
    day = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    start, end = f"{day} 10:00", f"{day} 11:00"

    assert run_cli(db, "init").returncode == 0

    booked = run_cli(db, "book", "--unit", "MIC-01", "--requester", "Ana Perez",
                     "--start", start, "--end", end)
    assert booked.returncode == 0, booked.stderr

    listed = run_cli(db, "list")                      # a different process
    assert listed.returncode == 0
    assert "MIC-01" in listed.stdout and "Ana Perez" in listed.stdout

    clash = run_cli(db, "book", "--unit", "MIC-01", "--requester", "Luis Gomez",
                    "--start", f"{day} 10:30", "--end", f"{day} 11:30")
    assert clash.returncode != 0
    assert clash.stderr.strip() != ""

    assert run_cli(db, "cancel", "--id", "1").returncode == 0

    active = run_cli(db, "list")
    assert "Ana Perez" not in active.stdout
    everything = run_cli(db, "list", "--all")
    assert "Ana Perez" in everything.stdout and "CANCELLED" in everything.stdout

    assert run_cli(db, "cancel", "--id", "1").returncode != 0   # already cancelled


def test_cli_reset_requires_confirmation(tmp_path):
    db = tmp_path / "cli.db"
    day = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    run_cli(db, "init")
    run_cli(db, "book", "--unit", "MIC-01", "--requester", "Ana Perez",
            "--start", f"{day} 10:00", "--end", f"{day} 11:00")

    run_cli(db, "reset")                              # no --yes: nothing happens
    assert "Ana Perez" in run_cli(db, "list").stdout

    assert run_cli(db, "reset", "--yes").returncode == 0
    assert "Ana Perez" not in run_cli(db, "list", "--all").stdout
