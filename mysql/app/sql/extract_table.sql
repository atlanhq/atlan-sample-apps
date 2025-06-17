/*
 * File: extract_table.sql
 * Purpose: Extracts table metadata from MySQL server
 *
 * Description:
 *   - Retrieves table information including catalog, schema, name, and type
 *   - Determines if a table is partitioned
 *   - Filters out system schemas and applies include/exclude regex patterns
 *
 * Parameters:
 *   {normalized_exclude_regex} - Regex pattern for schemas to exclude
 *   {normalized_include_regex} - Regex pattern for schemas to include
 *   {temp_table_regex_sql} - SQL fragment for additional table filtering
 *
 */
SELECT
    t.TABLE_CATALOG table_catalog,
    t.TABLE_SCHEMA table_schema,
    t.TABLE_NAME table_name,
    CASE
            WHEN t.table_type = 'BASE TABLE' THEN 'TABLE'
            ELSE t.table_type
    END AS table_type,
    CASE
        WHEN MAX(p.PARTITION_NAME) IS NOT NULL THEN true
        ELSE false
    END AS is_partition
    FROM
        INFORMATION_SCHEMA.TABLES t
    LEFT JOIN
        INFORMATION_SCHEMA.PARTITIONS p
    ON
        t.TABLE_SCHEMA = p.TABLE_SCHEMA
        AND t.TABLE_NAME = p.TABLE_NAME
    WHERE
        t.TABLE_SCHEMA NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
        AND CONCAT(t.TABLE_CATALOG, '.', t.TABLE_SCHEMA) NOT REGEXP '{normalized_exclude_regex}'
        AND CONCAT(t.TABLE_CATALOG, '.', t.TABLE_SCHEMA) REGEXP '{normalized_include_regex}'
        {temp_table_regex_sql}
    GROUP BY
        t.TABLE_CATALOG,
        t.TABLE_SCHEMA,
        t.TABLE_NAME,
        t.TABLE_TYPE;