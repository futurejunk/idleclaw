---
name: "OPSX: Ship"
description: Commit and push all work from a completed change
category: Workflow
tags: [workflow, git, ship, experimental]
---

Commit and push all work from a completed or in-progress change.

**Input**: Optionally specify a change name (e.g., `/opsx:ship websocket-wiring`). If omitted, infer from conversation context. If ambiguous, prompt for selection.

**Steps**

1. **Identify the change**

   If a name is provided, use it. Otherwise:
   - Infer from conversation context if the user recently applied or archived a change
   - Run `openspec list --json` if needed and let the user select
   - Also check `openspec/changes/archive/` for recently archived changes

   Announce: "Shipping change: <name>"

2. **Find the change's artifacts for context**

   Look for the change in both active and archived locations:
   - `openspec/changes/<name>/`
   - `openspec/changes/archive/*-<name>/`

   Read the **proposal.md** (for the "Why") and **tasks.md** (for what was done) to understand the scope.

3. **Review git state**

   Run in parallel:
   - `git status` to see all changed/untracked files
   - `git diff --stat` to see a summary of changes
   - `git log --oneline -5` to see recent commits and follow commit style

4. **Stage files intelligently**

   - Stage all files related to the change (source code, specs, config, lock files)
   - **Exclude**: `.claude/`, `.cursor/`, `.env`, credentials, large binaries
   - Use specific `git add` commands, not `git add -A`
   - If unsure about a file, ask the user

5. **Draft commit message**

   Based on the proposal and completed tasks, write a commit message:
   - First line: short summary of the change (under 72 chars)
   - Blank line
   - Body: 2-4 sentences explaining what was built and why
   - End with: `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`

   Use a HEREDOC for proper formatting:
   ```bash
   git commit -m "$(cat <<'EOF'
   <message>

   Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
   EOF
   )"
   ```

6. **Ask before pushing**

   After the commit succeeds, show the commit hash and ask the user:
   > "Committed. Push to origin/main?"

   Use `AskUserQuestion` with options: "Push now" / "I'll push manually".

   Only run `git push` if the user explicitly chooses "Push now".

7. **Show summary**

   Display:
   - Change name
   - Commit hash and message
   - Files changed count
   - Push status (pushed / skipped)

**Output**

```
## Shipped: <change-name>

**Commit:** <hash> <first line of message>
**Files:** N files changed
**Pushed:** yes / skipped (you can run `git push`)

### Files included
- server/src/...
- frontend/src/...
- openspec/...
```

**Guardrails**
- Never commit `.env`, credentials, or secrets
- Never force push
- Always show the commit message before committing (let the user reject if needed)
- If there are no changes to commit, say so and stop
- Include openspec artifacts (archived changes, synced specs) in the commit
- NEVER push without explicit user confirmation
