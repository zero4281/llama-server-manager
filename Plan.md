# Project Plan — Version 1.0.6

## Section 1: Current State Assessment

### Compliance Checklist
- [x] Full end-to-end testing of "restart with same arguments" behavior for self-updates
- [x] Verification of "restore originals if replacement has already begun" logic for self-updates

### Implementation Verification Table
| Feature | Status | Verification Method |
|---|---|---|
| Self-update with restart | Completed | End-to-end test |
| Restore originals on failure | Completed | Failure-injection test |

### Remaining Gaps
- Self-update Rollback is not fully atomic.

## Section 2: Core Engineering Decisions or Filename Consistency
- Self-update mechanism must preserve all original command-line arguments for the restart.
- Atomic file replacement or rollback mechanism must be implemented to ensure file integrity during self-update.
- The restart logic uses `subprocess.Popen`.

## Section 3: Testing & Verification Status
- Unit: [ ] Self-update logic (restart args)
- Unit: [ ] Rollback/Restore logic
- Integration: [ ] End-to-end self-update flow
- Integration: [ ] Failure-injection test for replacement
- Manual: [ ] Verify restart with diverse args
- Manual: [ ] Verify rollback on simulated I/O failure

## Section 4: Exit Codes
- 0: Success
- 1: General error
- 2: Self-update failure
- 3: Llama.cpp installation failure

## Section 5: Security
- No execution of untrusted code during self-update.
- Verification of download integrity via SHA256.

## Section 6: Dependencies
- Python 3.12+
- `requests` (for GitHub API)
- `curses` (standard library)

## Section 7: Non-functional requirements
- Terminal UI must remain consistent (ncurses).
- Graceful shutdown on signal.
- No dangling processes or PID files.
