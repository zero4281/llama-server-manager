---
name: project-implement
description: Use this skill to orchestrate and execute source code updates based on the gaps identified in Update.md.
---
# Skill Instructions
**Constraint:** Do not modify any markdown documentation files (`.md`). Do not modify, add, or delete any files inside designated test directories as defined in `./Testing Strategy.md`. Use the todowrite tool to manage the high-level implementation tracking.

⚠️ **AGENT BOUNDARY** — The orchestrator must NOT modify source code files or run tests directly. The orchestrator's sole responsibility is to break down `Update.md` into incremental execution steps, track them, and delegate code modifications and test executions to an @general agent.

**EXECUTION POLICY:** Code updates must be performed strictly one task at a time. Do not batch modifications or initiate a new sub-task until the previous task has been fully implemented, verified via a code diff, and returned by the agent.

---

## Phase 1 — Implementation Breakdown

Read `./Requirements.md`, `./Plan.md`, and `./Testing Strategy.md` to establish context.
Read `./Update.md` to extract the required code updates and features targeted for removal.

Identify the logical units of work. You will execute these sequentially through `@general` in Phase 2. Do not write these sub-tasks to an external markdown file; maintain them within the orchestrator's step-by-step execution loop.

---

## Phase 2 — Sequential Code Updates

For each gap or feature removal identified in Phase 1, use todowrite to spawn a tracking task and assign it to @general. 

**Constraint:** You must execute these one at a time. Wait for confirmation and a written summary of changes from @general before moving to the next item.

Each prompt to @general must include:
- The specific target file path.
- The precise feature modification or removal instructions (with line range references if available from `Update.md`).
- The explicit constraint: Do not modify markdown files or any testing environment paths.

**REALLOCATION LOOP:** If @general fails to update a component cleanly, re-verify the code diff, supply the specific compilation or logical error, and re-assign the fix to @general before proceeding.

---

## Phase 3 — Regression Testing & Verification

Once all structural code updates from Phase 2 are complete, use todowrite to create the verification task and assign it to @general.

> Read `./Testing Strategy.md` to extract the project's configured test suite execution command.
> 
> Execute the test suite using that exact command.
> 
> Review the output:
> - If all tests pass successfully, return a verification success message.
> - If any tests fail, identify which source code updates caused the regression.
> 
> **CRITICAL:** Do not modify any test files to force a passing state. All fixes must be applied strictly to the source code files to bring them into alignment with the established test suites and requirements.

**WAIT:** If tests fail, pass the failure logs back to @general as a new sub-task to fix the source code. Repeat Phase 3 until the project's test suite runs completely green.