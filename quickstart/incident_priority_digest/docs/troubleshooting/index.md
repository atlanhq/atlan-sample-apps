# Troubleshooting

This section provides comprehensive troubleshooting guides and solutions for common issues encountered with the [EXTRACTOR_APP_NAME] connector. Use these resources to diagnose and resolve problems quickly.

> **Note**: All configuration examples in this document are for illustration purposes only. Adapt them to your specific environment and requirements.

## Quick Diagnostic Checklist

Before diving into specific troubleshooting guides, run through this quick checklist:

### ✅ Basic Health Check

1. **Network Connectivity**

   ```bash
   # Test basic connectivity
   ping your-extractor-app.company.com
   telnet your-extractor-app.company.com 5432
   ```

2. **Authentication**

   ```bash
   # Test database connection
   psql -h your-extractor-app.company.com -U atlan_user -d production_db -c "SELECT 1;"
   ```

3. **Authorization**

   ```sql
   -- Check table access
   SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';
   ```

4. **Resource Availability**
   ```bash
   # Check system resources
   free -h
   df -h
   top
   ```

## Common Issue Categories

### 🔌 [Connectivity Issues](./connectivity-troubleshooting.md)

Problems connecting to your [EXTRACTOR_APP_NAME] instance, including network, firewall, and DNS issues.

**Common symptoms:**

- Connection timeouts
- "Host unreachable" errors
- SSL/TLS handshake failures
- DNS resolution failures

### 🔐 Authentication and Permission Issues

Problems with user credentials, database permissions, and access control.

**Common symptoms:**

- "Authentication failed" errors
- "Permission denied" messages
- Missing tables or schemas in results
- "Access denied to system catalogs"

### ⚡ Performance Issues

Slow crawling, timeouts, and resource-related problems.

**Common symptoms:**

- Crawls taking too long to complete
- Memory or CPU exhaustion
- Network bandwidth saturation
- Database connection pool exhaustion

### 📊 Data Quality Issues

Problems with extracted metadata quality, completeness, or accuracy.

**Common symptoms:**

- Missing metadata for some objects
- Incorrect data types or relationships
- Incomplete profiling results
- Inconsistent lineage information

### 🔧 Configuration Issues

Problems with connector configuration, scheduling, and deployment.

**Common symptoms:**

- Connector fails to start
- Invalid configuration errors
- Scheduling problems
- Environment-specific issues

## Troubleshooting Methodology

### Step 1: Identify the Problem

1. **Gather Information**
   - What operation was being performed?
   - When did the issue first occur?
   - Has this worked before?
   - What changed recently?

2. **Check Logs**

   ```bash
   # View recent connector logs
   atlan-connector logs --name extractor-app --tail 100

   # Check system logs
   journalctl -u atlan-connector -f

   # Review application logs
   tail -f /var/log/atlan/connector.log
   ```

3. **Reproduce the Issue**
   ```bash
   # Try to reproduce with debug mode
   atlan-connector crawl --name extractor-app --debug --dry-run
   ```

### Step 2: Isolate the Cause

1. **Test Components Individually**
   - Network connectivity
   - Authentication
   - Database access
   - Configuration validity

2. **Use Diagnostic Tools**

   ```bash
   # Run comprehensive diagnostics
   atlan-connector diagnose --name extractor-app --comprehensive

   # Generate health report
   atlan-connector health-check --name extractor-app --output report.json
   ```

### Step 3: Apply Solutions

1. **Start with Simple Fixes**
   - Restart the connector
   - Clear caches
   - Verify configuration

2. **Apply Targeted Solutions**
   - Use specific troubleshooting guides
   - Implement recommended fixes
   - Test changes incrementally

3. **Verify the Fix**
   - Run test operations
   - Monitor for recurrence
   - Document the solution

## Error Code Reference

### Connection Errors (CONN_xxx)

| Code     | Message               | Cause                             | Solution                                     |
| -------- | --------------------- | --------------------------------- | -------------------------------------------- |
| CONN_001 | Connection timeout    | Network latency or firewall       | Check network path and firewall rules        |
| CONN_002 | Connection refused    | Service not running or wrong port | Verify service status and port configuration |
| CONN_003 | Host unreachable      | Network routing issue             | Check network connectivity and routing       |
| CONN_004 | DNS resolution failed | DNS configuration issue           | Verify hostname and DNS settings             |

