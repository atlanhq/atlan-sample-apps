/*
 * File: extract_column.sql
 * Purpose: Extracts column metadata from MySQL server
 *
 * Description:
 *   - Retrieves column information including data type, nullability, and position
 *   - Identifies auto-increment columns
 *   - Filters out system schemas and applies include/exclude regex patterns
 *
 * Parameters:
 *   {normalized_exclude_regex} - Regex pattern for schemas to exclude
 *   {normalized_include_regex} - Regex pattern for schemas to include
 *   {temp_table_regex_sql} - SQL fragment for additional table filtering
 *
 */
SELECT
    TABLE_CATALOG table_catalog,
    TABLE_SCHEMA table_schema,
    TABLE_NAME table_name,
    COLUMN_NAME column_name,
    ORDINAL_POSITION ordinal_position,
    IS_NULLABLE is_nullable,
    DATA_TYPE data_type,
    CASE
        WHEN EXTRA LIKE '%auto_increment%' THEN 'YES'
        ELSE 'NO'
    END AS is_autoincrement
FROM
    INFORMATION_SCHEMA.COLUMNS t
WHERE
    TABLE_SCHEMA NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
    AND CONCAT(t.TABLE_CATALOG, '.', t.TABLE_SCHEMA) NOT REGEXP '{normalized_exclude_regex}'
    AND CONCAT(t.TABLE_CATALOG, '.', t.TABLE_SCHEMA) REGEXP '{normalized_include_regex}'
    {temp_table_regex_sql}
ORDER BY
    TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION;