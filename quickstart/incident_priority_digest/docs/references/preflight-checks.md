# Preflight checks for Extractor App

This document outlines the essential validation checks and requirements that must be met before configuring and running the [EXTRACTOR_APP_NAME] connector with Atlan.

> **Note**: All configuration examples in this document are for illustration purposes only. Adapt them to your specific environment and requirements.

## Overview

Preflight checks ensure that your environment is properly configured and all prerequisites are met for successful metadata extraction. These checks help identify and resolve potential issues before they impact the crawling process.

## System Requirements

### Hardware Requirements

#### Minimum Requirements

- **CPU**: 2 cores (2.0 GHz or higher)
- **Memory**: 4 GB RAM
- **Storage**: 10 GB available disk space
- **Network**: 100 Mbps bandwidth

#### Recommended Requirements

- **CPU**: 4 cores (2.5 GHz or higher)
- **Memory**: 8 GB RAM
- **Storage**: 50 GB available disk space
- **Network**: 1 Gbps bandwidth

#### Large Scale Requirements (>1000 tables)

- **CPU**: 8 cores (3.0 GHz or higher)
- **Memory**: 16 GB RAM
- **Storage**: 100 GB available disk space
- **Network**: 10 Gbps bandwidth

### Software Requirements

#### [EXTRACTOR_APP_NAME] Version Compatibility

| [EXTRACTOR_APP_NAME] Version | Connector Support  | Notes               |
| ---------------------------- | ------------------ | ------------------- |
| 1.x                          | ❌ Not Supported   | End of life         |
| 2.0 - 2.5                    | ⚠️ Limited Support | Basic features only |
| 2.6 - 3.0                    | ✅ Full Support    | Recommended         |
| 3.1+                         | ✅ Full Support    | Latest features     |

#### Operating System Support

| OS             | Version | Status              |
| -------------- | ------- | ------------------- |
| Ubuntu         | 18.04+  | ✅ Supported        |
| CentOS/RHEL    | 7+      | ✅ Supported        |
| Amazon Linux   | 2       | ✅ Supported        |
| Windows Server | 2019+   | ⚠️ Limited          |
| macOS          | 10.15+  | ⚠️ Development only |

#### Runtime Dependencies

```yaml
# Required runtime components
dependencies:
  python: ">=3.8,<3.13"
  pip: ">=21.0"

  # Database drivers
  database_drivers:
    - "psycopg2>=2.8" # PostgreSQL
    - "pymysql>=1.0" # MySQL
    - "cx_Oracle>=8.0" # Oracle

  # System libraries
  system_libraries:
    - "libssl-dev"
    - "libffi-dev"
    - "build-essential"
```

## Network Connectivity

### Network Access Requirements

#### Outbound Connections

The connector requires outbound access to:

| Destination                 | Port   | Protocol | Purpose                 |
| --------------------------- | ------ | -------- | ----------------------- |
| [EXTRACTOR_APP_NAME] Server | 5432\* | TCP      | Database connection     |
| Atlan Platform              | 443    | HTTPS    | Metadata upload         |
| Package Repositories        | 443    | HTTPS    | Dependency installation |
| NTP Servers                 | 123    | UDP      | Time synchronization    |

\*Port may vary based on your [EXTRACTOR_APP_NAME] configuration

#### Inbound Connections

- **Management Interface**: Port 8080 (optional)
- **Health Check Endpoint**: Port 8081 (optional)

### Firewall Configuration

#### Required Firewall Rules

```bash
# Allow outbound to [EXTRACTOR_APP_NAME]
iptables -A OUTPUT -p tcp --dport 5432 -d [EXTRACTOR_APP_IP] -j ACCEPT

# Allow outbound HTTPS
iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT

# Allow outbound NTP
iptables -A OUTPUT -p udp --dport 123 -j ACCEPT

# Allow return traffic
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
```

### DNS Resolution

Ensure proper DNS resolution for:

- [EXTRACTOR_APP_NAME] server hostname
- Atlan platform endpoints
- Package repository domains

```bash
# Test DNS resolution
nslookup your-extractor-app.company.com
nslookup api.atlan.com
nslookup pypi.org
```

## Authentication and Permissions

