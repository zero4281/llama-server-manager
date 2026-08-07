---
name: project-commit
description: Use this skill to verify test health, manage git branching conventions, and commit code changes safely.
---

# Skill Instructions

**Constraint:** Do not bypass failing tests. Use the `todowrite` tool to manage commit lifecycle tracking.

⚠️ **STRICT AGENT BOUNDARY & ORCHESTRATION RULES:**
- You are acting SOLELY as an **orchestrator**. You must NOT perform direct work (file edits, code analysis, or terminal execution) in the main interface.
- All technical inspection, file updates, and shell executions MUST be delegated to an `@general` agent via `todowrite`.

**EXECUTION POLICY:** Perform lifecycle steps strictly in sequence. If a preceding phase fails (e.g., test regressions or dirty validation issues), halt the pipeline immediately. Do not execute any subsequent git mutations or pushes.

---

## Phase 1 — Pre-Commit Testing Verification

Before attempting any version control actions, use `todowrite` to create a test verification step and assign it to @general.

> Read `./Testing Strategy.md` to extract the primary test suite execution command.
> Execute the full regression test suite using that exact command.
> Return the final test status to the orchestrator.
> 
> **CRITICAL:** If any tests fail, report the failures immediately and abort the workflow. Do not proceed to branch evaluation or staging under any circumstances.

**WAIT:** Do not proceed to Phase 2 until the test verification step is marked complete and runs completely green.

---

## Phase 2 — Branch Management Analysis

Once tests are verified to pass, use `todowrite` to create a branch assessment step and assign it to @general.

> Read the current version number from `./Plan.md`.
> Inspect the current local repository git state.
> 1. Identify the current active branch name.
> 2. If the current branch is `main`:
>    - Execute `git diff HEAD -- Bugs.md` (or check uncommitted/staged diffs for `Bugs.md`).
>    - Determine the branch type prefix: select `bugfix/` if `Bugs.md` has been modified and any bug entry was marked as completed (e.g., status updated to `RESOLVED`). Otherwise, select `feature/`.
>    - Construct a new branch using the exact format: `[feature/bugfix]/[Extracted-Version]-[short-description]` (e.g., `bugfix/v1.0.7-fix-install-titles` or `feature/v1.0.7-user-confirmation-flows`).
>    - Create and switch to this new branch.
> 3. If the repository is already checked out to a feature or bugfix branch (any branch other than `main`), continue using that active branch without creating a new one.
> 
> Return the final confirmed branch name back to the orchestrator.

**WAIT:** Do not proceed until the branch status has been confirmed and returned.

---

## Phase 3 — Stage, Document, and Commit

Use `todowrite` to create the staging and commit generation step and assign it to @general.

> 1. Check `git status` and scan for untracked artifacts using `git ls-files --others --exclude-standard` to ensure all relevant files are captured.
> 2. Ingest the modifications made to the codebase and auto-generate a git commit message.
> 
> **COMMIT MESSAGE CONSTRAINT:** The commit subject (first line) must be concise (maximum 72 characters) suitable for use as a Pull Request title. Optionally, include a brief body description below a blank line for necessary context. Avoid long lists or multi-paragraph blocks.
> 
> 3. Stage the files, execute the git commit, and push the active branch to the remote repository.
> 
> Return a final success confirmation including the commit message and targeted push URL.