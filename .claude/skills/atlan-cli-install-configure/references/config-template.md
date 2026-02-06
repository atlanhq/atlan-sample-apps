# Atlan CLI Config Template

## Minimum Config File
Create `.atlan/config.yaml` with:

```yaml
atlan_base_url: https://tenant.atlan.com
log:
  enabled: false
  level: info
```

## Auth Options
Prefer environment variable:

```bash
export ATLAN_API_KEY="your-api-key"
```

Or store in config:

```yaml
atlan_api_key: your-api-key
```

Never echo or log full API keys.

## Optional Data Source Mapping
Add data source blocks only when user provides source details:

```yaml
"data_source snowflake":
  type: snowflake
  connection:
    name: snowflake-prod
    qualified_name: "default/snowflake/1234567890"
  database: db
  schema: analytics
```

## Validation Checklist
1. `atlan --version` works.
2. `atlan --help` works.
3. `.atlan/config.yaml` exists when config-file mode is used.
4. At least one auth path is set (`ATLAN_API_KEY` or `atlan_api_key`).
