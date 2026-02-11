/*
 * File: extract_schema.sql
 * Purpose: Extract schema metadata from a specific Starburst Enterprise catalog
 *
 * Description:
 *   - Queries INFORMATION_SCHEMA.SCHEMATA for the given catalog
 *   - Excludes the internal 'information_schema' schema
 *   - Applies include/exclude regex filtering
 *
 * Parameters:
 *   {catalog_name} - The catalog to query
 *   {normalized_exclude_regex} - Regex pattern for schemas to exclude
 *   {normalized_include_regex} - Regex pattern for schemas to include
 */
SELECT
    catalog_name,
    schema_name
FROM
    "{catalog_name}".information_schema.schemata
WHERE
    schema_name != 'information_schema'
    AND schema_name NOT REGEXP '{normalized_exclude_regex}'
    AND schema_name REGEXP '{normalized_include_regex}'
ORDER BY
    schema_name
