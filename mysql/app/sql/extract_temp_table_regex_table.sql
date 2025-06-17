/*
 * File: extract_temp_table_regex_table.sql
 * Purpose: SQL fragment for filtering tables by name pattern
 *
 * Parameters:
 *   {exclude_table_regex} - Regex pattern for table names to exclude
 *
 * Notes:
 *   - This is a SQL fragment meant to be included in other queries
 *   - Used to exclude tables matching a specific pattern
 *   - Designed to be inserted after a WHERE clause with AND operator
 */
AND TABLE_NAME NOT LIKE '{exclude_table_regex}'