# Verification Checklist

1. Read at least one SDK code file relevant to the task.
2. Read at least one SDK doc page relevant to the task.
3. For command-driven tasks, verify CLI behavior from at least one CLI code/doc source.
4. For new app tasks, verify CLI availability strategy (`atlan` present, install path, or shim path).
5. For run/e2e tasks, verify dependency startup prerequisites (`uv`, `temporal`, `dapr`, Dapr runtime init).
6. Record at least three resolved facts in the manifest.
7. Resolve contradictions before code generation.
8. Mark manifest `blocked` if unresolved questions remain.
