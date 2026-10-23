# Evidence (step 6)

Raw outputs saved as produced, nothing edited:

| File | What it is |
|---|---|
| `versions.txt` | Python, pytest, git, Claude Code versions, OS, date |
| `pytest-output.txt` | `python -m pytest -v`: 65 passed, exit 0 |
| `restart-procedure-output.txt` | Each CLI command in its own process; DB survives between them |

## Who ran what
- **Executed by the Claude Code agent** in the working session (commands issued through its Bash tool, outputs copied verbatim into the files above). The human has **not yet** re-run them independently; do that before the final submission (see PROGRESS.md, step 7).
- **Agent-reported identity:** the session states the model as `claude-sonnet-5-5`. This comes from the session context, not from a command.
- **Command-reported:** `claude --version` printed `2.1.283 (Claude Code)` (see `versions.txt`).

## Restart procedure: expected vs observed
Setup: fresh temporary DB, dates = today + 10 days, every command a separate process.

| # | Command | Expected | Observed |
|---|---|---|---|
| 1 | `init` | exit 0 | exit 0 |
| 2 | `book MIC-01 Ana Perez 10:00-11:00` | reservation #1 ACTIVE | #1 ACTIVE |
| 3 | `book MIC-02 Luis Gomez 10:00-11:00` | reservation #2 ACTIVE (other unit) | #2 ACTIVE |
| 4 | `cancel --id 2` | #2 CANCELLED | #2 CANCELLED |
| 5 | *(new processes)* `list` | only #1 | only #1 |
| 6 | `list --all` | #1 ACTIVE and #2 CANCELLED | both, #2 with `cancelada:` timestamp |
| 7 | `availability MIC-01 10:30-11:30` | OCUPADA, blocked by #1 | OCUPADA, #1 listed |
| 8 | `availability MIC-02 10:30-11:30` | LIBRE (#2 cancelled) | LIBRE |
| 9 | `book MIC-01 10:30-11:30` | rejected, exit != 0 | `Error: ... ya esta reservada ...`, exit 1 |
| 10 | `book MIC-02 10:00-11:00` (slot of cancelled #2) | accepted | #3 ACTIVE |
| 11 | `cancel --id 2` again | error | `La reserva 2 ya estaba cancelada.`, exit 1 |
| 12 | `reset` (no `--yes`) | refuses, data kept | refused, exit 1 |
| 13 | `list` | #1 and #3 | #1 and #3 |

Result: observed matches expected in all 13 steps. Active and cancelled reservations persist across separate processes, cancelled slots can be rebooked, and `reset` without `--yes` deletes nothing.

## Not covered by this evidence
- `reset --yes` is covered only by the automated test `test_cli_reset_requires_confirmation`, not by the manual procedure.
- The CLI tests use the real clock (today + 10 days); they will keep passing as long as the dates stay within the 90-day window.
- No fresh-clone run yet (step 7 checklist).
