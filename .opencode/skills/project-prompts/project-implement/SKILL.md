---
name: project-implement
description: Use this skill to orchestrate and execute source code updates based on the gaps identified in Update.md.
---

# Skill Instructions

**Constraint:** Do not modify any markdown documentation files (`.md`). Do not modify, add, or delete any files inside designated test directories as defined in `./Testing Strategy.md`. Use the `todowrite` tool to manage high-level implementation tracking.

⚠️ **STRICT AGENT BOUNDARY & ORCHESTRATION RULES:**
- You are acting SOLELY as an **orchestrator**. You must NOT perform direct work (file edits, code analysis, or terminal execution) in the main interface.
- All technical inspection, file updates, and shell executions MUST be delegated to an `@general` agent via `todowrite`.

**EXECUTION POLICY:** Code updates must be performed strictly one work item at a time. Do not batch modifications or initiate a new sub-item until the previous item has been fully implemented, verified via a code diff, and returned by the agent.

---

## Phase 1 — Implementation Breakdown

Read `./Requirements.md`, `./Plan.md`, and `./Testing Strategy.md` to establish context.
Read `./Update.md` to extract the required code updates and features targeted for removal.

Identify the logical units of work. You will execute these sequentially through `@general` in Phase 2. Do not write these work items to an external markdown file; maintain them within the orchestrator's step-by-step execution loop.

---

## Phase 2 — Sequential Code Updates

For each gap or feature removal identified in Phase 1, use the native `todowrite` tool to record a tracking item and assign it to @general. 

**Constraint:** You must execute these one at a time. Wait for confirmation and a written summary of changes from @general before moving to the next item.

Each prompt to @general must include:

- The specific target file path.
- The precise feature modification or removal instructions (with line range references if available from `Update.md`).
- The explicit constraint: Do not modify markdown files or any testing environment paths.

**REALLOCATION LOOP:** If @general fails to update a component cleanly, re-verify the code diff, supply the specific compilation or logical error, and re-assign the fix directly to @general before proceeding.

---

## Phase 3 — Dynamic Manual Verification

Once all structural code updates from Phase 2 are complete, use the native `todowrite` tool to record the verification step and assign it to @general to perform manual dynamic testing. 

The orchestrator must read the **Manual Dynamic Testing** section of `./Testing Strategy.md` to extract the mandatory testing constraints, execution environments, session logging/capture patterns, special sandbox/isolation protocols, and the exact interactive verification lifecycle.

Based on the specific updates implemented in Phase 2 and the guidelines in `./Testing Strategy.md`, determine:

1. The appropriate application startup command, runtime configuration, environment variables, or flags required to exercise the updated feature.
2. The specific sequence of user inputs, parameters, payloads, or navigation paths needed to reach and trigger the modified functionality.

Instruct @general to execute the dynamic verification steps according to the interaction procedure outlined in `./Testing Strategy.md`, enforcing the following rules as clear, explicit constraints in the prompt:

- **CRITICAL — Environment Isolation & Safety Gates:** Parse `./Testing Strategy.md` for any "Special Case" testing requirements or destructive workflows. Set up the specified isolation environment (such as a temporary sandbox directory) and execute mandatory validation gates before launching the execution session if required.
- **STATE SYNCHRONIZATION POLICY:** 
  1. **Pre-Test Sync:** Copy fresh, edited source files from the active working repository into the sandbox environment.
  2. **Post-Failure Sync:** If verification fails, apply code fixes directly to the **active working repository**, *not* inline inside the sandbox.
- **Scratch Artifacts:** State captures, execution logs, and output dumps must be written strictly to scratch/temporary locations (e.g., `/tmp/`).
- **Session Cleanup:** The application instance or interactive test session must be explicitly terminated and cleaned up once final verification states are captured.
- **INLINE ERROR REPAIR:** If manual dynamic testing reveals failures during execution, apply necessary fixes directly to the source code files and repeat the verification loop until manual dynamic captures confirm stable, intended behavior.

Review the resulting artifacts:

- Verify that the specific feature changes, success states, or outputs expected from the `Update.md` requirements are visible in the captured application states.
- Confirm that the application handles input correctly, processes the dynamic workflow as expected, and does not crash or exhibit unintended behavior.

**CRITICAL:** Fixes for any behavioral bugs, execution errors, or functional flaws discovered here must be applied strictly to the source code. Never modify automated test files, test configurations, or paper over the issue by adjusting the interactive execution script.

**WAIT:** If dynamic testing reveals failures or incorrect behavior, the orchestrator must create a follow-up item using `todowrite` for `@general` to repair the source code. Repeat Phase 3 until manual testing artifacts confirm stable, intended behavior.