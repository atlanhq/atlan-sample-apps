/*
 * File: extract_database.sql
 * Purpose: Extracts list of databases from MySQL server
 *
 * Description:
 *   - Retrieves all non-system databases from INFORMATION_SCHEMA.SCHEMATA
 *   - Excludes system databases (information_schema, performance_schema, mysql, sys)
 *
 */
SELECT SCHEMA_NAME AS database_name
FROM INFORMATION_SCHEMA.SCHEMATA
WHERE schema_name NOT IN ('information_schema', 'performance_schema','mysql','sys');