# Agent Skills

Use agent skills to extend Codex with task-specific capabilities. A skill packages instructions, resources, and optional scripts so Codex can follow a workflow reliably. You can share skills across teams or with the community. Skills build on the [open agent skills standard](https://agentskills.io).

Skills are available in both the Codex CLI and IDE extensions.

## Agent skill definition

A skill captures a capability expressed through Markdown instructions in a `SKILL.md` file. A skill folder can also include scripts, resources, and assets that Codex uses to perform a specific task.

<FileTree
  class="mt-4"
  tree={[
    {
      name: "my-skill/",
      open: true,
      children: [
        {
          name: "SKILL.md",
          comment: "Required: instructions + metadata",
        },
        {
          name: "scripts/",
          comment: "Optional: executable code",
        },
        {
          name: "references/",
          comment: "Optional: documentation",
        },
        {
          name: "assets/",
          comment: "Optional: templates, resources",
        },
        {
          name: "agents/",
          open: true,
          children: [
            {
              name: "openai.yaml",
              comment: "Optional: appearance and dependencies",
            },
          ],
        },
      ],
    },

]}
/>

Skills use **progressive disclosure** to manage context efficiently. At startup, Codex loads the name and description of each available skill. Codex can then activate and use a skill in two ways:

1. **Explicit invocation:** You include skills directly in your prompt. To select one, run the `/skills` slash command, or start typing `$` to mention a skill. Codex web and iOS don't support explicit invocation yet, but you can still ask Codex to use any skill checked into a repo.

<div class="not-prose my-2 mb-4 grid gap-4 lg:grid-cols-2">
  <div>
    <img src="https://developers.openai.com/images/codex/skills/skills-selector-cli-light.webp"
      alt=""
      class="block w-full lg:h-64 rounded-lg border border-default my-0 object-contain bg-[#F0F1F5] dark:hidden"
    />
    <img src="https://developers.openai.com/images/codex/skills/skills-selector-cli-dark.webp"
      alt=""
      class="hidden w-full lg:h-64 rounded-lg border border-default my-0 object-contain bg-[#1E1E2E] dark:block"
    />
  </div>
  <div>
    <img src="https://developers.openai.com/images/codex/skills/skills-selector-ide-light.webp"
      alt=""
      class="block w-full lg:h-64 rounded-lg border border-default my-0 object-contain bg-[#E8E9ED] dark:hidden"
    />
    <img src="https://developers.openai.com/images/codex/skills/skills-selector-ide-dark.webp"
      alt=""
      class="hidden w-full lg:h-64 rounded-lg border border-default my-0 object-contain bg-[#181824] dark:block"
    />
  </div>
</div>

2. **Implicit invocation:** Codex can decide to use an available skill when your task matches the skill's description.

In either method, Codex reads the full instructions of the invoked skills and any extra references checked into the skill.

## Where to save skills

Codex reads from `.agents/skills` in your `$HOME / ~` folder and in git repositories. If multiple skills share the same `name`, Codex does not deduplicate them, and both can appear in skill selectors.

| Skill Scope | Location                                                                                                  | Suggested use                                                                                                                                                                                        |
| :---------- | :-------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `REPO`      | `$CWD/.agents/skills` <br /> Current working directory: where you launch Codex.                           | If you're in a repository or code environment, teams can check in skills relevant to a working folder. For example, skills only relevant to a microservice or a module.                              |
| `REPO`      | `$CWD/../.agents/skills` <br /> A folder above CWD when you launch Codex inside a Git repository.         | If you're in a repository with nested folders, organizations can check in skills relevant to a shared area in a parent folder.                                                                       |
| `REPO`      | `$REPO_ROOT/.agents/skills` <br /> The topmost root folder when you launch Codex inside a Git repository. | If you're in a repository with nested folders, organizations can check in skills relevant to everyone using the repository. These serve as root skills available to any subfolder in the repository. |
| `USER`      | `$HOME/.agents/skills` <br /> Any skills checked into the user's personal folder.                         | Use to curate skills relevant to a user that apply to any repository the user may work in.                                                                                                           |
| `ADMIN`     | `/etc/codex/skills` <br /> Any skills checked into the machine or container in a shared, system location. | Use for SDK scripts, automation, and for checking in default admin skills available to each user on the machine.                                                                                     |
| `SYSTEM`    | Bundled with Codex by OpenAI.                                                                             | Useful skills relevant to a broad audience such as the skill-creator and plan skills. Available to everyone when they start Codex.                                                                   |

Codex supports symlinked skill folders and follows the symlink target when scanning these locations.

## Enable or disable skills

Installed skills can be enabled or disabled in `~/.codex/config.toml`. Use `[[skills.config]]` entries to disable a skill without deleting it, then restart Codex:

```toml
[[skills.config]]
path = "/path/to/skill"
enabled = false
```

## Create a skill

To create a new skill, use the built-in `$skill-creator` skill in Codex. Describe what you want your skill to do, and Codex will start bootstrapping your skill.

If you also install `$create-plan` (experimental) with `$skill-installer install the create-plan skill from the .experimental folder`, Codex will create a plan for your skill before it writes files.

For a step-by-step guide, see [Create custom skills](https://developers.openai.com/codex/skills/create-skill).

You can also create a skill manually by creating a folder with a `SKILL.md` file inside a valid skill location. A `SKILL.md` must contain a `name` and `description` to help Codex select the skill:

```md
---
name: skill-name
description: Description that helps Codex select the skill
---

Skill instructions for the Codex agent to follow when using this skill.
```

Codex skills build on the [agent skills specification](https://agentskills.io/specification). Check out the documentation to learn more.

## Install new skills

To install more than the built-in skills, you can download skills from a [curated set of skills on GitHub](https://github.com/openai/skills) using the `$skill-installer` skill:

```bash
$skill-installer install the linear skill from the .experimental folder
```

You can also prompt the installer to download skills from other repositories.

After installing a skill, restart Codex to pick up new skills.

## Skill examples

### Plan a new feature

`$create-plan` is an experimental skill that you can install with `$skill-installer` to have Codex research and create a plan to build a new feature or solve a complex problem:

```bash
$skill-installer install the create-plan skill from the .experimental folder
```

### Access Linear context for Codex tasks

```bash
$skill-installer install the linear skill from the .experimental folder
```

<div class="not-prose my-4">
  <video
    class="w-full rounded-lg border border-default"
    controls
    playsinline
    preload="metadata"
  >
    <source
      src="https://cdn.openai.com/codex/docs/linear-example.mp4"
      type="video/mp4"
    />
  </video>
</div>

### Have Codex access Notion for more context

```bash
$skill-installer notion-spec-to-implementation
```

<div class="not-prose my-4">
  <video
    class="w-full rounded-lg border border-default"
    controls
    playsinline
    preload="metadata"
  >
    <source
      src="https://cdn.openai.com/codex/docs/notion-spec-example.mp4"
      type="video/mp4"
    />
  </video>
</div>


# Create skills

[Skills](https://developers.openai.com/codex/skills) let teams capture institutional knowledge and turn it into reusable, shareable workflows. Skills help Codex behave consistently across users, repositories, and sessions, which is especially useful when you want standard conventions and checks applied automatically.

A **skill** is a small bundle consisting of a `name`, a `description` that explains what it does and when to use it, and an optional body of instructions. Codex injects only the skill's name, description, and file path into the runtime context. The instruction body is never injected unless the skill is explicitly invoked.

## Decide when to create a skill

Use skills when you want to share behavior across a team, enforce consistent workflows, or encode best practices once and reuse them everywhere.

Typical use cases include:

- Standardizing code review checklists and conventions
- Enforcing security or compliance checks
- Automating common analysis tasks
- Providing team-specific tooling that Codex can discover automatically

Avoid skills for one-off prompts or exploratory tasks, and keep skills focused rather than trying to model large multi-step systems.

## Create a skill

### Use the skill creator

Codex ships with a built-in skill to create new skills. Use this method to receive guidance and iterate on your skill.

Invoke the skill creator from within the Codex CLI or the Codex IDE extension:

```text
$skill-creator
```

Optional: add context about what you want the skill to do.

```text
$skill-creator

Create a skill that drafts a conventional commit message based on a short summary of changes.
```

The creator asks what the skill does, when Codex should trigger it automatically, and the run type (instruction-only or script-backed). Use instruction-only by default.

When writing or revising a skill, treat the YAML frontmatter `description` as agent-facing metadata. The description is used by the agent to decide when to use the skill based on the user's prompt. Thus, the description should be explicit: describe what kinds of requests should trigger the skill, and what should not. Vague descriptions can cause over-triggering during implicit invocation. When editing a `SKILL.md` file manually, use the Skill Creator (`$skill-creator`) skill to update the YAML frontmatter `description` based on the contents of the skill.

The output is a `SKILL.md` file with a name, description, and instructions. If needed, it can also scaffold scripts and other optional resources.

### Create a skill manually

Use this method when you want full control or are working directly in an editor.

1. Choose a location (repo-scoped or user-scoped).

   ```shell
   # User-scoped skill (macOS/Linux default)
   mkdir -p ~/.agents/skills/<skill-name>

   # Repo-scoped skill (checked into your repository)
   mkdir -p .agents/skills/<skill-name>
   ```

2. Create `SKILL.md`.

   ```md
   ---
   name: <skill-name>
   description: <what it does and when to use it>
   ---

   <instructions, references, or examples>
   ```

3. Restart Codex to load the skill.

## Understand the skill format

Skills use YAML front matter plus an optional body. Required fields are `name` (non-empty, at most 100 characters, single line) and `description` (non-empty, at most 500 characters, single line). Codex ignores extra keys. The body can contain any Markdown, stays on disk, and isn't injected into the runtime context unless explicitly invoked.

Along with inline instructions, skill directories often include:

- Scripts (for example, Python files) to perform deterministic processing, validation, or external tool calls
- Templates and schemas such as report templates, JSON/YAML schemas, or configuration defaults
- Reference data like lookup tables, prompts, or canned examples
- Documentation that explains assumptions, inputs, or expected outputs

<FileTree
  class="mt-4"
  tree={[
    {
      name: "my-skill/",
      open: true,
      children: [
        {
          name: "SKILL.md",
          comment: "Required: instructions + metadata",
        },
        {
          name: "scripts/",
          comment: "Optional: executable code",
        },
        {
          name: "references/",
          comment: "Optional: documentation",
        },
        {
          name: "assets/",
          comment: "Optional: templates, resources",
        },
        {
          name: "agents/",
          open: true,
          children: [
            {
              name: "openai.yaml",
              comment: "Optional: appearance and dependencies",
            },
          ],
        },
      ],
    },
  ]}
/>

The skill's instructions reference these resources, but they remain on disk, keeping the runtime context small and predictable.

For real-world patterns and examples, see [agentskills.io](https://agentskills.io) and check out the skills catalog at [github.com/openai/skills](https://github.com/openai/skills).

## Choose where to save skills

Codex loads skills from these locations (repo, user, admin, and system scopes). Choose a location based on who should get the skill:

- Save skills in your repository's `.agents/skills/` when they should travel with the codebase.
- Save skills in your user skills directory when they should apply across all repositories on your machine.
- Use admin/system locations only in managed environments (for example, when loading skills on shared machines).

For the full list of supported locations and precedence, see the "Where to save skills" section on the [Skills overview](https://developers.openai.com/codex/skills#where-to-save-skills).

## See an example skill

```md
---
name: draft-commit-message
description: Draft a conventional commit message when the user asks for help writing a commit message.
---

Draft a conventional commit message that matches the change summary provided by the user.

Requirements:

- Use the Conventional Commits format: `type(scope): summary`
- Use the imperative mood in the summary (for example, "Add", "Fix", "Refactor")
- Keep the summary under 72 characters
- If there are breaking changes, include a `BREAKING CHANGE:` footer
```

Example prompt that triggers this skill:

```text
Help me write a commit message for these changes: I renamed `SkillCreator` to `SkillsCreator` and updated the sidebar.
```

Check out more example skills and ideas in the [github.com/openai/skills](https://github.com/openai/skills) repository.

## Follow best practices

- Write the `description` for the agent, not for humans.
  - Define explicit scope boundaries in `description`: when to use the skill.
  - This helps prevent over-triggering with implicit invocation based on the user's prompt.
- Keep skills small. Prefer narrow, modular skills over large ones.
- Prefer instructions over scripts. Use scripts only when you need determinism or external data.
- Assume no context. Write instructions as if Codex knows nothing beyond the input.
- Avoid ambiguity. Use imperative, step-by-step language.
- Test triggers. Verify your example prompts activate the skill as expected.

## Advanced configuration

To create the best experience for a skill in Codex, you can provide additional metadata for your skill inside an `agents/openai.yaml` file.

Within the file you can configure the visual appearance of the skill inside the [Codex app](https://developers.openai.com/codex/app) and declare dependencies for MCPs the skill requires.

```yaml
interface:
  display_name: "Optional user-facing name"
  short_description: "Optional user-facing description"
  icon_small: "./assets/small-logo.svg" # relative of the skill's main directory
  icon_large: "./assets/large-logo.png" # relative from the skill's main directory
  brand_color: "#3B82F6"
  default_prompt: "Optional surrounding prompt to use the skill with"

dependencies:
  tools:
    - type: "mcp" # MCPs defined here will be installed when the skill is used and OAuth flows are triggered
      value: "openaiDeveloperDocs"
      description: "OpenAI Docs MCP server"
      transport: "streamable_http"
      url: "https://developers.openai.com/mcp"
```

### Icon requirements

**Small icon**

- File type: `svg`
- Size: `16px` &times; `16px`
- Color: Use a fill of `currentColor`. The system will automatically adjust the color based on the theme

**Large icon**

- File type: `png` or `jpg`
- Size: `100px` &times; `100px`
- Color: Solid colored background

### Tool dependencies

**Model Context Protocol**

If you define a tool dependency of type `mcp`, Codex will automatically try to detect that MCP when the skill gets called by checking for the name declared in the `value` property. If the MCP has to be installed and requires OAuth, Codex will automatically start an authentication flow.

## Troubleshoot skills

### Skill doesn’t appear

If a skill doesn’t show up in Codex, make sure you enabled skills and restarted Codex. Confirm the file name is exactly `SKILL.md` and that it lives under a supported path.

If you’ve disabled a skill in `~/.codex/config.toml`, remove or flip the matching `[[skills.config]]` entry and restart Codex.

If you use symlinked directories, confirm the symlink target exists and is readable. Codex also skips skills with malformed YAML or `name`/`description` fields that exceed the length limits.

### Skill doesn’t trigger

If a skill loads but doesn’t run automatically, the most common issue is an unclear trigger. Make sure the `description` explicitly states when to use the skill, and test with prompts that match that description.

If two or more skills overlap in intent, narrow the description so Codex can select the correct one.

### Startup validation errors

If Codex reports validation errors at startup, fix the listed issues in `SKILL.md`. Most often, this is a multi-line or over-length `name` or `description`. Restart Codex to reload skills.