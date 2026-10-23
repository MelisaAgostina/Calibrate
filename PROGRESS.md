# PROGRESS

## Done
- Step 0: repo skeleton (`.gitignore`, `CLAUDE.md`, `.claude/settings.json`, `PROGRESS.md`, README skeleton).
- Step 1: spec written in `README.md` section 1 (rules R1-R15, commands, errors, storage, 10 acceptance criteria).

## Decisions
- See `docs/PLAN.md` section 1. `reset --yes` deletes all reservations and re-seeds missing units; it never deletes units.
- `availability` without `--unit` lists free units for the interval; with `--unit` it reports blockers.
- Errors: message on stderr, non-zero exit code, DB unchanged.

## Next
- Step 2: failing tests (red), starting with `tests/test_domain.py`. Needs `requirements.txt` (pytest).
