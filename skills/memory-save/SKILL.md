---
name: memory-save
description: Use when user explicitly says "remember this", "save this", "记住这个", or asks to persist a finding, decision, or lesson. Only save on direct request — never without asking.
---

# Memory Save — Explicit Save-Only Skill

Save session knowledge to persistent memory files. **Never writes without a direct request.** Only saves when the user explicitly asks.

---

## Trigger Phrases

Only act on direct user requests. Look for phrases like:

- "remember this" / "remember that"
- "save this" / "save that"
- "记住这个" / "记一下"
- "keep this somewhere"
- "write this down"
- "make a note"
- "record this"
- Any other explicit instruction to persist information

**Do not infer.** If the user did not say one of these (or an obvious equivalent), do not save.

---

## Usage

```bash
cli memory save --repo <repo-name> --subject <topic> --type <section> --tags "tag1, tag2" <content>
```

| Flag | Required | Description |
|------|----------|-------------|
| `--repo` | Yes | Repository or project name (kebab-case) |
| `--subject` | Yes | Topic name, matches the filename stem (kebab-case) |
| `--type` | Yes | Section type (see Allowed Types below) |
| `--tags` | No | Comma-separated search tags |
| `--star` | No | Pins the subject (sets starred=1.0, affects attention score) |
| `--score` | No | Override AI relevance weight (0.0–1.0, default computed) |
| `<content>` | Yes | The memory entry text |

---

## Allowed Types

These map to sections in the subject memory file:

| Type | Section | When to Use |
|------|---------|-------------|
| `findings` | Findings | Confirmed facts, resolved decisions, verified behavior |
| `hypotheses` | Hypotheses | Guesses, theories under investigation, unconfirmed patterns |
| `questions` | Open Questions | Unresolved questions, unknowns, things to investigate later |
| `tools` | Tools & Techniques | CLI commands, shortcuts, workflows, debugging tricks |
| `ideas` | Ideas | Feature suggestions, improvements, proposals |
| `mistakes` | Mistakes | Errors made, their impact, and the lesson learned |

---

## Storage Location

```
~/.claude/memory/<repo>/<subject>.md
~/.agents/memory/<repo>/<subject>.md    (mirror for OpenCode)
```

Each repository gets a flat directory. See `~/.claude/memory/<repo>/INDEX.md` for the catalog.

---

## Attention Score Formula

When saving, consider whether to set `--star` or adjust `--score`.

The attention score in INDEX.md is:

```
score = load_freq * 0.3 + recency * 0.3 + starred * 0.2 + ai_weight * 0.2
```

| Variable | Range | Description |
|----------|-------|-------------|
| `load_freq` | 0.0–1.0 | How often this file is loaded per session |
| `recency` | 0.0–1.0 | How recently it was accessed (1.0 = today) |
| `starred` | 0.0 or 1.0 | Human-pinned via `--star` flag |
| `ai_weight` | 0.0–1.0 | AI-assigned relevance, can be set via `--score` |

Use `--star` when the user sounds emphatic ("this is really important"). Use `--score` when the topic is unusually relevant to future work (e.g., 0.9 for a critical architectural decision, 0.3 for a minor note).

---

## Privacy Rules

- **Never** save secrets, passwords, API keys, tokens, or any credentials
- **Never** save personally identifiable information (PII)
- **Never** save internal URLs or server addresses unless explicitly asked
- When in doubt, ask the user: "This contains sensitive data — should I save it?"

---

## Common Mistakes

| Mistake | Why It Is Wrong |
|---------|-----------------|
| Saving without being asked | Wastes tokens, fills memory with noise. Only save on direct request. |
| Saving trivial details | "Used `ls` command" is not worth persisting. Save things with lasting value. |
| Saving temporary info | A bug that was fixed in the same session does not need a memory entry. |
| Omitting tags | Tags make memory searchable. Without them, entries are hard to find. |
| Using wrong type | A confirmed fact in "Hypotheses" breaks the convention. |
| Saving too much context | One sentence per entry. Link to code/files instead of copying them. |
| Saving session summaries without request | The user did not ask. Do not save end-of-session summaries unless requested. |

---

## No Unprompted Saves

**This skill only writes on explicit request.** There is no background process, no save-on-exit, no periodic flush, no hooks, no logging. If the user did not explicitly request a save, do not save. Silence on this topic means no save.
