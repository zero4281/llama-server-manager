---
name: project-commit
description: Use this skill to commit code to a branch.
---
# Skill Instructions
Delegate the following task to @general:

First, run `python3 -m pytest Tests/ -v`. If any tests fail, stop and report the failures — do not commit. If all tests pass, proceed: if the project is on the main branch then create a new branch with the format `[feature/bugfix]/[version]-[short-description]` (e.g. `feature/v1.1-user-confirmation-flows`). If the project is already in a feature branch (not the main branch) then continue without creating a branch. Check `git status`, use `git ls-files --others --exclude-standard` to find new files, then create a git commit message. Make sure the commit message is only one sentence long. Then commit the update and push the commit.