### [EXTRACTOR_APP_NAME] User Account

#### Required User Permissions

The connector requires a dedicated service account with the following permissions:

```sql
-- Database-level permissions
GRANT CONNECT ON DATABASE production_db TO atlan_service_user;
GRANT USAGE ON SCHEMA information_schema TO atlan_service_user;

-- Schema-level permissions (for each target schema)
GRANT USAGE ON SCHEMA public TO atlan_service_user;
GRANT USAGE ON SCHEMA analytics TO atlan_service_user;

-- Table-level permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO atlan_service_user;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO atlan_service_user;

-- System catalog access
GRANT SELECT ON pg_catalog.pg_class TO atlan_service_user;
GRANT SELECT ON pg_catalog.pg_attribute TO atlan_service_user;
GRANT SELECT ON pg_catalog.pg_constraint TO atlan_service_user;
GRANT SELECT ON pg_catalog.pg_index TO atlan_service_user;
```

#### Service Account Best Practices

```yaml
# Service account configuration
service_account:
  username: "atlan_service_user"
  password_policy:
    min_length: 16
    complexity: "high"
    rotation_days: 90

  restrictions:
    login_hours: "00:00-23:59" # 24/7 access
    max_connections: 10
    idle_timeout: 3600 # 1 hour

  monitoring:
    log_connections: true
    log_queries: false # Avoid logging sensitive data
    alert_on_failure: true
```

### Permission Validation

#### Automated Permission Check

```sql
-- Check database connection
SELECT current_database(), current_user, version();

-- Check schema access
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name IN ('public', 'analytics', 'production');

-- Check table access
SELECT COUNT(*) as accessible_tables
FROM information_schema.tables
WHERE table_schema IN ('public', 'analytics')
AND table_type = 'BASE TABLE';

-- Check system catalog access
SELECT COUNT(*) as system_tables
FROM pg_catalog.pg_class
WHERE relkind = 'r';
```

#### Manual Permission Verification

```bash
# Test connection with service account
psql -h your-extractor-app.com -U atlan_service_user -d production_db -c "SELECT 1;"

# Test schema access
psql -h your-extractor-app.com -U atlan_service_user -d production_db -c "\\dn"

# Test table access
psql -h your-extractor-app.com -U atlan_service_user -d production_db -c "\\dt public.*"
```

## Configuration Validation

### Connection Configuration

#### Required Configuration Parameters

```yaml
# Minimum required configuration
connection:
  host: "your-extractor-app.company.com" # Required
  port: 5432 # Required
  database: "production_db" # Required
  username: "atlan_service_user" # Required
  password: "secure_password" # Required

# Optional but recommended
optional_config:
  ssl_mode: "require" # Recommended
  connect_timeout: 30 # Recommended
  application_name: "atlan-connector" # Recommended
```

#### Configuration Validation Script

```python
#!/usr/bin/env python3
"""
Configuration validation script for [EXTRACTOR_APP_NAME] connector
"""

import sys
import yaml
from typing import Dict, List

def validate_connection_config(config: Dict) -> List[str]:
    """Validate connection configuration"""
    errors = []

    # Required fields
    required_fields = ['host', 'port', 'database', 'username', 'password']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")

    # Port validation
    if 'port' in config:
        port = config['port']
        if not isinstance(port, int) or port < 1 or port > 65535:
            errors.append(f"Invalid port number: {port}")

    # SSL validation
    if 'ssl_mode' in config:
        valid_ssl_modes = ['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']
        if config['ssl_mode'] not in valid_ssl_modes:
            errors.append(f"Invalid SSL mode: {config['ssl_mode']}")

    return errors

def main():
    """Main validation function"""
    if len(sys.argv) != 2:
        print("Usage: validate_config.py <config_file>")
        sys.exit(1)

    config_file = sys.argv[1]

    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading config file: {e}")
        sys.exit(1)

    errors = validate_connection_config(config.get('connection', {}))

    if errors:
        print("Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("Configuration validation passed!")

if __name__ == "__main__":
    main()
```

### Environment Validation

#### System Resource Check

