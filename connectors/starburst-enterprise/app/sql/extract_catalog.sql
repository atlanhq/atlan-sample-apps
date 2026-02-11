/*
 * File: extract_catalog.sql
 * Purpose: Extract catalog metadata from Starburst Enterprise
 *
 * Description:
 *   - Retrieves all available catalogs from the system metadata
 *   - Excludes the internal 'system' catalog
 *
 * Note: Trino does not have a single INFORMATION_SCHEMA across catalogs.
 *       We use the system.metadata.catalogs table instead.
 */
SELECT
    catalog_name,
    connector_name AS catalog_kind
FROM
    system.metadata.catalogs
WHERE
    catalog_name != 'system'
ORDER BY
    catalog_name
