# Run Matrix

## Default Execution Contract
For run/test loops, use CLI first and fallback only when necessary.

## Preflight
1. Check CLI availability: `command -v atlan`
2. If missing, install CLI before run/test:
   - invoke `../atlan-cli-install-configure/SKILL.md`
   - use Homebrew or pre-built binaries based on OS/arch
   - never use `go get` for CLI installation
   - do not begin by searching for local `atlan-cli` clones
   - verify: `command -v atlan && atlan --help`
3. If installation is blocked (network/policy), stop and ask the user to enable installation or provide an existing CLI binary path.
4. Verify runtime prerequisites:
   - `command -v uv`
   - `command -v temporal`
   - `command -v dapr`
5. Verify Dapr runtime initialization:
   - check `~/.dapr/config.yaml`
   - if missing or deps fail to start, run `atlan app init tools`
   - if still broken, run manual recovery:
     - `dapr uninstall`
     - `dapr init --slim`
   - retry run/test loop.

## Preferred Commands
- `atlan app run -p <app_path>`
- `atlan app test -p <app_path> -t unit`
- `atlan app test -p <app_path> -t e2e`
- `atlan app test -p <app_path> -t all`

## Fallback Commands
Use only when CLI path is unavailable or mismatched.
- `uv run poe start-deps`
- `uv run main.py`
- `uv run pytest`

## Reporting
- Write `loop_report.md` for each loop.
- Log CLI mismatches in `cli-change-proposals.md` with source evidence.
- Include dependency logs when startup fails (`/tmp/atlan/<app>/deps.log` or CLI-reported log path).
