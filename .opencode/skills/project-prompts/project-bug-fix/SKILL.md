---
name: project-bug-fix
description: Use this skill to select, implement, verify, and document fixes for items in the Bugs.md file.
---
# Skill Instructions
**Constraint:** Do not modify any files inside designated test directories or configuration metrics during this initial execution loop. Only modify the targeted source code files requiring the fix and update `./Bugs.md`. Use the todowrite tool to track the lifecycle of this fix.

⚠️ **AGENT BOUNDARY** — The orchestrator must NOT inspect the implementation diffs, edit source blocks, or run test binaries directly. Selection presentations, code repairs, and regression test suites must be handled entirely by an @general agent.

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
> Implement the precise source code modification required to resolve the bug, adhering to the expected outcomes and behaviors defined in `./Requirements.md`. Do not touch markdown tracking documents or test files yet. Return a written summary of the changes made.

**WAIT:** Do not proceed until @general reports code modification completion.

---

## Phase 3 — Verification & Regression Testing

Use todowrite to create the verification task and assign it to @general.

> 1. Read `./Testing Strategy.md` to extract the project's designated test suite command.
> 2. Perform a manual verification of the modified code diff against the requirements.
> 3. Run the regression test suite using the extracted test command.
> 
> Return the test results and logs to the orchestrator.
> 
> **ERROR HANDLING LOOP:** If the tests fail, provide the exact error logs back to @general and request an updated code fix. Repeat this test-and-repair loop strictly within source boundaries until the test suite runs completely green. Do not alter test assertions to bypass failures.

---

## Phase 4 — Finalize Tracking

Once the fix passes all verification checks, use todowrite to create the final tracking update task and assign it to @general.

> Update `./Bugs.md` to officially mark the selected bug item as complete. Include a brief, high-level summary of the resolution changes under its entry or tracking log.