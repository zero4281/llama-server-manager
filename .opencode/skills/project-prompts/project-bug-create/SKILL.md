---
name: project-bug-create
description: Use this skill to triage, analyze, and document new issues in the Bugs.md file.
---
# Skill Instructions
**Constraint:** Do not modify any source code files, test files, or configuration files. This is a documentation-only workflow. Only modify `./Bugs.md`. Use the todowrite tool to manage this triage iteration.

⚠️ **AGENT BOUNDARY** — The orchestrator must NOT parse local project files or directly append entries to the bug tracking documents. All duplication scanning, technical dependency analysis, and document adjustments must be delegated to an @general agent.

**EXECUTION POLICY:** Perform tasks strictly in sequence. Do not spawn concurrent agents. You must pause and wait for explicit user approval via AskUserQuestion before finalizing and appending any bug entry to the filesystem.

---

## Phase 1 — Information Gathering & Intake

Use AskUserQuestion to prompt the user for a clear, concise description of the issue.
*Optional:* Request the user to estimate severity, provide specific reproduction steps, or mention known environmental details if available.

---

## Phase 2 — Technical Analysis & Drafting

Once intake details are received, use todowrite to create the analysis task and assign it to @general.

> Read `./Requirements.md`, `./Plan.md`, `./Testing Strategy.md`, and the existing `./Bugs.md`.
> Parse the user's provided bug report:
> "[Insert User Bug Report Here]"
> 
> Analyze the codebase context to achieve the following:
> 1. Check the 'Current Bug Reports' section of `./Bugs.md` to ensure the bug is not a duplicate.
> 2. Cross-reference `./Requirements.md` and `./Plan.md` to identify dependencies and affected modules.
> 3. Reference `./Testing Strategy.md` to determine if a new test case is required to reproduce or verify this bug.
> 
> **CRITICAL:** Perform NO code changes, refactoring, or bug fixes. Draft a structured entry for `./Bugs.md` containing: Clear Title, Severity/Priority, Dependencies, and detailed Reproduction Steps. Return this draft to the orchestrator.

**WAIT:** Do not proceed until the agent returns the written draft.

---

## Phase 3 — User Verification

Review the entry drafted by @general. Use AskUserQuestion to present the draft directly to the user for structural review and validation. 

**WAIT:** Do not proceed to Phase 4 until the user provides explicit approval. If the user requests alterations, re-run Phase 2 with their feedback.

---

## Phase 4 — Document Finalization

Once approved by the user, use todowrite to create the write task and assign it to @general.

> Append the approved bug entry to the 'Current Bug Reports' section of `./Bugs.md`.
> Update the 'Project Roadmap' or status summary section within `./Bugs.md` to reflect the new tracked item.
> 
> Return a confirmation when the file has been successfully saved.

**WAIT:** Once confirmed, inform the user that the bug has been successfully tracked and is ready for the `project-bug-fix` pipeline.