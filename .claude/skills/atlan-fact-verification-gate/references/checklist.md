# Verification Checklist

1. Read at least one SDK code file relevant to the task.
2. Read at least one SDK doc page relevant to the task.
3. For command-driven tasks, verify CLI behavior from at least one CLI code/doc source (or local binary help output).
4. For new app tasks, verify CLI availability strategy (`atlan` present or web-first install path). Do not assume a local CLI shim path.
5. For run/e2e tasks, verify dependency startup prerequisites (`uv`, `temporal`, `dapr`, Dapr runtime init).
6. Record at least three resolved facts in the manifest.
7. For each resolved fact, record evidence with a provenance tag (`[local-checkout]`, `[installed-package]`, `[local-binary]`, `[remote-source]`, or `[remote-doc]`).
8. For build tasks, select a quality tier (`quickstart-utility` or `connector-standard`) from `../../_shared/references/app-quality-bar.md`.
9. Resolve contradictions before code generation.
10. Mark manifest `blocked` if unresolved questions remain.
