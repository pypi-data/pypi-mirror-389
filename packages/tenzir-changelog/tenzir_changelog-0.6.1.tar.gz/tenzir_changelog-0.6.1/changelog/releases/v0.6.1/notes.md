Forward the GitHub CLI token so release publish works via uvx.

## 🐞 Bug fixes

### Ensure release publish reuses GitHub token

`release publish` now forwards the cached GitHub CLI token so the workflow scope is available even when the command runs through `uvx`.

*By @codex.*
