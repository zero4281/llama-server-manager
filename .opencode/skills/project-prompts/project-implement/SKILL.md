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

## Phase 3 — Dynamic Manual Verification

Once all structural code updates from Phase 2 are complete, use todowrite to create the verification task and assign it to @general to perform manual dynamic testing. 

The orchestrator must read the **Manual Dynamic Testing** section of `./Testing Strategy.md` to extract the mandatory testing constraints, execution environments, session logging/capture patterns, special sandbox/isolation protocols, and the exact interactive verification lifecycle.

Based on the specific updates implemented in Phase 2 and the guidelines in `./Testing Strategy.md`, determine:

1. The appropriate application startup command, runtime configuration, environment variables, or flags required to exercise the updated feature.
2. The specific sequence of user inputs, parameters, payloads, or navigation paths needed to reach and trigger the modified functionality.

Instruct @general to execute the dynamic verification steps according to the interaction procedure outlined in `./Testing Strategy.md`, enforcing the following rules as clear, explicit constraints in the task assignment:

- **CRITICAL — Environment Isolation & Safety Gates:** The orchestrator must parse `./Testing Strategy.md` for any "Special Case" testing requirements or destructive workflows (e.g., self-overwriting flags, file-clobbering operations). If the determined test sequence triggers one of these conditions, the orchestrator **must** explicitly command the agent to set up the specified isolation environment (such as a temporary sandbox directory) and execute mandatory validation gates (e.g., directory matching or path checks) before launching the execution session. The agent must be explicitly forbidden from running destructive operations directly within the active working repository.
- **STATE SYNCHRONIZATION POLICY:** To prevent lost changes or testing stale code when using an isolated environment, the orchestrator must enforce a strict directional synchronization lifecycle on the agent:
  1. **Pre-Test Sync:** Before running the test sequence or spawning the execution session, the agent must copy the fresh, edited source files from the active working repository into the sandbox environment.
  2. **Post-Failure Sync (If bugs found):** If the verification fails and the agent discovers a bug during the session, any code adjustments or fixes must be applied directly to the **active working repository**, *not* patched inline inside the sandbox. The Pre-Test Sync must then be repeated before the next verification attempt.
- **Scratch Artifacts:** State captures, execution logs, and output dumps (e.g., initial or post-input verification data) must be written strictly to scratch or temporary locations (such as `/tmp/` or the current working directory outside the designated test directories). They must **never** be written to active automated test directories or committed.
- **Session Cleanup:** The application instance, background process, or interactive test session must be explicitly terminated and cleaned up once the final verification states are captured.

Review the resulting artifacts:

- Verify that the specific feature changes, success states, or outputs expected from the `Update.md` requirements are visible in the captured application states.
- Confirm that the application handles input correctly, processes the dynamic workflow as expected, and does not crash or exhibit unintended behavior.

**CRITICAL:** Fixes for any behavioral bugs, execution errors, or functional flaws discovered here must be applied strictly to the source code. Never modify automated test files, test configurations, or paper over the issue by adjusting the interactive execution script.

**WAIT:** If the dynamic testing reveals failures, unexpected crashes, or incorrect behavior, pass the logs/behavior notes back to @general as a new sub-task to fix the source code. Repeat Phase 3 until the manual testing artifacts confirm stable, intended behavior.