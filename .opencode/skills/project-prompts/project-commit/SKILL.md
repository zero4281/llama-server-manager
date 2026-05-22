---
name: project-commit
description: Use this skill to verify test health, manage git branching conventions, and commit code changes safely.
---
# Skill Instructions
**Constraint:** Do not bypass failing tests. Commit messages must be exactly one sentence long. Branch names must follow the exact syntax specified in the execution guidelines. Use the todowrite tool to manage the commit lifecycle tracking.

⚠️ **AGENT BOUNDARY** — The orchestrator must NOT directly interact with the local shell, execute git commands, or run the test suite. All environmental inspection, verification execution, and repository modifications must be delegated to an @general agent.

**EXECUTION POLICY:** Perform lifecycle tasks strictly in sequence. If a preceding phase fails (e.g., test regressions or dirty validation issues), you must immediately halt the pipeline. Do not execute any subsequent git mutations or pushes.

---

## Phase 1 — Pre-Commit Testing Verification

Before attempting any version control actions, use todowrite to create a test verification task and assign it to @general.

> Read `./Testing Strategy.md` to extract the primary test suite execution command.
> Execute the full regression test suite using that exact command.
> Return the final test status to the orchestrator.
> 
> **CRITICAL:** If any tests fail, report the failures immediately and abort the workflow. Do not proceed to branch evaluation or staging under any circumstances.

**WAIT:** Do not proceed to Phase 2 until the test verification task is marked complete and runs completely green.

---

## Phase 2 — Branch Management Analysis

Once tests are verified to pass, use todowrite to create a branch assessment task and assign it to @general. Pass the configuration version number provided by the orchestrator context.

> Inspect the current local repository git state.
> 1. Identify the current active branch name.
> 2. If the current branch is `main`, automatically determine an appropriate branch type prefix (`feature/` or `bugfix/`) and construct a new branch using the exact format: `[feature/bugfix]/[Version-from-orchestrator]-[short-description]` (e.g., `feature/v1.1-user-confirmation-flows`). Create and switch to this new branch.
> 3. If the repository is already checked out to a feature or bugfix branch (any branch other than `main`), continue using that active branch without creating a new one.
> 
> Return the final confirmed branch name back to the orchestrator.

**WAIT:** Do not proceed until the branch status has been confirmed and returned.

---

## Phase 3 — Stage, Document, and Commit

Use todowrite to create the staging and commit generation task and assign it to @general.

> 1. Check `git status` and scan for untracked artifacts using `git ls-files --others --exclude-standard` to ensure all relevant files are captured.
> 2. Ingest the modifications made to the codebase and auto-generate a git commit message. 
> 
> **CRITICAL CONSTRAINT:** The final commit message must be exactly one sentence long. No multi-line breaks, paragraphs, or lists.
> 
> 3. Stage the files, execute the git commit using the single-sentence message, and push the active branch to the remote repository. 
> 
> Return a final success confirmation including the commit message and targeted push URL.