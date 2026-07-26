# Update

## Summary
The codebase requires alignment with Requirements.md. Specifically, the startup sequence in `main.py` needs reordering, and the install workflow needs to include a "Compute Backend selection" screen.

## Implemented but Non-Required: Features to Remove
- None. The `wrapper_config.py` and `llama_wrapper/` files identified in the Plan for removal are already absent from the repository.

## Compliance Table
| Requirement / Plan Section | Status | Notes |
| --- | --- | --- |
| Requirement 5.4 (Startup Sequence) | Incomplete | Initialization order is incorrect |
| Requirement 7.3.3 (Install Workflow) | Incomplete | Compute Backend selection screen missing |
| Requirement 5.3.3 (Self-Update Restart) | Incomplete | Restart mechanism missing |
| Plan Section 1-2 | Complete | |
| Plan Section 4-7 | Partial | Install menu details updated but incomplete |

## Next Steps
1. Reorder startup sequence in `main.py` (Line 230-236).
2. Implement Compute Backend selection in `llama_updater.py` for the install workflow.
3. Implement self-update restart logic in `main.py` using `os.execv`.
4. Update `Plan.md` to reflect the current status of the install menus.
