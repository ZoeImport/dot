---
name: beatutifycodex
description: Maintain and migrate Codex CLI and Codex Desktop configuration, skills, MCP servers, plugins, connectors, and related agent settings. Use when the user says beatutifycodex, beautifycodex, migrate Codex Desktop to Codex CLI, sync Codex skills, sync Codex MCPs, sync Codex plugins, migrate Claude Code or Claude Desktop or OpenCode config into Codex CLI, audit Codex config, repair Codex config, or maintain Codex config files.
---

# Beatutifycodex

Maintain Codex CLI and Codex Desktop configuration without losing existing skills, MCP servers, plugins, connectors, or related agent settings.

## Core Rules

- Treat config migration as a merge, not a blind overwrite.
- Read current source and target files before editing anything.
- Back up any target file before changing it unless the user explicitly says not to.
- Do not copy secrets into shared repos or logs. Preserve local secrets only in local config files.
- Never remove an existing skill, MCP, plugin, connector, provider, or model route unless the user explicitly asks for removal.
- When copying MCP servers, classify database or business MCPs as sensitive and ask before moving them.
- Use JSON parsers for JSON config. Do not edit JSON with ad hoc text replacement.
- Prefer exact local paths discovered on the current machine over remembered platform defaults.

## Config Locations To Inspect

Discover paths first. Common macOS locations include:

- Codex CLI: `~/.codex/`, especially `~/.codex/config.toml`, `~/.codex/skills/`, `~/.codex/plugins/`, `~/.codex/plugins/cache/`
- Codex Desktop bundled or cached skills/plugins: `~/.codex/skills/`, `~/.codex/plugins/`, and app-managed plugin cache under `~/.codex/plugins/cache/`
- Personal shared skills: `~/.agents/skills/`
- Claude Code: `~/.claude/settings.json`, `~/.claude.json`
- Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json`
- OpenCode: `~/.config/opencode/opencode.json`, `~/.config/opencode/oh-my-openagent.json`, and macOS app support equivalents if present
- Dot backup repo when relevant: `~/CodeSpace/dot/`

If a location is missing, record it as absent and continue with the locations that exist.

## Workflow

1. Inventory
   - List Codex CLI, Codex Desktop, Claude Code, Claude Desktop, OpenCode, and personal skill locations that exist.
   - For each location, summarize skills, MCP server names, plugin names, provider/model config, and key config files.
   - Avoid printing secret values. Show only key names and redacted summaries.

2. Decide sources and target
   - Treat Codex CLI as the target unless the user says otherwise.
   - Treat Codex Desktop, Claude Code, Claude Desktop, OpenCode, and `~/.agents/skills` as possible sources.
   - If multiple sources define the same MCP or plugin name with different commands or args, show the diff and ask before choosing.

3. Back up target files
   - Create timestamped backups beside the target files, for example `config.toml.bak-YYYYMMDD-HHMMSS`.
   - For directories, prefer a backup manifest plus copying only changed files when possible.

4. Migrate skills
   - Copy user-authored skills into a Codex CLI discoverable skill directory.
   - Preserve each skill folder name and `SKILL.md`.
   - Do not copy generated caches unless the user explicitly wants cached plugin content migrated.
   - If duplicate skill names exist, compare `SKILL.md` and ask before overwriting.

5. Migrate MCPs
   - Extract MCP definitions from Claude Desktop and Claude Code sources.
   - Separate general tool MCPs from database/business MCPs.
   - Ask before migrating sensitive MCPs that include connection strings, credentials, internal hosts, or business database names.
   - Convert into the Codex CLI config format only after verifying the target file structure.

6. Migrate plugins and connectors
   - Inspect Codex plugin directories and manifests before copying.
   - Prefer installed plugin metadata over cache internals when both exist.
   - Preserve plugin ids, versions, and local manifests.
   - If the Codex CLI has a plugin install mechanism available, prefer installing or registering over raw copying.

7. Migrate providers and model routing
   - Read OpenCode and OhMyOpenAgent configs as separate sources.
   - Preserve provider/model names, fallback routes, and base URLs locally.
   - Do not write real API keys to dot repos or shared artifacts.
   - If provider formats differ, create a compatibility summary and ask before transforming.

8. Validate
   - Parse all edited JSON/TOML/YAML files with appropriate tools.
   - Run available Codex CLI diagnostic commands if present.
   - Report exactly what was changed, what was skipped, and what still needs user confirmation.

## Conflict Handling

Ask before editing when:

- A target entry exists with a different command, args, URL, provider, or plugin version.
- A source contains credentials or business/database connection details.
- A migration requires installing network dependencies.
- The correct Codex CLI config format cannot be verified locally.

Proceed without asking when:

- Copying a missing non-sensitive user skill into a discoverable Codex skill directory.
- Adding a missing general-purpose MCP with no credentials or business-specific values.
- Creating backups or validation reports.

## Useful Commands

Use these as starting points and adapt to the discovered machine:

```bash
find "$HOME/.codex" "$HOME/.agents/skills" "$HOME/.claude" -maxdepth 3 -type f 2>/dev/null
```

```bash
python3 -m json.tool "$HOME/.claude.json" >/dev/null
```

```bash
python3 -m json.tool "$HOME/Library/Application Support/Claude/claude_desktop_config.json" >/dev/null
```

For TOML validation, use Python `tomllib` when available:

```bash
python3 -c "import tomllib; tomllib.load(open('$HOME/.codex/config.toml','rb')); print('config.toml OK')"
```
