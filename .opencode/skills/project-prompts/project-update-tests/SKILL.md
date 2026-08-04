---
name: project-update-tests
description: Use this skill to review and update the test suite after code changes.
---

# Skill Instructions

**Constraint:** Do not modify any core source files. Only modify files located within the test directories defined in `./Testing Strategy.md`. Use the `todowrite` tool to track all execution items.

⚠️ **STRICT AGENT BOUNDARY & ORCHESTRATION RULES:**
- You are acting SOLELY as an **orchestrator**. You must NOT perform direct work (file edits, code analysis, or terminal execution) in the main interface.
- All technical inspection, file updates, and shell executions MUST be delegated to an `@general` agent via `todowrite`.

**EXECUTION POLICY:** Perform workflow steps strictly in sequence. Do not spawn concurrent agents. Wait for each returned summary before proceeding.

---

## Phase 1 — Analyze

**Constraint:** You must execute these items sequentially. Do not batch them. Wait for the summary of each step before creating the next. You must NOT read the files to perform this analysis yourself—delegate everything to `@general`.

Use `todowrite` to create the following three analysis steps and assign each to @general. 

Include the following context in every delegation prompt:

- Read `./Testing Strategy.md` to locate the correct testing folders, metadata properties, and execution commands.
- Extract the primary execution command defined near the top of `./Testing Strategy.md` (e.g., `pytest ...`). ALWAYS run tests using this command or by targeting specific test files with this runner. **DO NOT run tests or execute code using `python -c '[code]'`.**
- Only modify files inside the identified test directories.
- Read `./Requirements.md` and **specifically Section 3 (Testing & Verification Status) of `./Plan.md`** before starting. Do not review core implementation tasks outside of this section.
- Return a written summary of findings, including a list of specific fixes needed.

### Item 1 — Coverage Gaps

> Read `./Testing Strategy.md`. Locate the designated testing folders. Compare behaviors specified in the behavioral specifications and coverage gaps sections of the testing documentation against the existing test files. For each specified behavior with no corresponding test, note it as a gap. New tests must go into the existing file that matches their coverage area — do not create new test files. Follow the standard configuration rules outlined in the testing documentation. Return a written summary with a list of specific gaps found.

**WAIT:** Do not proceed until Item 1 is complete and the summary is returned.

### Item 2 — Stale Tests

> Identify existing tests within the test directories that no longer match the current source code (e.g., outdated return values, removed methods, or changed signatures). Note each discrepancy with a description of what needs to change. Return a written summary with a list of specific staleness issues found.

**WAIT:** Do not proceed until Item 2 is complete and the summary is returned.

### Item 3 — Mocking Compliance

> Read `./Testing Strategy.md` to check if a mock verification script path is defined in the configuration parameters. If a verification script is specified and exists on disk, run it using the environment's appropriate interpreter. Otherwise, manually scan the test directory files to ensure mocking patterns match the compliance and intercept rules defined in `./Testing Strategy.md`. Note any violations. Return a written summary listing any violations found.

---

## Phase 2 — Fix & Verify

Once all three analysis steps are complete and their summaries are returned, use `todowrite` to create one item per finding. Assign each item to @general one at a time.

**Constraint:** You must create and execute these items one at a time. Wait for the agent to confirm the fix before moving to the next finding.

Each delegation prompt must include:

- The specific test file and block to add or modify (from the analysis summary).
- The constraint: only modify files inside the project's designated test directories.
- **Test Command Rule:** Read the primary test runner command at the top of `./Testing Strategy.md` (e.g., `pytest`). Extract and run that command against the modified test file (e.g., `pytest Tests/test_file.py`).
- **Iterative Verification:** After applying a fix, run the relevant test file command to verify the change. Continue adjusting the test until it passes cleanly.
- **Unresolvable Blockers & Bug Filing:** If a test fails due to a bug or limitation in core source code (which cannot be modified per constraints):
  1. Stop attempting to modify the test file.
  2. Gather the exact core code failure details, including steps to reproduce, expected vs. actual behavior, and affected source files.
  3. Formulate a structured bug summary and invoke/trigger the `project-bug-create` skill to log the issue into `./Bugs.md`.
  4. Mark the item as blocked due to an open core bug report.

**WAIT:** Do not begin Phase 3 until all fix items are marked complete or explicitly reported as blocked with a filed bug report.

---

## Phase 3 — Verify & Retest

**Constraint:** The orchestrator must not run test execution commands directly. Spawn an `@general` agent to execute all test runs and analyze failures.

1. **Initial Verification Run:**
   Use `todowrite` to create the following item and assign it to an `@general` agent:
   
   > Read `./Testing Strategy.md` to extract the primary test suite command from the top section of the file (e.g., `pytest Tests/`). Execute that exact command in the terminal. **Do not use `python -c` snippets.** Analyze the full test runner output. If all tests pass, return a summary confirming 100% pass rate. If any tests fail, list every failing test name, the specific assertion failure/error output, and the file location.
   
2. **Iterative Repair Loop:**
   If there are failing tests:
   
   - For each failure, use `todowrite` to create a separate work item assigned to an `@general` agent. 
   - Instruct `@general` to analyze the specific test failure, inspect the test file, apply the required fix within the test directory, and re-run the specific test using the extracted test runner command (e.g., `pytest Tests/test_file.py::test_name`) to confirm the fix works. **Do not use `python -c` snippets.**
   - If a test cannot pass because of a defect in core source implementation code, instruct `@general` to gather the details, invoke `project-bug-create` to file the bug report in `./Bugs.md`, and document the blocker.
   - Execute these fix items one at a time.
   
   **WAIT:** Do not proceed until both testing layers pass cleanly.
   
3. **Final Suite Validation:**
   Once all fix items are complete, assign a final step to an `@general` agent to **re-run the entire test suite execution command** extracted from `./Testing Strategy.md`. 
   
**WAIT:** Repeat this verification loop until an `@general` agent explicitly confirms that the **entire test suite runs and passes cleanly with zero failures** (or provides a summary of remaining failures that have been successfully logged to `./Bugs.md` via `project-bug-create`).

---

## Phase 4 — Update Testing Strategy

Use `todowrite` to create the following update item and assign it to @general:

> Update `./Testing Strategy.md` only:
> 
> - Update the test count tracking metrics or layout to reflect the current number of tests per file.
> - Remove any entries from the coverage gaps section that are now successfully addressed.
> - Do not change any other sections unless source code changes have made them factually incorrect (e.g., a method signature changed).