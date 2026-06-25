---
name: project-bug-create
description: Use this skill to triage, analyze, and document new issues in the Bugs.md file.
---
# Skill Instructions
instructions: |
  1. **Preparation**:
     - Read `./Requirements.md`, `./Plan.md`, `./Testing Strategy.md`, and `./Bugs.md`.

  2. **User Interaction**:
     - Prompt the user for a clear, concise description of the issue using AskUserQuestion.
     - Optional: Ask the user to estimate severity or provide specific reproduction steps if they are known.

  3. **Analysis & Drafting**:
     - Delegate to @general. 
     - Give @general the users bug report.
     - **Constraint**: Provide the following instructions to @general:
       - Check `./Bugs.md` to ensure the bug is not a duplicate.
       - Analyze `./Requirements.md` and `./Plan.md` to identify dependencies and affected components.
       - Read `./Testing Strategy.md` to determine if a new test case is required to reproduce/verify the bug.
       - Read relevant code files to provide context.
       - **CRITICAL**: Perform NO code changes, refactoring, or bug fixes. This is a documentation-only task.
     - Request @general to draft the entry for `./Bugs.md`.

  4. **Verification**:
     - Review the drafted entry provided by @general.
     - Ensure the entry includes:
       - Clear Title
       - Severity/Priority
       - Dependencies
       - Reproduction steps
     - Use AskUserQuestion to present the draft to the user for approval.

  5. **Finalization**:
     - Once approved, append the new item to the 'Current Bug Reports' section of `./Bugs.md`.
     - Once approved, update the 'Project Roadmap' section of `./Bugs.md`.
     - Confirm to the user that the bug has been tracked and is ready for the `project-bug-fix` process.