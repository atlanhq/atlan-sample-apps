/*
 * File: extract_column.sql
 * Purpose: Extract column metadata from a Starburst Enterprise catalog
 *
 * Description:
 *   - Queries INFORMATION_SCHEMA.COLUMNS for the given catalog
 *   - Returns column name, type, nullability, ordinal position, and defaults
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
    column_name,
    ordinal_position,
    column_default,
    is_nullable,
    data_type
FROM
    "{catalog_name}".information_schema.columns
WHERE
    table_schema != 'information_schema'
    AND table_schema NOT REGEXP '{normalized_exclude_regex}'
    AND table_schema REGEXP '{normalized_include_regex}'
ORDER BY
    table_schema,
    table_name,
    ordinal_position
