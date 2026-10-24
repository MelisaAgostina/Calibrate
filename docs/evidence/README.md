# Evidence (step 6)

Raw outputs saved as produced, nothing edited:

| File | What it is |
|---|---|
| `versions.txt` | Python, pytest, git, Claude Code versions, OS, date |
| `pytest-output.txt` | `python -m pytest -v`: 65 passed, exit 0 |
| `restart-procedure-output.txt` | Each CLI command in its own process; DB survives between them |
| `human-run-melisa.txt` | Same procedure re-run by hand in PowerShell by the author (pasted terminal session) |

## Who ran what
- **Executed by the Claude Code agent** in the working session (commands issued through its Bash tool, outputs copied verbatim into `versions.txt`, `pytest-output.txt` and `restart-procedure-output.txt`). Bash on Windows, Python 3.10.11.
- **Re-run by the human** (Melisa) in PowerShell on 2026-10-23, saved in `human-run-melisa.txt`: `python -m pytest -v` gave 65 passed in 4.87 s, and the CLI procedure gave the same results as the agent run (details below). This is the "I ran it" evidence; the agent files are "agent reported".
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

## Human re-run (`human-run-melisa.txt`)
Same 13 steps plus `reset --yes` and a final `list --all`. Observed matches expected, with these notes:
- Steps 1-13 gave the same outcomes as the agent run (reservation IDs #1, #2, #3; clash rejected; second `cancel --id 2` rejected; `reset` without `--yes` refused). Dates and cancellation timestamps differ only by run time.
- `reset --yes` printed `Reservas borradas. Unidades restauradas desde inventory.json.` and the following `list --all` printed `No hay reservas.` This covers the confirmed reset by hand.
- **Truncated line:** the second `cancel --id 2` appears as `Error: La reserva 2 ya estaba` followed directly by the next command (`...ya estabapython -m calibrate.cli reset`). The file is the terminal text exactly as PowerShell displayed it -> terminal rendering

## Not covered by this evidence
- The CLI tests use the real clock (today + 10 days); they will keep passing as long as the dates stay within the 90-day window.
- No fresh-clone run yet (step 7 checklist).

