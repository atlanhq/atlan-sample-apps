/*
 * File: extract_temp_table_regex_column.sql
 * Purpose: SQL fragment for filtering columns by table name pattern
 *
 * Parameters:
 *   {exclude_table_regex} - Regex pattern for table names to exclude
 *
 * Notes:
 *   - This is a SQL fragment meant to be included in other queries
 *   - Used to exclude columns from tables matching a specific pattern
 *   - Designed to be inserted after a WHERE clause with AND operator
 */
AND t.TABLE_NAME NOT REGEXP '{exclude_table_regex}'