```bash
#!/bin/bash
# System resource validation script

echo "=== System Resource Check ==="

# Check CPU cores
CPU_CORES=$(nproc)
echo "CPU Cores: $CPU_CORES"
if [ $CPU_CORES -lt 2 ]; then
    echo "WARNING: Minimum 2 CPU cores recommended"
fi

# Check memory
MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
echo "Memory: ${MEMORY_GB}GB"
if [ $MEMORY_GB -lt 4 ]; then
    echo "WARNING: Minimum 4GB RAM recommended"
fi

# Check disk space
DISK_SPACE=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
echo "Available Disk Space: ${DISK_SPACE}GB"
if [ $DISK_SPACE -lt 10 ]; then
    echo "WARNING: Minimum 10GB disk space recommended"
fi

# Check network connectivity
echo "=== Network Connectivity Check ==="
if ping -c 1 google.com &> /dev/null; then
    echo "Internet connectivity: OK"
else
    echo "ERROR: No internet connectivity"
fi
```

## Data Validation

### Sample Data Access

#### Test Data Extraction

```sql
-- Test basic data access
SELECT
    schemaname,
    tablename,
    tableowner,
    hasindexes,
    hasrules,
    hastriggers
FROM pg_tables
WHERE schemaname IN ('public', 'analytics')
LIMIT 10;

-- Test column metadata access
SELECT
    table_schema,
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
LIMIT 10;

-- Test constraint information
SELECT
    constraint_name,
    table_name,
    constraint_type
FROM information_schema.table_constraints
WHERE table_schema = 'public'
LIMIT 10;
```

### Data Quality Checks

#### Metadata Completeness

```sql
-- Check for tables without descriptions
SELECT
    schemaname,
    tablename,
    obj_description(c.oid) as description
FROM pg_tables t
JOIN pg_class c ON c.relname = t.tablename
WHERE schemaname IN ('public', 'analytics')
AND obj_description(c.oid) IS NULL;

-- Check for columns without comments
SELECT
    table_schema,
    table_name,
    column_name
FROM information_schema.columns
WHERE table_schema IN ('public', 'analytics')
AND column_comment IS NULL
LIMIT 20;
```

## Security Validation

### SSL/TLS Configuration

#### SSL Connection Test

```bash
# Test SSL connection
openssl s_client -connect your-extractor-app.com:5432 -starttls postgres

# Verify SSL certificate
echo | openssl s_client -connect your-extractor-app.com:5432 -starttls postgres 2>/dev/null | openssl x509 -noout -dates
```

#### SSL Configuration Validation

```sql
-- Check SSL status
SHOW ssl;

-- Check SSL cipher
SELECT * FROM pg_stat_ssl WHERE pid = pg_backend_pid();
```

### Access Control Validation

#### User Privilege Audit

```sql
-- Check user privileges
SELECT
    grantee,
    table_schema,
    table_name,
    privilege_type
FROM information_schema.table_privileges
WHERE grantee = 'atlan_service_user'
ORDER BY table_schema, table_name;

-- Check role memberships
SELECT
    r.rolname as role_name,
    r.rolsuper as is_superuser,
    r.rolcreaterole as can_create_roles,
    r.rolcreatedb as can_create_db,
    r.rolcanlogin as can_login
FROM pg_roles r
WHERE r.rolname = 'atlan_service_user';
```

## Performance Validation

### Query Performance Test

#### Baseline Performance Metrics

```sql
-- Test query performance
EXPLAIN ANALYZE
SELECT COUNT(*) FROM information_schema.tables;

EXPLAIN ANALYZE
SELECT COUNT(*) FROM information_schema.columns;

EXPLAIN ANALYZE
SELECT COUNT(*) FROM pg_catalog.pg_class WHERE relkind = 'r';
```

#### Connection Pool Test

```python
#!/usr/bin/env python3
"""
Connection pool performance test
"""

import time
import concurrent.futures
import psycopg2
from psycopg2 import pool

def test_connection_pool():
    """Test connection pool performance"""

    # Create connection pool
    connection_pool = psycopg2.pool.ThreadedConnectionPool(
        1, 10,  # min and max connections
        host="your-extractor-app.com",
        database="production_db",
        user="atlan_service_user",
        password="secure_password"
    )

    def execute_query(query_id):
        """Execute a test query"""
        conn = connection_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables")
                result = cursor.fetchone()
                return f"Query {query_id}: {result[0]} tables"
        finally:
            connection_pool.putconn(conn)

    # Test concurrent connections
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(execute_query, i) for i in range(20)]
        results = [future.result() for future in futures]

    end_time = time.time()
    print(f"Executed 20 queries in {end_time - start_time:.2f} seconds")

    connection_pool.closeall()

if __name__ == "__main__":
    test_connection_pool()
```

