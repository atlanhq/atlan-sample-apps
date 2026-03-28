# Frequently Asked Questions (FAQ)

This section addresses common questions and scenarios encountered when working with the [EXTRACTOR_APP_NAME] connector. Find quick answers to setup, configuration, and troubleshooting questions.

> **Note**: All configuration examples in this document are for illustration purposes only. Adapt them to your specific environment and requirements.

## General Questions

### What is the [EXTRACTOR_APP_NAME] connector?

The [EXTRACTOR_APP_NAME] connector is a specialized integration that allows Atlan to discover, extract, and catalog metadata from your [EXTRACTOR_APP_NAME] instance. It provides comprehensive data discovery capabilities, including:

- **Metadata Extraction**: Tables, columns, schemas, and relationships
- **Data Profiling**: Quality metrics and statistical analysis
- **Lineage Discovery**: Data flow and transformation mapping
- **Usage Analytics**: Access patterns and popularity metrics

### How does the connector work?

The connector operates in two main phases:

1. **Crawling Phase**: Connects to your [EXTRACTOR_APP_NAME] instance and extracts structural metadata
2. **Mining Phase**: Analyzes the extracted data to provide insights, profiling, and lineage information

The process is automated and can be scheduled to run at regular intervals to keep your catalog up-to-date.

### What versions of [EXTRACTOR_APP_NAME] are supported?

| Version Range | Support Level    | Notes               |
| ------------- | ---------------- | ------------------- |
| 1.x           | ❌ Not Supported | End of life         |
| 2.0 - 2.5     | ⚠️ Limited       | Basic features only |
| 2.6 - 3.0     | ✅ Full Support  | Recommended         |
| 3.1+          | ✅ Full Support  | Latest features     |

For the most current compatibility information, check the [References](../references/) section.

## Setup and Configuration

### How long does the initial setup take?

Setup time varies based on your environment:

- **Small instances** (< 100 tables): 15-30 minutes
- **Medium instances** (100-1,000 tables): 30-60 minutes
- **Large instances** (> 1,000 tables): 1-3 hours

The initial crawl takes longer than subsequent incremental crawls.

### Do I need special permissions to set up the connector?

Yes, you need:

**On the [EXTRACTOR_APP_NAME] side:**

- Database connection permissions
- SELECT access on target schemas and tables
- Access to system catalogs for metadata extraction

**On the Atlan side:**

- Admin or Connector Manager role
- Permission to create and configure connectors

See the [Setup Guide](../getting-started/setup-extractor-app.md) for detailed permission requirements.

### Can I test the connection before running a full crawl?

Absolutely! The connector provides several testing options:

```bash
# Test basic connectivity
atlan-connector test-connection --config config.yaml

# Test with sample data
atlan-connector test-crawl --config config.yaml --sample 100

# Validate configuration
atlan-connector validate-config --config config.yaml
```

### How do I configure the connector for multiple environments?

You can set up separate connector instances for different environments:

```yaml
# Production environment
production:
  host: "prod-extractor-app.company.com"
  database: "production_db"
  schedule: "daily"

# Staging environment
staging:
  host: "staging-extractor-app.company.com"
  database: "staging_db"
  schedule: "weekly"

# Development environment
development:
  host: "dev-extractor-app.company.com"
  database: "dev_db"
  schedule: "manual"
```

## Crawling and Data Extraction

### How often should I run the crawler?

Recommended frequencies based on your data change patterns:

- **High-change environments**: Daily incremental crawls
- **Medium-change environments**: Weekly full crawls with daily incremental
- **Low-change environments**: Monthly full crawls with weekly incremental
- **Development environments**: Manual or weekly crawls

### What happens if the crawl fails partway through?

The connector includes robust error handling:

- **Automatic Retry**: Failed operations are retried with exponential backoff
- **Partial Success**: Successfully extracted metadata is preserved
- **Resume Capability**: Subsequent crawls can resume from the last successful point
- **Error Reporting**: Detailed logs help identify and resolve issues

### Can I exclude certain schemas or tables from crawling?

Yes, you can use inclusion and exclusion patterns:

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

# Exclude specific tables
exclude_tables:
  - "audit_log"
  - "session_data"
  - "cache_*"
```

### How much data does the connector extract?

The connector extracts **metadata only**, not the actual data:

- **Structural metadata**: Table and column definitions (~KB per table)
- **Statistical metadata**: Row counts, data types (~KB per table)
- **Sample data**: Small samples for profiling (configurable, typically < 1MB per table)

Total metadata size is typically:

- **Small instances**: < 10 MB
- **Medium instances**: 10-100 MB
- **Large instances**: 100 MB - 1 GB

### Can I crawl data from multiple [EXTRACTOR_APP_NAME] instances?

Yes, you can set up multiple connector instances:

1. **Separate Connectors**: Create individual connectors for each instance
2. **Unified Catalog**: All metadata appears in a single Atlan catalog
3. **Distinct Naming**: Use qualified names to distinguish between instances

```yaml
# Instance 1: Production
connector_1:
  name: "production-extractor-app"
  host: "prod-db.company.com"
  prefix: "prod"

