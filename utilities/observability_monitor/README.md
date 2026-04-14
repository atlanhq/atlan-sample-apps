# Observability Monitor

Read-only Atlan embedded app that shows observability execution history for assets.

Executions are modeled as `CustomEntity` assets under the `Observability` connection, linked to their target asset via `applicationQualifiedName`. Execution entries are stored in the `Observability.Executions` custom metadata (multi-value array, pipe-separated: `execution_id|cut_off_date|execution_date`).
