/*
 * File: tables_check.sql
 * Purpose: Counts the number of tables matching specified criteria
 *
 * Description:
 *   - Counts tables that match the include/exclude regex patterns
 *   - Excludes system schemas (performance_schema, information_schema, mysql, sys)
 *   - Used to verify if there are any tables to process
 *
 * Parameters:
 *   {normalized_exclude_regex} - Regex pattern for schemas to exclude
 *   {normalized_include_regex} - Regex pattern for schemas to include
 *   {temp_table_regex_sql} - SQL fragment for additional table filtering
 *
 */
SELECT count(*) count
FROM INFORMATION_SCHEMA.TABLES t
WHERE t.TABLE_SCHEMA NOT IN ('performance_schema', 'information_schema', 'mysql','sys')
    AND CONCAT(t.TABLE_CATALOG, '.', t.TABLE_SCHEMA) NOT REGEXP '{normalized_exclude_regex}'
    AND CONCAT(t.TABLE_CATALOG, '.', t.TABLE_SCHEMA) REGEXP '{normalized_include_regex}'
    {temp_table_regex_sql};