# Instance 2: Analytics
connector_2:
  name: "analytics-extractor-app"
  host: "analytics-db.company.com"
  prefix: "analytics"
```

## Performance and Optimization

### The crawler is running slowly. How can I optimize it?

Several optimization strategies:

**1. Adjust Batch Sizes**

```yaml
performance:
  batch_size: 1000 # Increase for better throughput
  parallel_workers: 4 # Increase based on available CPU
```

**2. Use Incremental Crawling**

```yaml
crawling:
  mode: "incremental" # Only extract changes
  lookback_period: "24h"
```

**3. Optimize Filtering**

```yaml
filtering:
  exclude_large_tables: true
  max_table_size: "1GB"
  skip_empty_tables: true
```

**4. Schedule During Off-Peak Hours**

```yaml
schedule:
  time: "02:00" # Run during low-usage periods
  timezone: "UTC"
```

### How much network bandwidth does crawling use?

Network usage depends on your instance size:

- **Metadata extraction**: 1-10 Mbps sustained
- **Data profiling**: 10-100 Mbps in bursts
- **Large instances**: May require 100+ Mbps for reasonable performance

The connector automatically throttles to avoid overwhelming your network.

### Can I run multiple crawls simultaneously?

It's generally not recommended to run multiple crawls of the same instance simultaneously as this can:

- Overload your [EXTRACTOR_APP_NAME] instance
- Cause resource conflicts
- Lead to incomplete or inconsistent results

However, you can:

- Run crawls of different instances simultaneously
- Run different types of operations (crawl + mine) in parallel
- Use the queue system to schedule multiple operations

## Data Quality and Profiling

### What data quality checks does the connector perform?

The connector includes comprehensive data quality assessment:

**Completeness Checks:**

- Null value analysis
- Empty string detection
- Missing value patterns

**Validity Checks:**

- Data type validation
- Format pattern matching
- Range and constraint validation

**Consistency Checks:**

- Cross-column validation
- Referential integrity
- Duplicate detection

**Uniqueness Analysis:**

- Primary key validation
- Unique constraint verification
- Cardinality analysis

### How accurate is the data profiling?

Profiling accuracy depends on sample size:

| Sample Size  | Accuracy | Performance |
| ------------ | -------- | ----------- |
| 1,000 rows   | ~85%     | Very Fast   |
| 10,000 rows  | ~95%     | Fast        |
| 100,000 rows | ~99%     | Moderate    |
| Full table   | 100%     | Slow        |

You can configure sample sizes based on your accuracy requirements:

```yaml
profiling:
  sample_size: 10000 # Balance accuracy and performance
  confidence_level: 0.95
  max_sample_size: 100000
```

### Can I customize the data profiling rules?

Yes, you can define custom profiling rules:

```yaml
custom_profiling:
  rules:
    - name: "email_validation"
      pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
      columns: ["*email*", "*mail*"]

    - name: "phone_validation"
      pattern: "^\\+?[1-9]\\d{1,14}$"
      columns: ["*phone*", "*mobile*"]

    - name: "ssn_detection"
      pattern: "^\\d{3}-\\d{2}-\\d{4}$"
      classification: "PII.SSN"
      sensitivity: "high"
```

## Security and Privacy

### How does the connector handle sensitive data?

The connector includes several privacy protection mechanisms:

**Data Minimization:**

- Extracts metadata only, not actual data
- Configurable sample sizes for profiling
- Option to disable data sampling entirely

**Sensitive Data Detection:**

- Automatic PII pattern recognition
- Custom classification rules
- Masking of sensitive sample data

**Access Control:**

- Uses dedicated service accounts
- Principle of least privilege
- Audit logging of all activities

### Is the connection secure?

Yes, the connector supports multiple security measures:

- **Encryption in Transit**: TLS/SSL for all connections
- **Authentication**: Multiple authentication methods
- **Network Security**: VPN and private link support
- **Credential Management**: Secure credential storage

```yaml
security:
  ssl_mode: "require"
  certificate_verification: true
  encryption_in_transit: true
  credential_encryption: true
```

### Can I audit connector activities?

Comprehensive auditing is available:

**Activity Logs:**

- Connection attempts and results
- Metadata extraction operations
- Data access patterns
- Error and warning events

**Compliance Reporting:**

- GDPR compliance reports
- Data access summaries
- Privacy impact assessments
- Retention policy compliance

```yaml
auditing:
  enabled: true
  log_level: "INFO"
  retention_days: 90
  compliance_reporting: true
```

## Troubleshooting

### The connector can't connect to my [EXTRACTOR_APP_NAME] instance. What should I check?

Follow this troubleshooting checklist:

**1. Network Connectivity**

```bash
# Test basic connectivity
ping your-extractor-app.company.com

