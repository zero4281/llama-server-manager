---
name: project-update
description: Use this skill to perform a gap assessment between Plan.md and the source code, generating or replacing Update.md.
---
# Skill Instructions
**Constraint:** Do not modify any source code files, configuration files, or files inside `./Tests/`. Only modify `./Update.md`. Do not include test coverage gaps or test file changes in this artifact. Use the todowrite tool to track the gap analysis lifecycle.

⚠️ **AGENT BOUNDARY** — The orchestrator must NOT read codebase files, parse execution logic, or directly modify markdown documents. All technical analysis, comparison loops, and file writing must be delegated to an @general agent.

**EXECUTION POLICY:** Perform tasks strictly in sequence. Do not spawn concurrent agents or proceed to final file generation until the complete gap assessment analysis has been returned and verified.

---

## Phase 1 — Technical Gap Assessment

Use todowrite to create the following code assessment task and assign it to @general.

> Read `./Requirements.md` and `./Plan.md` to establish the target implementation baseline.
> Review all local source code files, explicitly ignoring any files inside the `./Tests/` directory.
> 
> Perform a comprehensive gap assessment to identify:
> 1. Required features from the plan that are missing, incomplete, or partially implemented in the source code.
> 2. Implemented features currently in the source code that are non-required or explicitly omitted by the current version of the plan (features to remove).
> 
> Return a clear structural breakdown of required updates and code to prune.

**WAIT:** Do not proceed until the gap assessment task is marked complete and the technical summary is returned.

---

## Phase 2 — Generate/Replace Update Artifact

Based on the verified findings from Phase 1, use todowrite to create the update generation task and assign it to @general.

> Create `./Update.md` if it does not exist. If it does exist, completely overwrite and replace its entire contents. 
> 
> Write the gap assessment results into the file using the following layout:
> - A high-level Summary of the required alignment.
> - An explicit section details "Implemented but Non-Required: Features to Remove" (specifying file targets, line ranges, and rationale).
> - A structured compliance table mapping out the codebase status against each section of the requirements.
> - A clear set of immediate Next Steps for implementation.
> 
> **CRITICAL:** Ensure no test-related tasks or test suite gaps are written to this file.

**WAIT:** Do not consider this skill execution complete until `./Update.md` has been successfully written and verified.