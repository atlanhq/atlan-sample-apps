/*
 * File: extract_table.sql
 * Purpose: Extract table and view metadata from a Starburst Enterprise catalog
 *
 * Description:
 *   - Queries INFORMATION_SCHEMA.TABLES for the given catalog
 *   - Returns tables (BASE TABLE) and views (VIEW)
 *   - Excludes the internal 'information_schema' schema
 *   - Applies include/exclude regex filtering on schema names
 *
 * Parameters:
 *   {catalog_name} - The catalog to query
 *   {normalized_exclude_regex} - Regex pattern for schemas to exclude
 *   {normalized_include_regex} - Regex pattern for schemas to include
 */
SELECT
    table_catalog,
    table_schema,
    table_name,
    CASE
        WHEN table_type = 'BASE TABLE' THEN 'TABLE'
        ELSE table_type
    END AS table_type
FROM
    "{catalog_name}".information_schema.tables
WHERE
    table_schema != 'information_schema'
    AND table_schema NOT REGEXP '{normalized_exclude_regex}'
    AND table_schema REGEXP '{normalized_include_regex}'
ORDER BY
    table_schema,
    table_name
