---
name: project-bug-create
description: Use this skill to triage, analyze, reproduce via manual terminal verification, and document new issues in the Bugs.md file.
---

# Skill Instructions

**Constraint:** Do not modify any source code files, test files, or configuration files. This is a documentation-only workflow. Only modify `./Bugs.md`. Use the `todowrite` tool to manage this triage iteration.

⚠️ **STRICT AGENT BOUNDARY & ORCHESTRATION RULES:**
- You are acting SOLELY as an **orchestrator**. You must NOT perform direct work (file edits, code analysis, or terminal execution) in the main interface.
- All technical inspection, file updates, and shell executions MUST be delegated to an `@general` agent via `todowrite`.

**EXECUTION POLICY:** Perform steps strictly in sequence. Do not spawn concurrent agents. You must pause and wait for explicit user approval via AskUserQuestion before finalizing and appending any bug entry to the filesystem.

---

## Phase 1 — Information Gathering & Intake

Use AskUserQuestion to prompt the user for a clear, concise description of the issue.
*Optional:* Request the user to estimate severity, provide specific reproduction steps, or mention known environmental details if available.

---

## Phase 2 — Technical Analysis, Manual Verification & Drafting

Once intake details are received, use `todowrite` to create the combined analysis and manual verification step and assign it to @general.

> Read `./Requirements.md`, `./Plan.md`, `./Testing Strategy.md`, and the existing `./Bugs.md`.
> Parse the user's provided bug report:
> "[Insert User Bug Report Here]"
> 
> Execute manual dynamic verification to confirm and analyze the bug behavior before drafting the entry:
> 
> 1. **Dynamic Reproduction Session:** Read the 'Manual Dynamic Testing' section of `./Testing Strategy.md`. Formulate the appropriate application startup command, runtime configuration, and specific sequence of interactive user inputs needed to exercise and expose the reported bug.
> 2. **Run and Capture:** Launch the interactive execution session using the session management tool or runner specified in `./Testing Strategy.md`, send the keypresses/inputs to navigate to the faulty behavior, and capture the terminal state. Enforce the following execution rules strictly during reproduction:
>    - *CRITICAL — Environment Isolation & Safety Gates:* Parse `./Testing Strategy.md` for any "Special Case" testing requirements or destructive workflows. If triggered, set up the specified isolation environment (such as a temporary sandbox directory) and execute mandatory validation gates before launching the session.
>    - *STATE SYNCHRONIZATION POLICY:* Copy relevant application files from the active working repository into the sandbox environment before testing. Do not copy runtime configs or generated binaries back into the working repository.
>    - *Scratch Artifact Pattern:* Write state captures or text dumps strictly to temporary locations (e.g., `/tmp/`). Never write to automated test directories or git history.
>    - *Session Cleanup:* Terminate and clean up the interactive session or background process once states are captured.
> 3. **Duplicate & Dependency Checks:** Check the 'Current Bug Reports' section of `./Bugs.md` to ensure the bug is not a duplicate. Cross-reference `./Requirements.md` and `./Plan.md` to identify dependencies and affected modules.
> 4. **Test Suitability:** Reference `./Testing Strategy.md` to determine if a new automated test case is required later to prevent this bug from reoccurring.
> 
> **CRITICAL:** Perform NO code changes, refactoring, or active bug fixes. Draft a structured entry for `./Bugs.md` containing: Clear Title, Severity/Priority, Dependencies, and the verified, precise workflow required to reproduce the bug based on your manual dynamic testing results. Return this draft to the orchestrator.

**WAIT:** Do not proceed until the agent returns the written draft.

---

## Phase 3 — User Verification

Review the entry drafted by @general. Use AskUserQuestion to present the draft directly to the user for structural review and validation. 

**WAIT:** Do not proceed to Phase 4 until the user provides explicit approval. If the user requests alterations, re-run Phase 2 with their feedback.

---

## Phase 4 — Document Finalization

Once approved by the user, use `todowrite` to create the write step and assign it to @general.

> Append the approved bug entry to the 'Current Bug Reports' section of `./Bugs.md`.
> Update the 'Project Roadmap' or status summary section within `./Bugs.md` to reflect the new tracked item.
> 
> Return a confirmation when the file has been successfully saved.

**WAIT:** Once confirmed, inform the user that the bug has been successfully tracked and is ready for the `project-bug-fix` pipeline.