## Automated Preflight Check Script

### Comprehensive Validation Script

```bash
#!/bin/bash
# Comprehensive preflight check script for [EXTRACTOR_APP_NAME] connector

set -e

# Configuration
EXTRACTOR_HOST="${EXTRACTOR_HOST:-your-extractor-app.com}"
EXTRACTOR_PORT="${EXTRACTOR_PORT:-5432}"
EXTRACTOR_DB="${EXTRACTOR_DB:-production_db}"
EXTRACTOR_USER="${EXTRACTOR_USER:-atlan_service_user}"
EXTRACTOR_PASS="${EXTRACTOR_PASS:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check system requirements
check_system_requirements() {
    log_info "Checking system requirements..."

    # Check CPU cores
    CPU_CORES=$(nproc)
    if [ $CPU_CORES -ge 2 ]; then
        log_info "CPU cores: $CPU_CORES ✓"
    else
        log_warn "CPU cores: $CPU_CORES (minimum 2 recommended)"
    fi

    # Check memory
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [ $MEMORY_GB -ge 4 ]; then
        log_info "Memory: ${MEMORY_GB}GB ✓"
    else
        log_warn "Memory: ${MEMORY_GB}GB (minimum 4GB recommended)"
    fi

    # Check disk space
    DISK_SPACE=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
    if [ $DISK_SPACE -ge 10 ]; then
        log_info "Disk space: ${DISK_SPACE}GB ✓"
    else
        log_warn "Disk space: ${DISK_SPACE}GB (minimum 10GB recommended)"
    fi
}

# Check network connectivity
check_network_connectivity() {
    log_info "Checking network connectivity..."

    # Test DNS resolution
    if nslookup $EXTRACTOR_HOST > /dev/null 2>&1; then
        log_info "DNS resolution for $EXTRACTOR_HOST ✓"
    else
        log_error "DNS resolution failed for $EXTRACTOR_HOST"
        return 1
    fi

    # Test port connectivity
    if nc -z $EXTRACTOR_HOST $EXTRACTOR_PORT; then
        log_info "Port $EXTRACTOR_PORT connectivity to $EXTRACTOR_HOST ✓"
    else
        log_error "Cannot connect to $EXTRACTOR_HOST:$EXTRACTOR_PORT"
        return 1
    fi

    # Test internet connectivity
    if ping -c 1 google.com > /dev/null 2>&1; then
        log_info "Internet connectivity ✓"
    else
        log_warn "No internet connectivity (may affect package installation)"
    fi
}

# Check database connectivity and permissions
check_database_access() {
    log_info "Checking database access..."

    if [ -z "$EXTRACTOR_PASS" ]; then
        log_error "Database password not provided (set EXTRACTOR_PASS environment variable)"
        return 1
    fi

    # Test basic connection
    if PGPASSWORD=$EXTRACTOR_PASS psql -h $EXTRACTOR_HOST -p $EXTRACTOR_PORT -U $EXTRACTOR_USER -d $EXTRACTOR_DB -c "SELECT 1;" > /dev/null 2>&1; then
        log_info "Database connection ✓"
    else
        log_error "Database connection failed"
        return 1
    fi

    # Test schema access
    SCHEMA_COUNT=$(PGPASSWORD=$EXTRACTOR_PASS psql -h $EXTRACTOR_HOST -p $EXTRACTOR_PORT -U $EXTRACTOR_USER -d $EXTRACTOR_DB -t -c "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast');" 2>/dev/null | xargs)

    if [ "$SCHEMA_COUNT" -gt 0 ]; then
        log_info "Schema access: $SCHEMA_COUNT schemas accessible ✓"
    else
        log_warn "No user schemas accessible"
    fi

    # Test table access
    TABLE_COUNT=$(PGPASSWORD=$EXTRACTOR_PASS psql -h $EXTRACTOR_HOST -p $EXTRACTOR_PORT -U $EXTRACTOR_USER -d $EXTRACTOR_DB -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_type = 'BASE TABLE' AND table_schema NOT IN ('information_schema', 'pg_catalog');" 2>/dev/null | xargs)

    if [ "$TABLE_COUNT" -gt 0 ]; then
        log_info "Table access: $TABLE_COUNT tables accessible ✓"
    else
        log_warn "No user tables accessible"
    fi
}

# Check software dependencies
check_dependencies() {
    log_info "Checking software dependencies..."

    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_info "Python version: $PYTHON_VERSION ✓"
    else
        log_error "Python 3 not found"
        return 1
    fi

    # Check pip
    if command -v pip3 &> /dev/null; then
        log_info "pip3 available ✓"
    else
        log_warn "pip3 not found (may affect package installation)"
    fi

    # Check psql client
    if command -v psql &> /dev/null; then
        log_info "PostgreSQL client available ✓"
    else
        log_warn "psql client not found (used for testing)"
    fi
}

# Main execution
main() {
    echo "========================================"
    echo "  [EXTRACTOR_APP_NAME] Preflight Checks"
    echo "========================================"
    echo

    check_system_requirements
    echo

    check_dependencies
    echo

    check_network_connectivity
    echo

    check_database_access
    echo

    log_info "Preflight checks completed!"
    echo
    echo "Next steps:"
    echo "1. Review any warnings or errors above"
    echo "2. Configure the connector with your settings"
    echo "3. Run a test crawl to validate the setup"
}

# Run main function
main "$@"
```

