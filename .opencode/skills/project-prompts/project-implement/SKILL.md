---
name: project-implement
description: Use this skill to implement code based on `Update.md`.
---
# Skill Instructions
Delegate the following task to @general:

Read `./Requirements.md` and `./Plan.md`.
Read `./Update.md`.
Read `./Testing Strategy.md`.

Use the gap assesment from `./Update.md` to update the code. Do not modify any Markdown files. Do not modify or execute anything in `./Tests/`. Break the work into sub-tasks and delegate them individually to @general, but do not write these sub-tasks to `TODOs.md` — they are working memory only. After all code changes are complete, run `python3 -m pytest Tests/ -v` and confirm all existing tests still pass. If any test fails, fix the source code (not the tests) before finishing.