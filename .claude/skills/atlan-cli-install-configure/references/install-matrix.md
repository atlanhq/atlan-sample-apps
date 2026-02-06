# Atlan CLI Install Matrix

## Closed Preview Notice
Atlan CLI app lifecycle flows are in closed preview. Before installing, confirm the user or org is authorized for preview usage.

## Install Decision Rules
1. If `command -v atlan` succeeds and reinstall is not requested, skip install.
2. macOS: prefer Homebrew.
3. If Homebrew is unavailable or user prefers direct binary, use OS/arch pre-built binary.
4. Do not use `go get` or source-build by default.

## Recommended (macOS with Homebrew)
```bash
brew tap atlanhq/atlan
brew install atlan
```

## Pre-built Binary Commands

### macOS (Apple Silicon / arm64)
```bash
curl -o atlan.tgz -L https://github.com/atlanhq/atlan-cli-releases/releases/latest/download/atlan_Darwin_arm64.tar.gz
tar xf atlan.tgz
```

### macOS (Intel / amd64)
```bash
curl -o atlan.tgz -L https://github.com/atlanhq/atlan-cli-releases/releases/latest/download/atlan_Darwin_amd64.tar.gz
tar xf atlan.tgz
```

### Linux (amd64)
```bash
curl -o atlan.tgz -L https://github.com/atlanhq/atlan-cli-releases/releases/latest/download/atlan_Linux_amd64.tar.gz
tar -zxf atlan.tgz
```

### Windows (amd64)
```powershell
curl -o atlan.zip -L https://github.com/atlanhq/atlan-cli-releases/releases/latest/download/atlan_Windows_amd64.zip
unzip atlan.zip
```

## Post-Install Verification
```bash
atlan --version
atlan --help
```

## PATH Notes
If `atlan` is installed but not discoverable:
1. Move binary to a PATH directory (for example `~/.local/bin` or `/usr/local/bin` on macOS/Linux).
2. Update shell profile and reload shell.
3. Re-run `command -v atlan` and `atlan --version`.
