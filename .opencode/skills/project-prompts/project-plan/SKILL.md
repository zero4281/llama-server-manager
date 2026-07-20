---
name: project-plan
description: Use this skill to reconcile Requirements.md with the implementation codebase and generate/update Plan.md.

---

# Skill Instructions
**Constraint:** Do not modify any source code files, configuration files, or files inside `./Tests/`. Only modify `./Plan.md` and `./Update.md`. Use the todowrite tool to track the lifecycle of this planning iteration.

⚠️ **AGENT BOUNDARY** — The orchestrator must NOT parse the codebase file contents or perform document synchronization directly. All file analysis, verification, and text modifications must be delegated to an @general agent.

**EXECUTION POLICY:** Perform tasks strictly in sequence. Do not spawn concurrent agents or proceed to subsequent phases until the current tracking task's output has been completely returned and evaluated.

---

## Phase 1 — Verify & Assess Gaps

Use todowrite to create the following verification task and assign it to @general.

> Read `./Requirements.md` and the existing `./Plan.md` (if present). Review the local project structure and source code files to verify exactly what components match the requirements. Identify:
> 1. Which requirements are fully met, partially met, or entirely unverified.
> 2. Any structural or functional drift between the actual code files and the current plan.
> Return a clear, structural summary of findings back to the orchestrator.

**WAIT:** Do not proceed until the verification task is marked complete and the summary is returned.

---

## Phase 2 — Generate/Replace Plan

Based on the verified status from Phase 1, use todowrite to create the update task and assign it to @general. 

> Read the current version string from the top of `./Requirements.md`. 
> Create `./Plan.md` if it does not exist. If it does exist, completely overwrite and replace its entire contents to purge all obsolete entries, resolved gaps, and historical violations.
> Rewrite the file as **Version [Insert Extracted Version String Here]** based *only* on the current outstanding gaps found in Phase 1.
> Ensure the updated document strictly adheres to the standard layout:
> - Section 1: Current State Assessment (with a compliance checklist and implementation verification table).
> - Section 2: Core Engineering Decisions or Filename Consistency.
> - Section 3: Testing & Verification Status (Unit, Integration, and Manual checklists).
> - Section 4-7: Architectural specifications (Exit codes, Security, Dependencies, Non-functional requirements).

**WAIT:** Do not proceed until `./Plan.md` has been successfully written and verified.

---

## Phase 3 — Invalidate Downstream Artifacts

To prevent the execution engine from running outdated gap analyses against a fresh plan, use todowrite to create the cleanup task and assign it to @general.

> Check for the existence of `./Update.md`. 
> If `./Update.md` does not exist, create it. 
> If it does exist, completely overwrite and replace its contents. 
> The file must contain only this single line of text:
> "Update.md is stale — re-run /project-update."
> This ensures that code updates cannot accidentally be executed against an obsolete plan.