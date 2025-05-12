/*
 * File: extract_schema.sql
 * Purpose: Extracts detailed schema information from MySQL server
 *
 * Description:
 *   - Retrieves schema metadata including character set, collation, and encryption settings
 *   - Counts tables and views in each schema
 *   - Filters out system schemas and applies include/exclude regex patterns
 *
 * Parameters:
 *   {normalized_exclude_regex} - Regex pattern for schemas to exclude
 *   {normalized_include_regex} - Regex pattern for schemas to include
 *
 */
SELECT
    s.CATALOG_NAME catalog_name,
    s.SCHEMA_NAME schema_name,
    s.DEFAULT_CHARACTER_SET_NAME default_character_set_name,
    s.DEFAULT_COLLATION_NAME default_collation_name,
    s.SQL_PATH sql_path,
    s.DEFAULT_ENCRYPTION default_encryption,
    CAST(table_counts.table_count AS CHAR) AS table_count,
    CAST(table_counts.view_count AS CHAR) AS view_count
FROM
    information_schema.schemata s
LEFT JOIN (
    SELECT
        table_schema,
        SUM(CASE WHEN table_type = 'BASE TABLE' THEN 1 ELSE 0 END) as table_count,
        SUM(CASE WHEN table_type = 'VIEW' THEN 1 ELSE 0 END) as view_count
    FROM
        information_schema.tables
    GROUP BY
        table_schema
) as table_counts
ON s.schema_name = table_counts.table_schema
WHERE s.schema_name NOT IN ('information_schema', 'performance_schema', 'mysql','sys')
    AND CONCAT(s.CATALOG_NAME, '.', s.SCHEMA_NAME) NOT REGEXP '{normalized_exclude_regex}'
    AND CONCAT(s.CATALOG_NAME, '.', s.SCHEMA_NAME) REGEXP '{normalized_include_regex}';