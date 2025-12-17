# What does Atlan crawl from Extractor App?

This document provides a comprehensive reference of all metadata types, assets, and properties that Atlan extracts from your [EXTRACTOR_APP_NAME] instance.

> **Note**: All configuration examples in this document are for illustration purposes only. Adapt them to your specific environment and requirements.

## Overview

The [EXTRACTOR_APP_NAME] connector extracts metadata across multiple levels of your data infrastructure, from high-level organizational structures down to individual column properties and relationships.

## Asset Types

### Database Level Assets

#### Databases

Atlan crawls database-level metadata including:

**Properties Extracted:**

- Database name and identifier
- Database description/comments
- Creation and modification timestamps
- Database owner and permissions
- Character set and collation settings
- Database size and storage information
- Connection parameters and configuration

**Example:**

```json
{
  "typeName": "Database",
  "attributes": {
    "name": "production_db",
    "description": "Main production database",
    "owner": "db_admin",
    "createdDate": "2023-01-15T10:30:00Z",
    "modifiedDate": "2024-01-15T14:22:00Z",
    "characterSet": "UTF8",
    "collation": "en_US.UTF-8",
    "sizeBytes": 1073741824
  }
}
```

### Schema Level Assets

#### Schemas/Namespaces

Atlan extracts schema-level organization and metadata:

**Properties Extracted:**

- Schema name and fully qualified name
- Schema description and documentation
- Schema owner and access permissions
- Creation and modification timestamps
- Schema-level configuration settings
- Usage statistics and access patterns

**Example:**

```json
{
  "typeName": "Schema",
  "attributes": {
    "name": "analytics",
    "qualifiedName": "production_db.analytics",
    "description": "Analytics and reporting schema",
    "owner": "analytics_team",
    "createdDate": "2023-02-01T09:15:00Z",
    "tableCount": 45,
    "viewCount": 12
  }
}
```

### Table Level Assets

#### Tables

Comprehensive table metadata extraction:

**Properties Extracted:**

- Table name and fully qualified name
- Table type (base table, temporary, external)
- Table description and comments
- Row count and size estimates
- Creation and modification timestamps
- Table owner and permissions
- Storage format and compression
- Partitioning information
- Table constraints and indexes

**Example:**

```json
{
  "typeName": "Table",
  "attributes": {
    "name": "customer_orders",
    "qualifiedName": "production_db.analytics.customer_orders",
    "description": "Customer order transactions",
    "tableType": "BASE_TABLE",
    "rowCount": 1250000,
    "sizeBytes": 524288000,
    "owner": "data_team",
    "createdDate": "2023-03-15T11:45:00Z",
    "modifiedDate": "2024-01-20T16:30:00Z",
    "isPartitioned": true,
    "partitionKeys": ["order_date"]
  }
}
```

#### Views

View definitions and metadata:

**Properties Extracted:**

- View name and fully qualified name
- View definition (SQL query)
- View type (materialized, standard)
- Dependencies on base tables
- View description and comments
- Creation and modification timestamps
- View owner and permissions
- Refresh schedule (for materialized views)

**Example:**

```json
{
  "typeName": "View",
  "attributes": {
    "name": "monthly_sales_summary",
    "qualifiedName": "production_db.analytics.monthly_sales_summary",
    "viewType": "MATERIALIZED",
    "definition": "SELECT DATE_TRUNC('month', order_date) as month, SUM(total_amount) as total_sales FROM customer_orders GROUP BY 1",
    "description": "Monthly aggregated sales data",
    "dependsOn": ["production_db.analytics.customer_orders"],
    "refreshSchedule": "0 2 1 * *"
  }
}
```

### Column Level Assets

#### Columns

Detailed column metadata for all tables and views:

**Properties Extracted:**

- Column name and position
- Data type and precision/scale
- Nullable constraints
- Default values
- Column description and comments
- Primary key and foreign key relationships
- Index participation
- Data classification and sensitivity
- Statistical information (if profiling enabled)

**Example:**

