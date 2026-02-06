# Agent Surface Compatibility

This skill pack is designed for both Codex and Claude Code.

## Skill roots
- Codex: `.agents/skills`
- Claude Code: `.claude/skills`

## Sync command
Run after any update:
`python ../scripts/sync_claude_skills.py`

## Authoring rules for cross-agent compatibility
1. Keep YAML frontmatter minimal: `name`, `description`.
2. Keep deterministic logic in scripts; keep `SKILL.md` concise.
3. Use one-level reference links from `SKILL.md`.
4. Avoid machine-local absolute paths and hardcoded workstation assumptions.
5. Fetch source context on demand from available repos.
