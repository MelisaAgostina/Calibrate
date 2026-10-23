# PROGRESS

## Done
- Step 0: repo skeleton (`.gitignore`, `CLAUDE.md`, `.claude/settings.json`, `PROGRESS.md`, README skeleton).
- Step 1: spec written in `README.md` section 1 (rules R1-R15, commands, errors, storage, 10 acceptance criteria).
- Step 2: failing tests (red) in `tests/test_domain.py`, `test_service.py`, `test_persistence.py`; `requirements.txt`, `pytest.ini`, `inventory.json`. `pytest` run: 3 collection errors (`No module named 'calibrate'`), as expected before any code.
- Step 3: `src/calibrate/domain.py` (green): `tests/test_domain.py` 25 passed. Service and persistence tests still red (no service/repository yet).
- Step 4: `repository.py` + `service.py` (green). Full suite: 63 passed, 2 failed (the two CLI tests: `No module named calibrate.cli`, expected until step 5).
- Step 5: `src/calibrate/cli.py` (green). Full suite: 65 passed. Manual demo session run (init, units, book ok/clash/consecutive, availability, cancel twice, list, list --all, reset without --yes); output not yet saved to `docs/evidence/`.
- Step 6: evidence saved in `docs/evidence/` (`versions.txt`, `pytest-output.txt` 65 passed, `restart-procedure-output.txt`, `README.md` with expected vs observed, 13/13 match). Claude Code version from `claude --version`: 2.1.283.
- Evidence updated with the human re-run (`docs/evidence/human-run-melisa.txt`, 65 passed, CLI procedure matched; one error message truncated by the paste). README sections 2-3 written; `CALIBRATE_DB` added to spec 1.6 (spec change: commit separately).

## Decisions
- See `docs/PLAN.md` section 1. `reset --yes` deletes all reservations and re-seeds missing units; it never deletes units.
- `availability` without `--unit` lists free units for the interval; with `--unit` it reports blockers.
- Errors: message on stderr, non-zero exit code, DB unchanged.
- Test-defined API: `domain` (`ValidationError`, `overlaps`, `parse_datetime`, `validate_interval(start, end, now)`, `validate_requester`); `CalibrateService(db_path, inventory, now=callable)` with `init`, `reset(confirm)`, `units`, `book`, `cancel`, `list(unit=None, include_cancelled=False)`, `blocking(unit, start, end)`, `free_units(start, end)`.
- Overlap is checked in Python with `domain.overlaps` over the unit's active reservations (not in SQL), so there is a single overlap function; the check + insert run in one `BEGIN IMMEDIATE` transaction.
- CLI reads the DB path from env `CALIBRATE_DB` (not yet in the spec).

## Next
- Add `CALIBRATE_DB` to the spec (separate spec commit).
- Step 7: finish README section 3 (approvals granted, what was reviewed) and 4 (episodes), write `docs/episodes.md` (3 real episodes) and `docs/decisions.md`, add `CALIBRATE_DB` to the spec (separate commit), secrets check, fresh-clone check, human re-runs the evidence commands, repo access, send email.