# Test port access
telnet your-extractor-app.company.com 5432
```

**2. Credentials**

```bash
# Test manual connection
psql -h your-extractor-app.company.com -U atlan_user -d production_db
```

**3. Firewall Rules**

- Check that port 5432 (or your custom port) is open
- Verify that the Atlan IP addresses are whitelisted
- Confirm that outbound connections are allowed

**4. DNS Resolution**

```bash
# Verify hostname resolution
nslookup your-extractor-app.company.com
```

### I'm getting permission errors. How do I fix them?

Permission errors usually indicate insufficient database privileges:

**1. Check Current Permissions**

```sql
-- Check user privileges
SELECT * FROM information_schema.table_privileges
WHERE grantee = 'atlan_service_user';

-- Check role memberships
SELECT * FROM pg_roles WHERE rolname = 'atlan_service_user';
```

**2. Grant Required Permissions**

```sql
-- Basic permissions
GRANT CONNECT ON DATABASE production_db TO atlan_service_user;
GRANT USAGE ON SCHEMA public TO atlan_service_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO atlan_service_user;

-- System catalog access
GRANT SELECT ON pg_catalog.pg_class TO atlan_service_user;
GRANT SELECT ON pg_catalog.pg_attribute TO atlan_service_user;
```

**3. Verify Access**

```sql
-- Test table access
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema = 'public';
```

### The crawl completed but I'm missing some tables. Why?

Several possible causes:

**1. Permission Issues**

- Tables may exist but not be accessible to the service account
- Check schema-level permissions

**2. Filtering Configuration**

- Tables may be excluded by inclusion/exclusion patterns
- Review your filtering settings

**3. Table Types**

- Some table types (temporary, system) may be excluded by default
- Check the table type configuration

**4. Size Limits**

- Very large tables may be skipped if size limits are configured
- Review size-based filtering rules

```yaml
# Debug configuration
debug:
  log_excluded_objects: true
  show_permission_errors: true
  verbose_filtering: true
```

### How do I get help with specific issues?

Multiple support channels are available:

**1. Documentation**

- Check the [Troubleshooting Guide](../troubleshooting/)
- Review [References](../references/) for technical details

**2. Community Support**

- [Community Forum](https://community.atlan.com)
- [GitHub Issues](https://github.com/atlanhq/connectors)

**3. Professional Support**

- Contact your Atlan support team
- Submit a support ticket with logs and configuration

**4. Self-Service Debugging**

```bash
# Enable debug mode
atlan-connector crawl --debug --verbose

# Generate diagnostic report
atlan-connector diagnose --output report.json

# Validate configuration
atlan-connector validate --comprehensive
```

## Advanced Topics

### Can I customize the metadata extraction process?

Yes, several customization options are available:

**Custom Extractors:**

```python
# Example custom extractor
class CustomTableExtractor(BaseExtractor):
    def extract_custom_metadata(self, table):
        # Your custom logic here
        return custom_metadata
```

**Custom Transformations:**

```yaml
transformations:
  - name: "normalize_names"
    type: "regex"
    pattern: "([A-Z])"
    replacement: "_\\1"

  - name: "add_prefix"
    type: "prefix"
    value: "prod_"
```

### How do I integrate with CI/CD pipelines?

The connector can be integrated into automated workflows:

```yaml
# GitHub Actions example
name: Metadata Sync
on:
  schedule:
    - cron: "0 2 * * *" # Daily at 2 AM

jobs:
  sync-metadata:
    runs-on: ubuntu-latest
    steps:
      - name: Run Atlan Connector
        run: |
          atlan-connector crawl \
            --config production.yaml \
            --mode incremental \
            --notify-on-failure
```

### Can I use the connector with infrastructure as code?

Yes, the connector supports IaC approaches:

**Terraform Example:**

```hcl
resource "atlan_connector" "extractor_app" {
  name = "production-extractor-app"
  type = "extractor-app"

  connection {
    host     = var.extractor_app_host
    database = var.extractor_app_database
    username = var.extractor_app_username
    password = var.extractor_app_password
  }

  schedule {
    frequency = "daily"
    time      = "02:00"
  }
}
```

**Ansible Example:**

```yaml
- name: Configure Extractor App Connector
  atlan_connector:
    name: "{{ connector_name }}"
    type: "extractor-app"
    config: "{{ connector_config }}"
    state: present
```

## Getting More Help

### Where can I find more detailed documentation?

- **Getting Started**: [Setup guides](../getting-started/) for initial configuration
- **Crawling**: [Detailed crawling documentation](../crawling/) for advanced configuration
- **References**: [Technical specifications](../references/) and API documentation
- **Troubleshooting**: [Comprehensive troubleshooting guide](../troubleshooting/)

### How do I stay updated on new features?

- **Release Notes**: Check the connector release notes for updates
- **Community**: Join the Atlan community for announcements
- **Documentation**: This documentation is updated with each release
- **Support**: Your support team will notify you of important updates

### Can I contribute to the connector development?

Yes! The connector is open source and welcomes contributions:

- **Bug Reports**: Submit issues on GitHub
- **Feature Requests**: Propose new features through the community
- **Code Contributions**: Submit pull requests with improvements
- **Documentation**: Help improve this documentation

For more information on contributing, see the project's contribution guidelines.
