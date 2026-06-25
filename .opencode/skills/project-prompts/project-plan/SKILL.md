---
name: project-plan
description: Use this skill to generate `Plan.md` based on `Requirements.md`.
---
# Skill Instructions
Delegate the following task to @general:

`./Requirements.md` has been updated. `./Plan.md` is the implementation plan for this project. Read `./Requirements.md`, `./Plan.md`, and `./Update.md`, then read the code to verify that `./Plan.md` is up to date with the requirements. Update `./Plan.md` with the new requirements. If `./Update.md` exists and its gap assessment is now inconsistent with the updated plan, delete its contents and add a single line: "Update.md is stale — re-run /project-update."