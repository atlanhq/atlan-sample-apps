/*
 * File: filter_metadata.sql
 * Purpose: Filters metadata to exclude system schemas
 *
 * Description:
 *   - Retrieves basic schema information
 *   - Excludes system schemas (information_schema, performance_schema, mysql, sys)
 *
 */
SELECT schema_name schema_name, catalog_name catalog_name
FROM INFORMATION_SCHEMA.SCHEMATA
WHERE schema_name NOT IN ('information_schema', 'performance_schema','mysql','sys');