## Troubleshooting Common Issues

### Connection Issues

1. **Connection Timeout**

   ```bash
   # Test network latency
   ping -c 5 your-extractor-app.com

   # Test port connectivity with timeout
   timeout 10 telnet your-extractor-app.com 5432
   ```

2. **Authentication Failures**

   ```bash
   # Test credentials manually
   psql -h your-extractor-app.com -U atlan_service_user -d production_db

   # Check password policy compliance
   # Ensure password meets complexity requirements
   ```

3. **Permission Denied**

   ```sql
   -- Check current user permissions
   SELECT current_user, session_user;

   -- List accessible databases
   SELECT datname FROM pg_database WHERE datallowconn = true;

   -- Check schema permissions
   SELECT schema_name FROM information_schema.schemata;
   ```

### Performance Issues

1. **Slow Queries**

   ```sql
   -- Check query performance
   EXPLAIN (ANALYZE, BUFFERS)
   SELECT COUNT(*) FROM information_schema.tables;

   -- Check system load
   SELECT * FROM pg_stat_activity WHERE state = 'active';
   ```

2. **Resource Constraints**

   ```bash
   # Monitor system resources during checks
   top -p $(pgrep -f "preflight")

   # Check memory usage
   free -h

   # Check disk I/O
   iostat -x 1 5
   ```

## Next Steps

After completing all preflight checks:

1. ✅ **System Requirements Met**: Proceed with connector installation
2. ✅ **Network Connectivity Verified**: Configure connection settings
3. ✅ **Database Access Confirmed**: Set up crawling parameters
4. ✅ **Dependencies Installed**: Begin initial metadata extraction

If any checks fail:

1. 🔧 **Review Error Messages**: Address specific issues identified
2. 📞 **Contact System Administrator**: For permission or network issues
3. 📚 **Consult Documentation**: Review setup guides for your environment
4. 🆘 **Contact Support**: If issues persist after troubleshooting

## Automated Monitoring

Set up ongoing monitoring to ensure continued health:

```yaml
# Monitoring configuration
monitoring:
  health_checks:
    - name: "database_connectivity"
      interval: "5m"
      timeout: "30s"

    - name: "permission_validation"
      interval: "1h"
      timeout: "60s"

    - name: "resource_usage"
      interval: "1m"
      timeout: "10s"

  alerts:
    - condition: "connectivity_failure"
      severity: "critical"
      notification: "email"

    - condition: "high_resource_usage"
      severity: "warning"
      notification: "slack"
```
