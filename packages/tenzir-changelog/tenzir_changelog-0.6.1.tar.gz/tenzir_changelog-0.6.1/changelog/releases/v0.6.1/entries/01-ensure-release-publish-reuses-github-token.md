---
title: Ensure release publish reuses GitHub token
type: bugfix
authors:
- codex
created: 2025-11-04
---

`release publish` now forwards the cached GitHub CLI token so the workflow scope is available even when the command runs through `uvx`.
