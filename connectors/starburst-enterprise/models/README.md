# Models Directory

This directory contains the Atlan type definitions (typedefs) for Starburst Enterprise entities.

## Starburst Enterprise Object Types

### REST API Objects
- **Domain** - Organizational grouping for Data Products
- **Data Product** - Curated data offering (maps to schema + views)
- **Dataset** - View or Materialized View within a Data Product
- **Dataset Column** - Column within a Dataset

### SQL Objects (INFORMATION_SCHEMA)
- **Catalog** - Top-level container (connector to external data source)
- **Schema** - Namespace within a catalog
- **Table** - Physical data table
- **View** - SQL view definition
- **Column** - Column within a Table or View

## Key Relationships
- Domain contains Data Products
- Data Product maps 1:1 to a Schema
- Dataset maps 1:1 to a View/Materialized View
- Catalog contains Schemas
- Schema contains Tables and Views
- Tables/Views contain Columns
