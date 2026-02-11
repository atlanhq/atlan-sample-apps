/*
 * File: extract_view.sql
 * Purpose: Extract view definitions from a Starburst Enterprise catalog
 *
 * Description:
 *   - Queries INFORMATION_SCHEMA.VIEWS for the given catalog
 *   - Returns view name, schema, and the SQL definition
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
    view_definition
FROM
    "{catalog_name}".information_schema.views
WHERE
    table_schema != 'information_schema'
    AND table_schema NOT REGEXP '{normalized_exclude_regex}'
    AND table_schema REGEXP '{normalized_include_regex}'
ORDER BY
    table_schema,
    table_name
