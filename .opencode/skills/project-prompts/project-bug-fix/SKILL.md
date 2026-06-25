---
name: project-bug-fix
description: Use this skill to select, implement, verify, and document fixes for items in the Bugs.md file.
---
# Skill Instructions
instructions: |
  1. **Preparation**: 
     - Read `./Requirements.md`, `./Plan.md`,`./Testing Strategy.md`, and `./Bugs.md`.
     - Parse `./Bugs.md` to build a list of pending tasks. Ignore completed items.

  2. **User Interaction**:
     - Present the list (titles, priority, and dependencies) to the user via AskUserQuestion.
     - Wait for the user to select an item.

  3. **Delegation**:
     - Print out: "Starting work on [Bug Title]."
     - Delegate to @general immediately following the notification.
     - **Constraint**: You must provide the following context in the prompt: 
       - The full bug description from `./Bugs.md`.
       - Relevant files identified from `./Requirements.md`, `./Plan.md`, and `./Testing Strategy.md`.
       - The expected outcome/behavior.

  4. **Verification & Testing**:
     - Delegate to @general. 
     - Once @general reports completion, verify:
       - The changes address the bug (manual inspection of the diff).
       - Run `python3 -m pytest Tests/ -v`.
     - **Error Handling**: If tests fail, provide the error output to @general and request a fix. Repeat until tests pass.

  5. **Finalization**:
     - Create a brief summary of the changes made.
     - Update `./Bugs.md` to mark the item as complete.