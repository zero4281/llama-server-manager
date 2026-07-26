---
name: project-bug-fix
description: Use this skill to select, implement, verify via manual dynamic testing then automated testing, and document fixes for items in the Bugs.md file.
---
# Skill Instructions
**Constraint:** Do not modify any files inside designated test directories or configuration metrics during this initial execution loop. Only modify the targeted source code files requiring the fix and update `./Bugs.md`. Use the todowrite tool to track the lifecycle of this fix.

⚠️ **STRICT AGENT BOUNDARY & ORCHESTRATION RULES:**
- You are acting SOLELY as an **orchestrator**. You must NOT perform any execution work yourself.
- You must NOT read or inspect source files, examine code diffs, write or edit source blocks, run test binaries, or directly execute terminal verification scripts in the main interface.
- **ALL work**—including bug listing, code repairs, regression testing, tmux session management, and Markdown updates—MUST be delegated entirely to an `@general` agent via `todowrite`.
- Your ONLY responsibility is managing task flow via `todowrite`, presenting selections to the user via `AskUserQuestion`, spawning `@general` agents to perform the work, and reviewing their returned summaries.

**EXECUTION POLICY:** Run repairs sequentially on exactly one bug at a time. Do not initiate an agent modification loop until the user has explicitly selected an item and the previous code state has been verified.

---

## Phase 1 — Select Target Bug

Use todowrite to create an initial parsing task and assign it to @general.

> Read `./Bugs.md`, `./Requirements.md`, `./Plan.md`, and `./Testing Strategy.md`.
> Parse `./Bugs.md` to compile a clean list of all pending, uncompleted bug items (including titles, priorities, and dependencies). Return this list to the orchestrator.

**WAIT:** Once the list is returned, present it to the user via AskUserQuestion and wait for them to explicitly select which bug item to resolve.

---

## Phase 2 — Targeted Delegation & Fix

Print the message: "Starting work on [Selected Bug Title]." Immediately follow this by using todowrite to create the implementation task and assign it to @general.

> Ingest the full bug description, reproduction steps, and dependencies from `./Bugs.md` for: [Selected Bug Title].
> Review the source code files identified as relevant during Phase 1.
> 
> Implement the precise source code modification required to resolve the bug, adhering to the expected outcomes and behaviors defined in `./Requirements.md` and `./Plan.md`. Do not touch markdown tracking documents or test files yet. Return a written summary of the changes made.

**WAIT:** Do not proceed until @general reports code modification completion.

---

## Phase 3 — Verification & Regression Testing

Use todowrite to create the verification task and assign it to @general to perform manual dynamic terminal testing followed by automated regression testing.

> 1. **Manual Dynamic Testing:** Read the **Manual Dynamic Testing** section of `./Testing Strategy.md`. Formulate the appropriate application startup command and sequential user inputs needed to exercise the fixed functionality.
> 
>    **Session Interaction & Capture Rules:** Enforce the following execution rules strictly during the interactive verification:
>    - *CRITICAL — Environment Isolation & Safety Gates:* You must parse `./Testing Strategy.md` for any "Special Case" testing requirements or destructive workflows (e.g., self-overwriting flags, file-clobbering operations). If the determined test sequence triggers one of these conditions, you **must** set up the specified isolation environment (such as a temporary sandbox directory) and execute mandatory validation gates (e.g., directory matching or path checks) before launching the execution session. You are explicitly forbidden from running destructive operations directly within the active working repository.
>    - *STATE SYNCHRONIZATION POLICY:* To prevent lost changes or testing stale code when using an isolated environment, you must adhere to a strict directional synchronization lifecycle:
>      1. **Pre-Test Sync:** Before running the test sequence or spawning the execution session, copy the fresh, edited source files from the active working repository into the sandbox environment.
>      2. **Post-Failure Sync (If bugs found):** If the verification fails and you discover a bug or regression during the session, any code adjustments or fixes must be applied directly to the **active working repository**, *not* patched inline inside the sandbox. The Pre-Test Sync must then be repeated before the next verification attempt.
>    - *Scratch Artifacts:* State captures and terminal output dumps must be written strictly to scratch or temporary locations (such as `/tmp/` or the current working directory outside designated test directories). They must **never** be written to automated test directories or committed.
>    - *Session Cleanup:* The application instance and interactive `tmux` session must be explicitly terminated and cleaned up once the final verification states are captured.
> 
>    **EARLY SHORT-CIRCUIT:** If the manual dynamic testing reveals any regressions, unintended crashes, or improper input handling, **STOP IMMEDIATELY**. Do not proceed to Step 2 (Automated Testing). Log the captured failures and enter the error handling loop to perform the required source code repairs.
> 
> 2. **Automated Testing:** ONLY if Manual Dynamic Testing passes completely, proceed to automated testing. Read `./Testing Strategy.md` to extract the project's designated test suite command. Run the regression test suite using the extracted test command.
> 
> Return the verification summaries and test results to the orchestrator.
> 
> **ERROR HANDLING LOOP:** If manual dynamic captures reveal defects, OR if the automated test suite fails, pass the specific errors and behavioral logs back to @general to apply an updated source code fix. Repeat this test-and-repair loop strictly within source boundaries until manual dynamic captures confirm stable behavior AND the automated test suite runs completely green. Do not alter automated test assertions to bypass failures, and do not adjust the tmux validation parameters to mask source defects.

**WAIT:** Do not proceed until both testing layers pass cleanly.

---

## Phase 4 — Finalize Tracking

Once the fix passes all verification checks, use todowrite to create the final tracking update task and assign it to @general.

> Update `./Bugs.md` to officially mark the selected bug item as complete. Include a brief, high-level summary of the resolution changes under its entry or tracking log.