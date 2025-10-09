# References

This section provides technical reference materials and specifications for the [EXTRACTOR_APP_NAME] connector. Use these documents to understand the technical details, capabilities, and requirements.

> **Note**: All configuration examples in this document are for illustration purposes only. Adapt them to your specific environment and requirements.

## Reference Guides

### 1. [What does Atlan crawl from Extractor App?](./what-does-atlan-crawl.md)

Comprehensive reference of all metadata types, assets, and properties that Atlan extracts from your [EXTRACTOR_APP_NAME] instance.

**What you'll find:**

- Complete list of supported asset types
- Metadata properties extracted for each asset
- Relationship mappings and lineage information
- Data types and format specifications

### 2. [Preflight checks for Extractor App](./preflight-checks.md)

Essential validation checks and requirements that must be met before running the connector.

**What you'll find:**

- System requirements and prerequisites
- Permission and access validation
- Network connectivity checks
- Configuration validation steps

## Technical Specifications

### Supported Versions

| Component            | Minimum Version | Recommended Version | Maximum Version |
| -------------------- | --------------- | ------------------- | --------------- |
| [EXTRACTOR_APP_NAME] | 1.0.0           | 2.1.0               | 3.0.x           |
| Atlan Platform       | 2.0.0           | 2.5.0               | Latest          |
| Python Runtime       | 3.8             | 3.11                | 3.12            |

### System Requirements

#### Minimum Requirements

- **CPU**: 2 cores
- **Memory**: 4 GB RAM
- **Storage**: 10 GB available space
- **Network**: 100 Mbps bandwidth

#### Recommended Requirements

- **CPU**: 4 cores
- **Memory**: 8 GB RAM
- **Storage**: 50 GB available space
- **Network**: 1 Gbps bandwidth

### API Compatibility

The connector supports the following API versions:

- **REST API**: v2.0, v2.1, v2.2
- **GraphQL API**: v1.0 (if applicable)
- **Streaming API**: v1.5 (if applicable)

## Data Types and Mappings

### Supported Data Types

| [EXTRACTOR_APP_NAME] Type | Atlan Type | Notes                  |
| ------------------------- | ---------- | ---------------------- |
| VARCHAR                   | String     | Variable length text   |
| INTEGER                   | Number     | 32-bit integer         |
| BIGINT                    | Number     | 64-bit integer         |
| DECIMAL                   | Number     | Decimal with precision |
| BOOLEAN                   | Boolean    | True/false values      |
| DATE                      | Date       | Date only              |
| TIMESTAMP                 | DateTime   | Date and time          |
| JSON                      | Object     | JSON objects           |
| ARRAY                     | Array      | Array of values        |

### Custom Type Mappings

```yaml
# Custom type mapping configuration
type_mappings:
  custom_types:
    - source_type: "CUSTOM_STRING"
      target_type: "String"
      transformation: "uppercase"

    - source_type: "ENUM_TYPE"
      target_type: "String"
      allowed_values: ["VALUE1", "VALUE2", "VALUE3"]
```

## Metadata Schema

### Asset Hierarchy

```
Database
├── Schema
│   ├── Table
│   │   ├── Column
│   │   ├── Index
│   │   └── Constraint
│   ├── View
│   │   └── Column
│   └── Procedure
│       └── Parameter
└── User
    └── Permission
```

### Relationship Types

- **Contains**: Database contains Schemas, Schema contains Tables
- **References**: Foreign key relationships between tables
- **Derives**: Views derive from base tables
- **Uses**: Procedures use tables and views
- **Grants**: Users have permissions on objects

## Configuration Reference

### Connection Parameters

```yaml
# Complete connection configuration reference
connection:
  # Required parameters
  host: "string" # Server hostname or IP
  port: "integer" # Connection port (default: 5432)
  database: "string" # Database name
  username: "string" # Authentication username
  password: "string" # Authentication password

  # Optional parameters
  ssl_mode: "string" # SSL connection mode
  connect_timeout: "integer" # Connection timeout in seconds
  query_timeout: "integer" # Query timeout in seconds
  schema: "string" # Default schema
  application_name: "string" # Application identifier

  # Advanced parameters
  pool_size: "integer" # Connection pool size
  max_overflow: "integer" # Maximum pool overflow
  pool_timeout: "integer" # Pool connection timeout
  pool_recycle: "integer" # Connection recycle time
```

### Extraction Parameters

