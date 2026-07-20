---
name: project-bug-fix
description: Use this skill to select, implement, verify via automated and manual dynamic testing, and document fixes for items in the Bugs.md file.
---
# Skill Instructions
**Constraint:** Do not modify any files inside designated test directories or configuration metrics during this initial execution loop. Only modify the targeted source code files requiring the fix and update `./Bugs.md`. Use the todowrite tool to track the lifecycle of this fix.

⚠️ **AGENT BOUNDARY** — The orchestrator must NOT inspect the implementation diffs, edit source blocks, run test binaries, or directly execute terminal verification scripts. Selection presentations, code repairs, regression testing, and tmux session interactions must be handled entirely by an @general agent.

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

Use todowrite to create the verification task and assign it to @general to perform both automated regression testing and manual dynamic terminal testing.

> 1. **Automated Testing:** Read `./Testing Strategy.md` to extract the project's designated test suite command. Run the regression test suite using the extracted test command.
> 2. **Manual Dynamic Testing:** Read the **Manual Dynamic Testing** section of `./Testing Strategy.md`. Formulate the appropriate application startup command and sequential user inputs needed to exercise the fixed functionality.
> 3. **Session Interaction & Capture:** Launch the app inside a detached `tmux` session, transmit the navigation keypresses, and capture the post-input state to verify the layout or behavior fixes are active and terminal stability is restored.
>    - *Scratch Artifacts:* State captures and terminal output dumps must be written strictly to scratch or temporary locations (such as `/tmp/` or the current working directory outside designated test directories). They must **never** be written to automated test directories or committed.
>    - *Session Cleanup:* The application instance and interactive `tmux` session must be explicitly terminated and cleaned up once the final verification states are captured.
> 
> Return the automated test results and the manual verification state summaries to the orchestrator.
> 
> **ERROR HANDLING LOOP:** If the automated test suite fails or the captured manual testing states reveal regressions, unintended crashes, or improper input handling, pass the specific errors and behavioral logs back to @general. Request an updated code fix. Repeat this test-and-repair loop strictly within source boundaries until the automated test suite runs completely green and the manual dynamic captures confirm stable, intended behavior. Do not alter automated test assertions to bypass failures, and do not adjust the tmux validation parameters to mask source defects.

**WAIT:** Do not proceed until both testing layers pass cleanly.

---

## Phase 4 — Finalize Tracking

Once the fix passes all verification checks, use todowrite to create the final tracking update task and assign it to @general.

> Update `./Bugs.md` to officially mark the selected bug item as complete. Include a brief, high-level summary of the resolution changes under its entry or tracking log.