```json
{
  "typeName": "Column",
  "attributes": {
    "name": "customer_email",
    "qualifiedName": "production_db.analytics.customers.customer_email",
    "dataType": "VARCHAR(255)",
    "isNullable": false,
    "position": 3,
    "description": "Customer email address",
    "isPrimaryKey": false,
    "isForeignKey": false,
    "hasIndex": true,
    "classification": "PII.Email",
    "defaultValue": null
  }
}
```

### Constraint Assets

#### Primary Keys

Primary key constraint information:

**Properties Extracted:**

- Constraint name
- Columns involved in the primary key
- Constraint definition
- Creation timestamp

#### Foreign Keys

Foreign key relationships and referential integrity:

**Properties Extracted:**

- Constraint name
- Source columns (foreign key)
- Referenced table and columns
- Referential actions (CASCADE, RESTRICT, etc.)
- Constraint definition

#### Check Constraints

Data validation constraints:

**Properties Extracted:**

- Constraint name
- Constraint expression
- Columns involved
- Constraint description

**Example:**

```json
{
  "typeName": "ForeignKey",
  "attributes": {
    "name": "fk_order_customer",
    "qualifiedName": "production_db.analytics.customer_orders.fk_order_customer",
    "sourceColumns": ["customer_id"],
    "referencedTable": "production_db.analytics.customers",
    "referencedColumns": ["id"],
    "onDelete": "CASCADE",
    "onUpdate": "RESTRICT"
  }
}
```

### Index Assets

#### Indexes

Database index metadata:

**Properties Extracted:**

- Index name and type (B-tree, Hash, etc.)
- Columns included in the index
- Index uniqueness constraints
- Index size and statistics
- Creation timestamp
- Index usage statistics

**Example:**

```json
{
  "typeName": "Index",
  "attributes": {
    "name": "idx_customer_email",
    "qualifiedName": "production_db.analytics.customers.idx_customer_email",
    "indexType": "BTREE",
    "columns": ["customer_email"],
    "isUnique": true,
    "sizeBytes": 10485760,
    "createdDate": "2023-03-20T14:15:00Z"
  }
}
```

### Procedure Assets

#### Stored Procedures

Stored procedure metadata and definitions:

**Properties Extracted:**

- Procedure name and signature
- Procedure definition (SQL code)
- Input and output parameters
- Return type
- Procedure description
- Creation and modification timestamps
- Procedure owner and permissions
- Dependencies on tables and other objects

#### Functions

User-defined function metadata:

**Properties Extracted:**

- Function name and signature
- Function definition
- Parameters and return type
- Function type (scalar, table-valued)
- Dependencies and usage

### User and Permission Assets

#### Users

Database user account information:

**Properties Extracted:**

- Username and user ID
- User type (regular, service account, admin)
- Account status (active, disabled)
- Creation date
- Last login timestamp
- Associated roles and groups

#### Roles and Permissions

Access control and permission metadata:

**Properties Extracted:**

- Role names and descriptions
- Permission grants on objects
- Role hierarchies and inheritance
- Permission types (SELECT, INSERT, UPDATE, DELETE, etc.)
- Grant timestamps and grantor information

## Relationship Mapping

### Hierarchical Relationships

```
Database
├── Contains → Schema
│   ├── Contains → Table
│   │   ├── Contains → Column
│   │   ├── Has → Index
│   │   └── Has → Constraint
│   ├── Contains → View
│   │   └── Contains → Column
│   └── Contains → Procedure
│       └── Has → Parameter
└── Has → User
    └── Has → Permission
```

### Reference Relationships

- **Foreign Key References**: Table A.column → Table B.column
- **View Dependencies**: View → Base Tables
- **Procedure Dependencies**: Procedure → Tables/Views
- **Index Coverage**: Index → Table Columns

### Lineage Relationships

Atlan extracts data lineage information including:

- **Table-to-Table Lineage**: ETL processes and data flows
- **Column-to-Column Lineage**: Field-level transformations
- **View Lineage**: View dependencies on source tables
- **Procedure Lineage**: Data transformations in stored procedures

