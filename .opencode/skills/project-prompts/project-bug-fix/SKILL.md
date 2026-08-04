---
name: project-bug-fix
description: Use this skill to select, implement, verify via manual dynamic testing then automated testing, and document fixes for items in the Bugs.md file.
---

# Skill Instructions

**Constraint:** Do not modify any files inside designated test directories or configuration metrics during this initial execution loop. Only modify the targeted source code files requiring the fix and update `./Bugs.md`. Use the `todowrite` tool to track the lifecycle of this fix.

⚠️ **STRICT AGENT BOUNDARY & ORCHESTRATION RULES:**
- You are acting SOLELY as an **orchestrator**. You must NOT perform direct work (file edits, code analysis, or terminal execution) in the main interface.
- All technical inspection, file updates, interactive session setups, and shell executions MUST be delegated to an `@general` agent via `todowrite`.

**EXECUTION POLICY:** Run repairs sequentially on exactly one bug at a time. Do not initiate an agent modification loop until the user has explicitly selected an item and the previous code state has been verified.

---

## Phase 1 — Select Target Bug

Use the native `todowrite` tool to record an initial parsing item and delegate it to @general.

> Read `./Bugs.md`.
> Parse `./Bugs.md` to compile a clean list of all pending, uncompleted bug items (including titles, priorities, and dependencies). Return this list to the orchestrator.

**WAIT:** Once the list is returned, present it to the user via AskUserQuestion and wait for them to explicitly select which bug item to resolve.

---

## Phase 2 — Targeted Delegation, Fix & Self-Verification

Print the message: "Starting work on [Selected Bug Title]." Immediately follow this by using the native `todowrite` tool to record the implementation item and delegate it to @general.

> 1. **Context & Safety Review:** 
>    
>    - Ingest the full bug description, reproduction steps, and dependencies from `./Bugs.md` for: **[Selected Bug Title]**.
>    - Read the **Manual Dynamic Testing** section of `./Testing Strategy.md` to identify all setup requirements, safety gates, environment rules, session tools, or special isolation protocols required when working on or verifying this functional area.
>    - Review the source code files identified as relevant during Phase 1.
>    
> 2. **Implementation:** Implement the precise source code modification required to resolve the bug, adhering to expected outcomes and behaviors defined in `./Requirements.md` and `./Plan.md`. Do not touch markdown tracking documents or test files yet.
>    
> 3. **Static & Syntax Self-Verification:** Perform a mandatory self-check on all edited files:
>    
>    - Run language-appropriate syntax, linting, or basic static checks on modified files to verify no syntax or parse errors were introduced.
>    - Run `git diff` to carefully review all edits against the expected outcomes in `./Requirements.md` and `./Plan.md` to confirm the fix is complete, correct, and free of unintended modifications.
>    
> 4. **Phase 2 Repair Loop:** If syntax errors, incomplete edits, or unintended side effects are discovered during self-verification, **immediately fix them** and repeat the self-verification steps. 
>    
> Once syntax check passes cleanly and `git diff` confirms accurate edits, return a summary detailing the changes made and the files modified.

**WAIT:** Do not proceed until @general reports successful completion of code modifications and self-verification.

---

## Phase 3 — Context Re-Ingestion, Verification & Regression Testing

Use the native `todowrite` tool to record a verification item and delegate the execution to @general. **Ensure the delegation prompt explicitly carries forward the [Selected Bug Title].**

> **Context Synchronization:** Before beginning verification:
> 
> 1. Re-read the target bug entry for **[Selected Bug Title]** directly from `./Bugs.md` to refresh the full bug description, reproduction steps, and criteria.
> 2. Run `git diff` to review all current pending modifications. Use this diff to identify the exact code paths and surface areas modified in Phase 2.
> 
> ---
> 
> 1. **Manual Dynamic Testing:** Read and execute the **Manual Dynamic Testing** procedure outlined in `./Testing Strategy.md` for all verifications without exception. Extract session runner protocols, environment flags, and interactive navigation steps directly from `./Testing Strategy.md`.
> 
> **Session Interaction & Capture Rules:** Enforce the following execution rules strictly during the interactive verification:
> 
> - *MANDATORY — Environment Isolation & Safety Gates:* Parse `./Testing Strategy.md` for any "Special Case" testing requirements or destructive workflows. If triggered, set up the specified isolation environment (such as a temporary sandbox directory) and execute mandatory validation gates before launching the execution session. Do not run destructive operations directly within the active working repository.
> - *STATE SYNCHRONIZATION POLICY:* 
>   1. **Pre-Test Sync:** Copy fresh, edited source files from the active working repository into the sandbox environment.
>   2. **Post-Failure Sync:** If verification fails, apply code fixes directly to the **active working repository**, *not* inline inside the sandbox. Repeat Pre-Test Sync before the next verification attempt.
> - *Scratch Artifacts:* State captures, execution logs, and output dumps must be written strictly to scratch/temporary locations (e.g., `/tmp/`). Never write scratch artifacts to automated test directories or git history.
> - *Session Cleanup:* Terminate and clean up application instances or interactive test sessions once states are captured.
> - **EARLY SHORT-CIRCUIT:** If manual dynamic testing reveals failures, unexpected crashes, or incorrect behavior during execution, **STOP IMMEDIATELY**. Do not proceed to Step 2 (Automated Testing). Log failures and enter the error handling loop.
> 
> 2. **Automated Testing:** ONLY if Manual Dynamic Testing passes completely, proceed to automated testing. Read `./Testing Strategy.md` to extract the project's designated test suite command. Run the regression test suite using the extracted test command.
> 
> Return the verification summaries and test results to the orchestrator.
> 
> **ERROR HANDLING LOOP:** If manual dynamic captures reveal defects, OR if the automated test suite fails, apply the necessary source code fix directly to the active working repository source files and repeat the verification loop until manual dynamic captures confirm stable, intended behavior. Do not attempt to spawn external sub-agents.
> 
> **WAIT:** Do not proceed until both testing layers pass cleanly.

---

## Phase 4 — Finalize Tracking

Once the fix passes all verification checks, use the native `todowrite` tool to record the final tracking update step and delegate it to @general.

> Update `./Bugs.md` to officially mark the selected bug item as complete. Include a brief, high-level summary of the resolution changes under its entry or tracking log.