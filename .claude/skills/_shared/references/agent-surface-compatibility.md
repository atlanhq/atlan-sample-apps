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
2. Use portable `repo://...` source URIs.
3. Keep deterministic logic in scripts; keep SKILL.md concise.
4. Use one-level reference links from SKILL.md.
5. Avoid machine-local paths and environment-specific assumptions.

## Standards references mirrored locally
- `source-mirror/application-sdk/agent-skills-docs/codex.md`
- `source-mirror/application-sdk/agent-skills-docs/open-agent.md`
- `source-mirror/application-sdk/agent-skills-docs/best-practices.md`
