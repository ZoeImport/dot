---
name: memory-load
description: Use when user asks about past sessions, asks "what did we find about X", or wants to recall saved memories. Do NOT auto-load at session start — load only on explicit user request.
---

# Memory Load

Load session memories on demand. This skill runs **only when the user explicitly asks** to recall past findings, decisions, or knowledge. It never auto-loads at session start or runs in the background.

---

## Overview

Session memories are stored per-repository as flat markdown files. An `INDEX.md` catalogs all subjects. The rule is simple: **load INDEX first, then load specific subjects.** Never load all subject files at once.

---

## Usage

All loading goes through the `cli` command:

**List INDEX (always first):**
```
cli memory list --repo <name>
```
Shows the INDEX table with all subjects, their keyword tags, entry counts, and last accessed dates.

**List subjects with stats:**
```
cli memory list --repo <name>
```
Same as above — use this to find which subject matches the user's question.

**Load a specific subject:**
```
cli memory load --repo <name> --subject <topic>
```
Loads exactly one subject file. The topic name matches the INDEX row.

**Search across subjects:**
```
cli memory search --repo <name> --keyword <keyword>
```
Searches all subject files without loading them. Useful when the user isn't sure which subject covers what they need.

---

## Storage Location

```
~/.claude/memory/<repo_name>/
  INDEX.md             -> index of all subjects
  auth.md              -> subject file
  deployment.md        -> subject file
  ...
```

---

## Behavior

1. User asks a question like "what did we find about authentication?"
2. Check if INDEX is already loaded. If not, run `cli memory list --repo <name>`.
3. Find the matching subject from the INDEX table.
4. Load only that subject: `cli memory load --repo <name> --subject <topic>`.
5. Use the loaded content to answer the user.

If the user asks broadly ("what do we know about X?"), use `search` first to narrow down.

---

## Common Mistakes

- **Loading all subjects at once.** Do not do this. It wastes context and makes the INDEX pointless. Always check INDEX first, then load one specific subject.
- **Skipping the INDEX.** Without INDEX you don't know what's available. Always start there.
- **Auto-loading at session start.** This skill is manual only. Never trigger it proactively.
- **Loading a subject that doesn't exist.** Always verify the subject name exists in INDEX before loading.
