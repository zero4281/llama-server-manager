---
name: project-update
description: Use this skill to perform a gap assessment between Requirements.md, Plan.md, and the source code, generating or replacing Update.md.
---

# Skill Instructions

**Constraint:** Do not modify any source code files, configuration files, or files inside `./Tests/`. Only modify `./Update.md`. Do not include test coverage gaps or test file changes in this artifact. Use the `todowrite` tool to track the gap analysis lifecycle.

⚠️ **STRICT AGENT BOUNDARY & ORCHESTRATION RULES:**
- You are acting SOLELY as an **orchestrator**. You must NOT perform direct work (file edits, code analysis, or terminal execution) in the main interface.
- All technical inspection, file updates, and shell executions MUST be delegated to an `@general` agent via `todowrite`.

**EXECUTION POLICY:** Perform steps strictly in sequence. Do not spawn concurrent agents or proceed to final file generation until the complete gap assessment analysis has been returned and verified.

---

## Phase 1 — Technical Gap Assessment

Use `todowrite` to create the following code assessment step and assign it to @general.

> Read `./Requirements.md` to establish the absolute, authoritative functional baseline and ultimate source of truth for the project.
> **IMPORTANT:** Parse the **Revision History** table at the end of `./Requirements.md`. Identify all revisions spanning from the current implementation baseline up to the target version (including any skipped or intermediate versions like `1.1.1` $\rightarrow$ `1.1.2`). Build a cumulative list of all required changes across these revisions.
> 
> Read `./Plan.md` to establish the active development baseline, explicitly ignoring Section 3 (Testing & Verification Status). Treat Requirements.md as a strict override if any contradictions exist between the Plan and the Requirements.
> Check if `./Update.md` currently contains the placeholder text "Update.md is stale — re-run /project-update." If it does, ignore the current content of Update.md completely.
> Review all local source code files, explicitly ignoring any files inside designated test directories defined in `./Testing Strategy.md`.
> 
> Perform a comprehensive multi-way gap assessment across the cumulative Requirements delta, the Plan, and the active codebase to identify:
> 1. Required features from all target/intermediate revision specifications or plan that are missing, incomplete, or partially implemented in the source code.
> 2. Implemented features currently in the source code that violate constraints or are explicitly omitted by Requirements.md (features to prune).
> 3. Any functional discrepancies or "drift" where Plan.md claims a requirement is complete, but the actual code implementation falls short of the Requirements.md specification.
> 
> Return a clear structural breakdown of required updates and code to prune.

**WAIT:** Do not proceed until the gap assessment step is marked complete and the technical summary is returned.

---

## Phase 2 — Generate/Replace Update Artifact

Based on the verified findings from Phase 1, use `todowrite` to create the update generation step and assign it to @general.

> Create `./Update.md` if it does not exist. If it does exist, completely overwrite and replace its entire contents.
> Write the gap assessment results into the file using the following layout:
> - A high-level Summary of the required alignment, explicitly calling out any multi-revision jumps processed (e.g., Target `1.1.2` including skipped `1.1.1` deltas).
> - An explicit section detailing "Implemented but Non-Required: Features to Remove" (specifying file targets, line ranges, and rationale based on Requirements.md).
> - A structured compliance table mapping out the codebase status against core functional specifications in Requirements.md and non-testing sections of Plan.md[cite: 1].
> - A clear set of immediate Next Steps for implementation.
> 
> CRITICAL: Ensure no test-related work items or test suite gaps are written to this file.

**WAIT:** Do not consider this skill execution complete until `./Update.md` has been successfully written and verified.