### Authentication Errors (AUTH_xxx)

| Code     | Message             | Cause                    | Solution                               |
| -------- | ------------------- | ------------------------ | -------------------------------------- |
| AUTH_001 | Invalid credentials | Wrong username/password  | Verify credentials and account status  |
| AUTH_002 | Account locked      | Too many failed attempts | Unlock account and reset password      |
| AUTH_003 | Permission denied   | Insufficient privileges  | Grant required database permissions    |
| AUTH_004 | SSL required        | Connection requires SSL  | Enable SSL in connection configuration |

### Extraction Errors (EXTR_xxx)

| Code     | Message                    | Cause                             | Solution                            |
| -------- | -------------------------- | --------------------------------- | ----------------------------------- |
| EXTR_001 | Schema not found           | Schema doesn't exist or no access | Verify schema name and permissions  |
| EXTR_002 | Table extraction failed    | Table-specific access issue       | Check table permissions and filters |
| EXTR_003 | Column metadata incomplete | Missing column permissions        | Grant SELECT on system catalogs     |
| EXTR_004 | Query timeout              | Long-running metadata query       | Increase timeout or optimize query  |

### Configuration Errors (CONF_xxx)

| Code     | Message                    | Cause                              | Solution                             |
| -------- | -------------------------- | ---------------------------------- | ------------------------------------ |
| CONF_001 | Invalid configuration      | Syntax or validation error         | Review configuration syntax          |
| CONF_002 | Missing required parameter | Required field not provided        | Add missing configuration parameters |
| CONF_003 | Parameter out of range     | Value outside acceptable range     | Adjust parameter to valid range      |
| CONF_004 | Conflicting settings       | Incompatible configuration options | Resolve configuration conflicts      |

## Diagnostic Commands

### Health Check Commands

```bash
# Comprehensive health check
atlan-connector health-check --name extractor-app --verbose

# Test specific components
atlan-connector test-connection --name extractor-app
atlan-connector test-permissions --name extractor-app
atlan-connector test-extraction --name extractor-app --sample 10

# Validate configuration
atlan-connector validate-config --name extractor-app --strict
```

### Debugging Commands

```bash
# Enable debug logging
atlan-connector set-log-level --name extractor-app --level DEBUG

# Run in debug mode
atlan-connector crawl --name extractor-app --debug --verbose

# Trace network calls
atlan-connector crawl --name extractor-app --trace-network

# Profile performance
atlan-connector crawl --name extractor-app --profile --output profile.json
```

### Information Gathering Commands

```bash
# Get connector information
atlan-connector info --name extractor-app

# List all connectors
atlan-connector list --status all

# Show configuration
atlan-connector show-config --name extractor-app

# Export logs
atlan-connector export-logs --name extractor-app --since "24h" --output logs.zip
```

## Log Analysis

### Understanding Log Levels

- **ERROR**: Critical issues that prevent operation
- **WARN**: Potential issues that don't stop operation
- **INFO**: General operational information
- **DEBUG**: Detailed diagnostic information

### Common Log Patterns

#### Connection Issues

```
ERROR: Connection to extractor-app.company.com:5432 failed: Connection timed out
WARN: Retrying connection attempt 2/3
INFO: Connection established successfully
```

#### Permission Issues

```
ERROR: Permission denied for schema "analytics"
WARN: Skipping inaccessible table "sensitive_data"
INFO: Successfully extracted 45 tables from schema "public"
```

#### Performance Issues

```
WARN: Query execution time exceeded 60 seconds
INFO: Extracted 1000 tables in 15 minutes
DEBUG: Memory usage: 2.1GB, CPU usage: 85%
```

### Log Analysis Tools

```bash
# Search for errors
grep -i "error" /var/log/atlan/connector.log | tail -20

# Count warning types
grep -i "warn" /var/log/atlan/connector.log | cut -d':' -f3 | sort | uniq -c

# Analyze performance metrics
grep "execution time" /var/log/atlan/connector.log | awk '{print $NF}' | sort -n

# Extract connection attempts
grep "connection" /var/log/atlan/connector.log | grep -E "(established|failed)"
```

## Performance Optimization

### Identifying Performance Bottlenecks

