# PROGRESS

## Done
- Step 0: repo skeleton (`.gitignore`, `CLAUDE.md`, `.claude/settings.json`, `PROGRESS.md`, README skeleton).
- Step 1: spec written in `README.md` section 1 (rules R1-R15, commands, errors, storage, 10 acceptance criteria).
- Step 2: failing tests (red) in `tests/test_domain.py`, `test_service.py`, `test_persistence.py`; `requirements.txt`, `pytest.ini`, `inventory.json`. `pytest` run: 3 collection errors (`No module named 'calibrate'`), as expected before any code.
- Step 3: `src/calibrate/domain.py` (green): `tests/test_domain.py` 25 passed. Service and persistence tests still red (no service/repository yet).

## Decisions
- See `docs/PLAN.md` section 1. `reset --yes` deletes all reservations and re-seeds missing units; it never deletes units.
- `availability` without `--unit` lists free units for the interval; with `--unit` it reports blockers.
- Errors: message on stderr, non-zero exit code, DB unchanged.
- Test-defined API: `domain` (`ValidationError`, `overlaps`, `parse_datetime`, `validate_interval(start, end, now)`, `validate_requester`); `CalibrateService(db_path, inventory, now=callable)` with `init`, `reset(confirm)`, `units`, `book`, `cancel`, `list(unit=None, include_cancelled=False)`, `blocking(unit, start, end)`, `free_units(start, end)`.
- CLI reads the DB path from env `CALIBRATE_DB` (not yet in the spec).

## Next
- Add `CALIBRATE_DB` to the spec (separate spec commit).
- Step 4: SQLite repository + service (`repository.py`, `service.py`) to turn `test_service.py` and the service part of `test_persistence.py` green.
