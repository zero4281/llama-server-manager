---
name: project-plan
description: Use this skill to perform a gap analysis between Requirements.md and the codebase, then generate or update Plan.md.
---

# Skill Instructions
**Constraint:** Do not modify any source code files, configuration files, or files inside `./Tests/`. Only modify `./Plan.md`. Use the todowrite tool to track the planning lifecycle.

⚠️ **AGENT BOUNDARY** — The orchestrator must NOT read codebase files, parse execution logic, or directly modify markdown documents. All technical analysis, comparison loops, and file writing must be delegated to an @general agent.

**EXECUTION POLICY:** Perform tasks strictly in sequence. Do not spawn concurrent agents or proceed to final file generation until the analysis phase is verified.

---

## Phase 1 — Revision & Gap Analysis

Use todowrite to create the following planning analysis task and assign it to @general.

> Read `./Requirements.md` as the authoritative functional baseline.
> 
> **REVISION HISTORY ANALYSIS:**
> Parse the **Revision History** table/section at the end of `./Requirements.md`. 
> 1. Identify the current target version from the latest entry in the Revision History.
> 2. Read the current version heading in `./Plan.md` (if it exists). 
> 3. Identify any intermediate or skipped revisions between the baseline version in `Plan.md` and the target version in `Requirements.md` (e.g., jumping from `1.1.0` directly to `1.1.2`, skipping `1.1.1`).
> 4. Compile a cumulative list of all functional, structural, and architectural changes across all intermediate revisions leading up to the target version.
>
> Review all source code files (excluding `./Tests/`) to compare current codebase state against the cumulative requirements of the target revision range.
> Identify missing requirements, structural drift, unverified functionality, and outdated implementation assumptions.
> 
> Return a clear summary of findings, including explicit notes on any multi-revision jump context.

**WAIT:** Do not proceed until the analysis task is marked complete and verified.

---

## Phase 2 — Generate/Replace Plan Artifact

Based on the verified findings from Phase 1, use todowrite to create the Plan generation task and assign it to @general.

> Create `./Plan.md` if it does not exist. If it exists, completely overwrite and replace its contents.
> 
> Structure `./Plan.md` as follows:
> - **Header Tag:** `**Version [Target Version]**`
> - **Revision Jump Context (If applicable):** If intermediate revisions were jumped (e.g., `1.1.0` $\rightarrow$ `1.1.2`), include a sub-section explicitly listing all intermediate versions processed during this planning cycle and their primary changes.
> - **Section 1: Current State Assessment** (Verification table and structural/functional drift breakdown).
> - **Section 2: Core Engineering Decisions or Filename Consistency** (Architectural alignment for all target changes).
> - **Section 3: Testing & Verification Status** (Unit, Integration, and Manual Checklists).
> - **Section 4: Exit Codes**
> - **Section 5: Security**
> - **Section 6: Dependencies**
> - **Section 7: Non-Functional Requirements**

**WAIT:** Do not consider this skill execution complete until `./Plan.md` has been successfully written and verified.