```yaml
# Complete extraction configuration reference
extraction:
  # Asset filtering
  include_schemas: ["string"] # Schemas to include
  exclude_schemas: ["string"] # Schemas to exclude
  include_tables: ["string"] # Tables to include
  exclude_tables: ["string"] # Tables to exclude

  # Metadata options
  extract_comments: "boolean" # Extract comments
  extract_indexes: "boolean" # Extract index information
  extract_constraints: "boolean" # Extract constraints
  extract_triggers: "boolean" # Extract triggers
  extract_procedures: "boolean" # Extract stored procedures

  # Performance options
  batch_size: "integer" # Batch size for extraction
  parallel_workers: "integer" # Number of parallel workers
  max_connections: "integer" # Maximum connections

  # Data sampling
  enable_sampling: "boolean" # Enable data sampling
  sample_size: "integer" # Sample size for profiling
  sampling_method: "string" # Sampling method (random/systematic)
```

## Error Codes and Messages

### Connection Errors

| Error Code | Message               | Solution                   |
| ---------- | --------------------- | -------------------------- |
| CONN_001   | Connection timeout    | Check network connectivity |
| CONN_002   | Authentication failed | Verify credentials         |
| CONN_003   | Database not found    | Check database name        |
| CONN_004   | Permission denied     | Grant required permissions |

### Extraction Errors

| Error Code | Message                     | Solution                       |
| ---------- | --------------------------- | ------------------------------ |
| EXTR_001   | Schema not accessible       | Check schema permissions       |
| EXTR_002   | Table extraction failed     | Review table-specific settings |
| EXTR_003   | Column metadata incomplete  | Verify column access rights    |
| EXTR_004   | Relationship mapping failed | Check foreign key constraints  |

## Performance Benchmarks

### Typical Performance Metrics

| Metric          | Small Instance | Medium Instance | Large Instance   |
| --------------- | -------------- | --------------- | ---------------- |
| Tables          | < 100          | 100 - 1,000     | > 1,000          |
| Extraction Time | < 5 min        | 5 - 30 min      | 30 min - 2 hours |
| Memory Usage    | < 1 GB         | 1 - 4 GB        | 4 - 8 GB         |
| Network I/O     | < 100 MB       | 100 MB - 1 GB   | > 1 GB           |

### Optimization Guidelines

- **Small Instances**: Use default settings
- **Medium Instances**: Increase batch size and parallel workers
- **Large Instances**: Enable incremental crawling and optimize filtering

## Security Considerations

### Authentication Methods

- **Basic Authentication**: Username and password
- **Token-based Authentication**: API tokens or JWT
- **Certificate Authentication**: Client certificates
- **Integrated Authentication**: SSO integration

### Network Security

- **Encryption**: TLS/SSL for data in transit
- **Firewall Rules**: Restrict access to required ports
- **VPN/Private Links**: Use private network connections
- **IP Whitelisting**: Restrict access by IP address

### Data Privacy

- **PII Detection**: Automatic detection of sensitive data
- **Data Masking**: Mask sensitive values during extraction
- **Access Logging**: Log all data access activities
- **Retention Policies**: Configure data retention settings

## Compliance and Governance

### Regulatory Compliance

- **GDPR**: Data protection and privacy compliance
- **HIPAA**: Healthcare data protection
- **SOX**: Financial data governance
- **PCI DSS**: Payment card data security

### Audit and Monitoring

- **Audit Logs**: Comprehensive activity logging
- **Change Tracking**: Track metadata changes
- **Access Monitoring**: Monitor data access patterns
- **Compliance Reporting**: Generate compliance reports

## API Reference

### REST API Endpoints

```
GET    /api/v2/connectors/extractor-app/status
POST   /api/v2/connectors/extractor-app/crawl
GET    /api/v2/connectors/extractor-app/assets
PUT    /api/v2/connectors/extractor-app/config
DELETE /api/v2/connectors/extractor-app/cache
```

### SDK Reference

```python
# Python SDK example
from atlan_connector import ExtractorAppConnector

# Initialize connector
connector = ExtractorAppConnector(
    host="extractor-app.example.com",
    username="user",
    password="pass"
)

# Test connection
connector.test_connection()

# Start crawling
result = connector.crawl(mode="incremental")
```

## Changelog

### Version History

- **v2.1.0**: Added support for custom data types
- **v2.0.0**: Major release with performance improvements
- **v1.5.0**: Added lineage extraction capabilities
- **v1.0.0**: Initial release

## Support and Resources

### Documentation Links

- [Official Documentation](https://docs.atlan.com/connectors/extractor-app)
- [API Reference](https://api-docs.atlan.com/connectors/extractor-app)
- [SDK Documentation](https://sdk-docs.atlan.com/python/extractor-app)

### Community Resources

- [Community Forum](https://community.atlan.com/extractor-app)
- [GitHub Repository](https://github.com/atlanhq/extractor-app-connector)
- [Sample Configurations](https://github.com/atlanhq/extractor-app-samples)