1. **Network Bottlenecks**

   ```bash
   # Monitor network usage
   iftop -i eth0

   # Check network latency
   ping -c 10 your-extractor-app.company.com

   # Test bandwidth
   iperf3 -c your-extractor-app.company.com
   ```

2. **Database Bottlenecks**

   ```sql
   -- Check active connections
   SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

   -- Monitor query performance
   SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

   -- Check lock contention
   SELECT * FROM pg_locks WHERE NOT granted;
   ```

3. **System Resource Bottlenecks**

   ```bash
   # Monitor CPU usage
   top -p $(pgrep -f atlan-connector)

   # Check memory usage
   ps aux | grep atlan-connector

   # Monitor disk I/O
   iostat -x 1 5
   ```

### Optimization Strategies

#### Network Optimization

```yaml
# Connection optimization
connection:
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
  pool_recycle: 3600

# Compression settings
network:
  compression: true
  buffer_size: "64KB"
  keep_alive: true
```

#### Query Optimization

```yaml
# Batch processing
extraction:
  batch_size: 1000
  parallel_workers: 4
  query_timeout: 300

# Selective extraction
filtering:
  include_schemas: ["production", "analytics"]
  exclude_large_tables: true
  max_table_size: "1GB"
```

#### Resource Optimization

```yaml
# Memory management
resources:
  memory_limit: "4GB"
  gc_threshold: 1000
  streaming_mode: true

# CPU optimization
processing:
  max_workers: 4
  worker_type: "thread"
  queue_size: 100
```

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Operational Metrics**
   - Connector uptime and availability
   - Crawl success/failure rates
   - Average crawl duration
   - Error rates by type

2. **Performance Metrics**
   - Network throughput and latency
   - Database connection pool usage
   - Memory and CPU utilization
   - Query execution times

3. **Data Quality Metrics**
   - Metadata completeness
   - Extraction accuracy
   - Lineage coverage
   - Profile data freshness

### Setting Up Monitoring

```yaml
# Monitoring configuration
monitoring:
  enabled: true
  metrics_endpoint: "http://localhost:8080/metrics"
  health_endpoint: "http://localhost:8080/health"

  # Metric collection
  collectors:
    - "system_metrics"
    - "connector_metrics"
    - "database_metrics"

  # Export configuration
  exporters:
    - type: "prometheus"
      endpoint: "http://prometheus:9090"
    - type: "datadog"
      api_key: "${DATADOG_API_KEY}"
```

### Alert Configuration

```yaml
# Alert rules
alerts:
  - name: "connector_down"
    condition: "up == 0"
    duration: "5m"
    severity: "critical"

  - name: "high_error_rate"
    condition: "error_rate > 0.1"
    duration: "10m"
    severity: "warning"

  - name: "slow_crawl"
    condition: "crawl_duration > 3600"
    duration: "0m"
    severity: "warning"
```

## Getting Additional Help

### Self-Service Resources

1. **Documentation**
   - [Getting Started Guide](../getting-started/)
   - [Configuration Reference](../references/)
   - [FAQ Section](../faq/)

2. **Community Resources**
   - [Community Forum](https://community.atlan.com)
   - [GitHub Issues](https://github.com/atlanhq/connectors)
   - [Knowledge Base](https://kb.atlan.com)

3. **Diagnostic Tools**

   ```bash
   # Generate support bundle
   atlan-connector support-bundle --name extractor-app --output support.zip

   # Run system diagnostics
   atlan-connector system-check --comprehensive

   # Export configuration for review
   atlan-connector export-config --name extractor-app --sanitized
   ```

### Professional Support

When contacting support, please provide:

1. **Problem Description**
   - What you were trying to do
   - What happened instead
   - Error messages received

2. **Environment Information**
   - Connector version
   - [EXTRACTOR_APP_NAME] version
   - Operating system and version
   - Network configuration

3. **Diagnostic Information**
   - Relevant log files
   - Configuration files (sanitized)
   - Support bundle (if available)

4. **Reproduction Steps**
   - Steps to reproduce the issue
   - Frequency of occurrence
   - Workarounds attempted

### Escalation Process

1. **Level 1**: Community support and documentation
2. **Level 2**: Professional support team
3. **Level 3**: Engineering team for complex technical issues
4. **Level 4**: Product team for feature requests or design issues

Contact your support team or submit a ticket through your organization's support portal to begin the escalation process.
