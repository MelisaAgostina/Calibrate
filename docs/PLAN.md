# Calibrate – Final Plan

Individual assignment "Challenge IA": lab equipment booking system built with a coding agent (Claude Code).
Graded on repo EVIDENCE, not on README claims. Weights: Spec 25 / Agent 25 / Function+tests 30 / Traceability 20.

## 1. Decisions (all [assumption] unless stated)
| Topic | Decision | Why |
|---|---|---|
| Language | Python 3, stdlib `sqlite3`, `argparse`, `pytest` | Minimal dependencies, easy to reproduce |
| Interface | Console (CLI) | Allowed by the assignment |
| Storage | SQLite file `data/calibrate.db` (ignored by git) | One file, survives restarts |
| Time zone | One fixed lab zone (America/Argentina/Buenos_Aires), no conversion | Simplicity |
| Date format | `YYYY-MM-DD HH:MM` | Unambiguous, sortable |
| Intervals | Half-open [start, end) | 10-11 and 11-12 do not clash |
| Past dates | Rejected; clock is injectable for tests | Deterministic tests |
| Max duration | 8 h | Avoid absurd bookings |
| Max anticipation | 90 days | Same |
| Cancel twice / unknown ID | Clear error | No silent success |
| README language | Spanish [assumption: the course is in Spanish] | Matches the grader |
| Concurrency | Overlap check + insert inside one `BEGIN IMMEDIATE` transaction | Two simultaneous `book` runs cannot both pass the check; otherwise document as a limitation |
| Date storage | `start`/`end` stored as `YYYY-MM-DD HH:MM` text | Sorts correctly in SQL |
| Status values | `status` restricted by a `CHECK` constraint (`ACTIVE`, `CANCELLED`) | Invalid states impossible at DB level |
| `reset --yes` | Deletes all reservations (active and cancelled), then re-seeds missing units from `inventory.json`; never deletes units | DB is usable right after reset; reuses `init` seeding |
| Unit seeding | `init` is idempotent: adds units missing from the DB, never duplicates | Re-running is safe |

## 2. Architecture
CLI -> Service (book / cancel / availability) -> Domain rules (pure functions) ; Service -> Repository -> SQLite
- ONE overlap function: `a.start < b.end and b.start < a.end`, same unit, ACTIVE only.
- Booking AND availability both call it (the assignment demands the same rules).
- Tables: `units(id, name)`; `reservations(id, unit_id, requester, start, end, status, created_at, cancelled_at)`.
- Units seeded from `inventory.json`: MIC-01, MIC-02, OSC-01, MUL-01, FUE-01.
- Commands: `init`, `reset --yes` (warns: deletes reservations), `units`, `availability`, `book`, `cancel`, `list`.

## 3. Required tests
- [X] Valid creation
- [X] Overlap rejected (10:30-11:30 vs 10:00-11:00)
- [X] Consecutive limits allowed (11:00-12:00)
- [X] MIC-02 bookable while MIC-01 is busy
- [X] Invalid inputs: unknown unit, "   " requester, 30 Feb, 25:00, start >= end, past date, too long, too far ahead
- [X] Cancel keeps record and frees the slot
- [X] Availability agrees with booking rules
- [X] Persistence: new service on the same DB still has active + cancelled reservations
- [X] Persistence via two separate CLI runs (manual or automatic procedure with expected vs observed)
- [X] Boundary: booking of exactly 8 h accepted, 8 h 1 min rejected
- [X] Boundary: start exactly 90 days ahead accepted, beyond rejected
- [X] Cancelling an already-cancelled reservation -> clear error, record unchanged
- [X] Cancelled slot can be rebooked (same unit, same times)
- [X] `init` run twice does not duplicate units; unit in `inventory.json` but missing in DB gets seeded
- [X] `reset` without `--yes` does nothing; with `--yes` deletes reservations as specified
- [X] Concurrency: second booking of the same slot is rejected even if attempted right after the first (transaction)

## 4. Agent setup (Claude Code)
- `CLAUDE.md` in repo root: spec first; tests before code; half-open intervals; no new dependencies without asking; no secrets or real student data; after every task update `PROGRESS.md` (done / decisions / next).
- `.claude/settings.json`: auto-allow `pytest` and read-only git; ask before commits, deletes, installs.
- Record exactly as seen: Claude Code version and model ID (write "not visible" if it is not shown). Do not guess.
- Record: context given, context excluded, approvals actually granted, what was reviewed before accepting.
- Specific adaptation with evidence of use: the `PROGRESS.md` rule (its git history is the proof).
- Keep real evidence in `docs/evidence/`: commands, versions, outputs, failures included. Separate "agent reported" from "I ran it".

## 5. Build order (each step = at least one commit)
- [X] 0. `git init`, `.gitignore`, `CLAUDE.md`, settings, `PROGRESS.md`, README skeleton
- [X] 1. Write the spec (README section 1) BEFORE any code -> commit "Initial spec"
- [X] 2. Failing tests (red)
- [X] 3. Domain rules (green)
- [X] 4. SQLite repository + persistence
- [X] 5. CLI + example input/output
- [X] 6. Run everything for real; save results in `docs/evidence/`
- [X] 7. Finish README, episodes, secrets check, repo access check.

Spec changes later = separate commits with the reason in the message (that is the "recoverable evolution").

## 6. Three delegation episodes (must be REAL; do not invent failures)
Format for each: goal + requirement -> context + instruction excerpt -> agent action/result -> human decision (accept / fix / reject) + reason -> link to commit/test/file.
Candidates:
1. Spec drafting: agent drafts acceptance criteria, human tightens ambiguous rules.
2. Overlap logic, tests-first: human reviews boundary tests.
3. Persistence + cancellation: human verifies the restart procedure.
Write them in `docs/episodes.md` right after each happens, not at the end.

## 7. Repo layout
```
README.md  CLAUDE.md  PROGRESS.md  requirements.txt  inventory.json  .gitignore
src/calibrate/  domain.py  repository.py  service.py  cli.py
tests/  test_domain.py  test_service.py  test_persistence.py
docs/  PLAN.md  decisions.md  episodes.md  evidence/
.claude/settings.json
```

## 8. Final checklist before sending
- [ ] Fresh clone: `pip install -r requirements.txt && pytest` passes without the model account
- [ ] README has the four sections: Spec / Solution / Agent preparation / Decisions + episodes
- [ ] README states where data lives and that `reset` deletes reservations; limitations listed
- [ ] No secrets, tokens, full chat transcripts, or real student names (fictitious requesters only)
- [ ] Repo accessible to the grader (public, or access shared); branch + commit noted
- [ ] Email to dgaifirst@gmail.com, subject «Challenge IA» (and Excel link if required)

## 9. Revisit if it grows
Concurrent users, multi-site time zones, authentication, inventory admin, Postgres.
