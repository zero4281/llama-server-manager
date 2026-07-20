---  
name: project-update-tests
description: Use this skill to review and update the test suite after code changes.

---

# Skill Instructions
**Constraint:** Do not modify any core source files. Only modify files located within the test directories defined in `./Testing Strategy.md`. Use the todowrite tool to track all tasks. 

⚠️ **AGENT BOUNDARY** — The orchestrator must NOT read files inside test suites or execute test commands directly. All such actions must be delegated to an @general agent. 

**EXECUTION POLICY:** Perform only one task at a time. Do not initiate any agent until the output of the previous agent has been returned and reviewed. 

---

## Phase 1 — Analyse

**Constraint:** You must execute these tasks sequentially. Do not batch them. Wait for the summary of each task before creating the next.

Use todowrite to create the following three tasks and assign each to @general. 

Include the following context in every task:
- Read `./Testing Strategy.md` to locate the correct testing folders, metadata properties, and execution commands.
- Only modify files inside the identified test directories.
- Read `./Requirements.md` and **specifically Section 3 (Testing & Verification Status) of `./Plan.md`** before starting. Do not review core implementation tasks outside of this section.
- Return a written summary of findings, including a list of specific fixes needed.

### Task 1 — Coverage Gaps
> Read `./Testing Strategy.md`. Locate the designated testing folders. Compare behaviors specified in the behavioral specifications and coverage gaps sections of the testing documentation against the existing test files. For each specified behavior with no corresponding test, note it as a gap. New tests must go into the existing file that matches their coverage area — do not create new test files. Follow the standard configuration rules outlined in the testing documentation. Return a written summary with a list of specific gaps found.

**WAIT:** Do not proceed until Task 1 is complete and the summary is returned.

### Task 2 — Stale Tests
> Identify existing tests within the test directories that no longer match the current source code (e.g., outdated return values, removed methods, or changed signatures). Note each discrepancy with a description of what needs to change. Return a written summary with a list of specific staleness issues found.

**WAIT:** Do not proceed until Task 2 is complete and the summary is returned.

### Task 3 — Mocking Compliance
> Read `./Testing Strategy.md` to check if a mock verification script path is defined in the configuration parameters. If a verification script is specified and exists on disk, run it using the environment's appropriate interpreter. Otherwise, manually scan the test directory files to ensure mocking patterns match the compliance rules defined in `./Testing Strategy.md` (paying strict attention to the UIManager curses.newwin intercept rules). Note any violations. Return a written summary listing any violations found.

---

## Phase 2 — Fix

Once all three analysis tasks are complete and their summaries are returned, use todowrite to create one task per finding. Assign each task to @general one at a time.

**Constraint:** You must create and execute these tasks one at a time. Wait for the agent to confirm the fix before moving to the next finding.

Each task must include:
- The specific test file and block to add or modify (from the analysis summary).
- The constraint: only modify files inside the project's designated test directories.
- Enough context from the summary so @general can act without re-reading everything.

**WAIT:** Do not begin Phase 3 until all fix tasks are marked complete.

---

## Phase 3 — Verify

Use todowrite to create the following task and assign it to an @general agent: 
> Read `./Testing Strategy.md` to extract the primary test suite command. Run that exact command and return a summary of the results.

Once the task is complete, for each failing test, use todowrite to create a new fix task. Assign each task to an @general agent one at a time. Have the agent perform the necessary analysis and test code updates. Send the agent a prompt with an appropriate amount of detail.

Repeat until all tests pass.

---

## Phase 4 — Update Testing Strategy

Use todowrite to create the following task and assign it to @general:

> Update `./Testing Strategy.md` only:
> - Update the test count tracking metrics or layout to reflect the current number of tests per file.
> - Remove any entries from the coverage gaps section that are now successfully addressed.
> - Do not change any other sections unless source code changes have made them factually incorrect (e.g., a method signature changed).