## Data Profiling Information

When data profiling is enabled, Atlan also extracts:

### Column Statistics

- **Null Count**: Number of null values
- **Distinct Count**: Number of unique values
- **Min/Max Values**: Range of values
- **Average Length**: For string columns
- **Data Distribution**: Value frequency analysis

### Data Quality Metrics

- **Completeness**: Percentage of non-null values
- **Validity**: Format and constraint compliance
- **Consistency**: Cross-column validation
- **Uniqueness**: Duplicate detection

### Pattern Recognition

- **Data Formats**: Email, phone, SSN patterns
- **Business Keys**: Potential identifier columns
- **Sensitive Data**: PII and confidential information

## Metadata Refresh Frequency

Different metadata types are refreshed at different intervals:

| Metadata Type    | Refresh Frequency | Notes                            |
| ---------------- | ----------------- | -------------------------------- |
| Schema Structure | Daily             | Tables, columns, constraints     |
| Statistics       | Weekly            | Row counts, size estimates       |
| Lineage          | Daily             | Data flow relationships          |
| Profiling        | Weekly            | Data quality metrics             |
| Usage Analytics  | Hourly            | Access patterns, query frequency |
| Permissions      | Daily             | User access and roles            |

## Filtering and Customization

### Inclusion/Exclusion Patterns

You can customize what gets crawled using patterns:

```yaml
# Include specific schemas
include_schemas:
  - "production"
  - "analytics"
  - "reporting"

# Exclude temporary and test objects
exclude_patterns:
  - "temp_*"
  - "test_*"
  - "*_backup"
  - "staging_*"

# Include specific object types
include_asset_types:
  - "Table"
  - "View"
  - "Column"
  - "Index"

# Exclude sensitive or large objects
exclude_asset_types:
  - "Trigger" # Skip triggers
  - "Sequence" # Skip sequences
```

### Custom Metadata

You can also extract custom metadata properties:

```yaml
# Custom property extraction
custom_properties:
  - name: "business_owner"
    source: "table_comment"
    pattern: "OWNER:(.*)"

  - name: "data_classification"
    source: "column_comment"
    pattern: "CLASS:(.*)"

  - name: "retention_period"
    source: "table_properties"
    key: "retention_days"
```

## Limitations and Considerations

### Size Limitations

- **Maximum Tables per Schema**: 10,000
- **Maximum Columns per Table**: 1,000
- **Maximum Index Size**: 1 GB
- **Query Timeout**: 5 minutes

### Performance Considerations

- Large tables (>1M rows) may require longer extraction times
- Complex views with multiple joins may impact performance
- Extensive foreign key relationships increase processing time
- Data profiling significantly increases extraction duration

### Security Restrictions

- System tables and internal schemas are excluded by default
- Encrypted columns may not be fully profiled
- Some administrative metadata requires elevated permissions
- Sensitive data is masked during profiling (configurable)

## Troubleshooting Extraction Issues

### Common Issues

1. **Missing Tables**: Check schema permissions and inclusion patterns
2. **Incomplete Columns**: Verify column-level access rights
3. **Missing Relationships**: Ensure foreign key constraints are defined
4. **No Statistics**: Enable data profiling and verify sampling permissions

### Validation Queries

Use these queries to validate extraction completeness:

```sql
-- Check table count
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema IN ('production', 'analytics');

-- Check column count
SELECT table_name, COUNT(*) as column_count
FROM information_schema.columns
WHERE table_schema = 'production'
GROUP BY table_name;

-- Check foreign key relationships
SELECT COUNT(*) FROM information_schema.referential_constraints
WHERE constraint_schema = 'production';
```

## Next Steps

After understanding what gets crawled:

1. Review [preflight checks](./preflight-checks.md) to ensure all requirements are met
2. Configure [crawling settings](../crawling/crawl-extractor-app.md) based on your needs
3. Set up [monitoring](../troubleshooting/) to track extraction completeness
4. Explore the crawled metadata in the Atlan catalog
