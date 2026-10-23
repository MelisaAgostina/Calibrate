# Calibrate

Lab equipment booking system (console, Python 3, stdlib `sqlite3`, `argparse`, `pytest`).
Full plan and decisions: `docs/PLAN.md`. The spec lives in `README.md` section 1.

## Rules
- Spec first: do not write code for behavior that is not in the spec. If the spec is ambiguous, ask; spec changes go in their own commit with the reason in the message.
- Tests before code: write the failing test, then the implementation.
- Intervals are half-open `[start, end)`; 10:00-11:00 and 11:00-12:00 do not clash.
- ONE overlap function in `domain.py` (`a.start < b.end and b.start < a.end`, same unit, ACTIVE only). Booking and availability both call it.
- Dates are `YYYY-MM-DD HH:MM` in one fixed lab zone; the clock is injectable so tests are deterministic.
- No new dependencies without asking.
- No secrets, tokens, or real student data; use fictitious requesters only.
- Never commit; the human commits.
- After every task, update `PROGRESS.md` (done / decisions / next).

## Layout
`src/calibrate/` (`domain.py`, `repository.py`, `service.py`, `cli.py`), `tests/`, `docs/`.

## Commands
- Tests: `python -m pytest`
