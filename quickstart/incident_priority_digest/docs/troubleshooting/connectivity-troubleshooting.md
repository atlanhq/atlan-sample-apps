# Troubleshooting Extractor App Connectivity

This guide provides comprehensive troubleshooting steps for resolving connectivity issues between the Atlan connector and your [EXTRACTOR_APP_NAME] instance.

> **Note**: All configuration examples in this document are for illustration purposes only. Adapt them to your specific environment and requirements.

## Overview

Connectivity issues are among the most common problems encountered when setting up or running the [EXTRACTOR_APP_NAME] connector. These issues can manifest in various ways, from complete connection failures to intermittent timeouts during metadata extraction.

## Common Connectivity Issues

### Connection Timeout Errors

**Symptoms:**

- "Connection timed out" error messages
- Connector hangs during connection attempts
- Intermittent connection failures

**Possible Causes:**

- Network latency or packet loss
- Firewall blocking connections
- [EXTRACTOR_APP_NAME] server overloaded
- Incorrect timeout settings

### Connection Refused Errors

**Symptoms:**

- "Connection refused" error messages
- Immediate connection failures
- Cannot establish initial connection

**Possible Causes:**

- [EXTRACTOR_APP_NAME] service not running
- Wrong port number in configuration
- Service bound to localhost only
- Firewall blocking the port

### DNS Resolution Failures

**Symptoms:**

- "Host not found" or "Name resolution failed"
- Cannot resolve hostname to IP address
- Works with IP but not hostname

**Possible Causes:**

- DNS server configuration issues
- Hostname not registered in DNS
- Network DNS resolution problems
- Local hosts file conflicts

### SSL/TLS Connection Issues

**Symptoms:**

- SSL handshake failures
- Certificate verification errors
- "SSL required" messages

**Possible Causes:**

- SSL/TLS configuration mismatch
- Invalid or expired certificates
- Cipher suite incompatibility
- SSL version conflicts

## Diagnostic Steps

### Step 1: Basic Network Connectivity

#### Test Network Reachability

```bash
# Test basic connectivity to the host
ping -c 5 your-extractor-app.company.com

# Test with IP address if hostname fails
ping -c 5 192.168.1.100

# Check network route
traceroute your-extractor-app.company.com

# Test DNS resolution
nslookup your-extractor-app.company.com
dig your-extractor-app.company.com
```

#### Test Port Connectivity

```bash
# Test port connectivity with telnet
telnet your-extractor-app.company.com 5432

# Test with netcat (more reliable)
nc -zv your-extractor-app.company.com 5432

# Test with timeout
timeout 10 nc -zv your-extractor-app.company.com 5432

# Scan multiple ports
nmap -p 5432,5433,5434 your-extractor-app.company.com
```

### Step 2: Database-Specific Testing

#### Test Database Connection

```bash
# Test with psql client
psql -h your-extractor-app.company.com -p 5432 -U atlan_user -d production_db -c "SELECT version();"

# Test with connection timeout
psql -h your-extractor-app.company.com -p 5432 -U atlan_user -d production_db -c "SELECT 1;" --set=connect_timeout=10

# Test SSL connection
psql "host=your-extractor-app.company.com port=5432 dbname=production_db user=atlan_user sslmode=require"
```

#### Test Connection Pool

```python
#!/usr/bin/env python3
"""
Test connection pooling and concurrent connections
"""

import psycopg2
from psycopg2 import pool
import threading
import time

def test_connection_pool():
    """Test connection pool functionality"""

    try:
        # Create connection pool
        connection_pool = psycopg2.pool.ThreadedConnectionPool(
            1, 10,  # min and max connections
            host="your-extractor-app.company.com",
            port=5432,
            database="production_db",
            user="atlan_user",
            password="your_password",
            connect_timeout=10
        )

        def test_connection(thread_id):
            """Test individual connection"""
            try:
                conn = connection_pool.getconn()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT %s as thread_id, now() as timestamp", (thread_id,))
                    result = cursor.fetchone()
                    print(f"Thread {thread_id}: {result}")
                connection_pool.putconn(conn)
                return True
            except Exception as e:
                print(f"Thread {thread_id} failed: {e}")
                return False

        # Test concurrent connections
        threads = []
        for i in range(5):
            thread = threading.Thread(target=test_connection, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        connection_pool.closeall()
        print("Connection pool test completed successfully")

    except Exception as e:
        print(f"Connection pool test failed: {e}")

if __name__ == "__main__":
    test_connection_pool()
```

### Step 3: Firewall and Security Testing

#### Check Local Firewall

```bash
# Check iptables rules (Linux)
sudo iptables -L -n | grep 5432

# Check firewalld (CentOS/RHEL)
sudo firewall-cmd --list-ports
sudo firewall-cmd --list-services

# Check ufw (Ubuntu)
sudo ufw status verbose

# Check for blocked connections
sudo netstat -tulpn | grep 5432
```

#### Test from Different Locations

```bash
# Test from the connector host
nc -zv your-extractor-app.company.com 5432

# Test from another host in the same network
ssh other-host "nc -zv your-extractor-app.company.com 5432"

# Test from outside the network (if applicable)
ssh external-host "nc -zv your-extractor-app.company.com 5432"
```

### Step 4: SSL/TLS Diagnostics

#### Test SSL Connection

```bash
# Test SSL handshake
openssl s_client -connect your-extractor-app.company.com:5432 -starttls postgres

# Check certificate details
echo | openssl s_client -connect your-extractor-app.company.com:5432 -starttls postgres 2>/dev/null | openssl x509 -noout -text

# Test specific SSL version
openssl s_client -connect your-extractor-app.company.com:5432 -starttls postgres -tls1_2

# Check certificate expiration
echo | openssl s_client -connect your-extractor-app.company.com:5432 -starttls postgres 2>/dev/null | openssl x509 -noout -dates
```

#### Verify SSL Configuration

```sql
-- Check SSL status on the database
SHOW ssl;

-- Check SSL cipher information
SELECT * FROM pg_stat_ssl WHERE pid = pg_backend_pid();

-- Check SSL certificate information
SELECT * FROM pg_stat_ssl;
```

## Common Solutions

### Network Connectivity Solutions

#### DNS Resolution Issues

**Solution 1: Use IP Address**

```yaml
# Temporarily use IP address instead of hostname
connection:
  host: "192.168.1.100" # Instead of hostname
  port: 5432
```

**Solution 2: Configure Local DNS**

```bash
# Add entry to /etc/hosts
echo "192.168.1.100 your-extractor-app.company.com" | sudo tee -a /etc/hosts

# Or configure DNS server
echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf
```

**Solution 3: Verify DNS Configuration**

```bash
# Check current DNS configuration
cat /etc/resolv.conf

# Test with different DNS server
nslookup your-extractor-app.company.com 8.8.8.8
```

#### Firewall Configuration

**Solution 1: Configure Local Firewall**

```bash
# Allow outbound connections to [EXTRACTOR_APP_NAME] (iptables)
sudo iptables -A OUTPUT -p tcp --dport 5432 -d your-extractor-app.company.com -j ACCEPT

# Allow outbound connections (firewalld)
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --reload

# Allow outbound connections (ufw)
sudo ufw allow out 5432/tcp
```

**Solution 2: Configure Remote Firewall**

```bash
# On the [EXTRACTOR_APP_NAME] server, allow inbound connections
sudo iptables -A INPUT -p tcp --dport 5432 -s connector-host-ip -j ACCEPT

# Or allow from entire subnet
sudo iptables -A INPUT -p tcp --dport 5432 -s 10.0.0.0/24 -j ACCEPT
```

### Connection Configuration Solutions

#### Timeout Configuration

```yaml
# Increase connection timeouts
connection:
  host: "your-extractor-app.company.com"
  port: 5432
  connect_timeout: 30 # Increase from default 10
  query_timeout: 300 # 5 minutes for long queries
  socket_timeout: 60 # Socket-level timeout

# Connection pool settings
pool:
  pool_timeout: 30 # Time to wait for connection from pool
  pool_recycle: 3600 # Recycle connections after 1 hour
  pool_pre_ping: true # Test connections before use
```

#### Retry Configuration

```yaml
# Configure connection retry behavior
retry:
  max_attempts: 3
  backoff_strategy: "exponential"
  initial_delay: 1 # Start with 1 second delay
  max_delay: 60 # Maximum 60 second delay
  backoff_multiplier: 2 # Double delay each retry
```

### SSL/TLS Configuration Solutions

#### SSL Mode Configuration

```yaml
# SSL configuration options
connection:
  host: "your-extractor-app.company.com"
  port: 5432
  ssl_mode: "require" # require | prefer | allow | disable
  ssl_cert: "/path/to/client.crt"
  ssl_key: "/path/to/client.key"
  ssl_ca: "/path/to/ca.crt"
  ssl_check_hostname: false # Disable hostname verification if needed
```

#### Certificate Issues

**Solution 1: Disable SSL Temporarily**

```yaml
# For testing only - not recommended for production
connection:
  ssl_mode: "disable"
```

**Solution 2: Use Custom CA Certificate**

```yaml
# Use custom CA certificate
connection:
  ssl_mode: "require"
  ssl_ca: "/path/to/custom-ca.crt"
  ssl_check_hostname: false
```

**Solution 3: Skip Certificate Verification**

```yaml
# Skip certificate verification (testing only)
connection:
  ssl_mode: "require"
  ssl_check_hostname: false
  ssl_verify_cert: false
```

### Performance Optimization Solutions

#### Connection Pool Optimization

```yaml
# Optimize connection pool for better performance
connection_pool:
  pool_size: 10 # Base number of connections
  max_overflow: 20 # Additional connections when needed
  pool_timeout: 30 # Wait time for connection
  pool_recycle: 3600 # Recycle connections hourly
  pool_pre_ping: true # Test connections before use

# Connection optimization
connection:
  tcp_keepalives_idle: 600 # Start keepalives after 10 minutes
  tcp_keepalives_interval: 30 # Send keepalive every 30 seconds
  tcp_keepalives_count: 3 # Drop connection after 3 failed keepalives
```

#### Query Optimization

```yaml
# Optimize queries for better performance
extraction:
  batch_size: 1000 # Process in smaller batches
  parallel_workers: 4 # Use multiple workers
  query_timeout: 300 # 5 minute query timeout

# Memory optimization
memory:
  streaming_mode: true # Use streaming for large results
  fetch_size: 1000 # Fetch results in batches
  buffer_size: "64KB" # Network buffer size
```

## Advanced Troubleshooting

### Network Analysis

#### Packet Capture Analysis

```bash
# Capture network traffic to [EXTRACTOR_APP_NAME]
sudo tcpdump -i any -w capture.pcap host your-extractor-app.company.com and port 5432

# Analyze with wireshark
wireshark capture.pcap

# Or analyze with tcpdump
tcpdump -r capture.pcap -A | grep -i "error\|timeout\|reset"
```

#### Network Performance Testing

```bash
# Test network bandwidth
iperf3 -c your-extractor-app.company.com -p 5201

# Test network latency under load
ping -f -c 1000 your-extractor-app.company.com

# Test MTU size
ping -M do -s 1472 your-extractor-app.company.com
```

### Database Server Analysis

#### Check Server Status

```sql
-- Check server status and connections
SELECT * FROM pg_stat_activity WHERE state = 'active';

-- Check connection limits
SELECT setting FROM pg_settings WHERE name = 'max_connections';

-- Check current connection count
SELECT count(*) FROM pg_stat_activity;

-- Check for connection errors
SELECT * FROM pg_stat_database WHERE datname = 'production_db';
```

#### Monitor Server Performance

```bash
# Monitor server resources
ssh your-extractor-app.company.com "top -b -n 1 | head -20"

# Check disk space
ssh your-extractor-app.company.com "df -h"

# Check network connections
ssh your-extractor-app.company.com "netstat -an | grep 5432"

# Check server logs
ssh your-extractor-app.company.com "tail -f /var/log/postgresql/postgresql.log"
```

### Load Balancer and Proxy Issues

#### Test Direct Connection

```bash
# Bypass load balancer and connect directly
psql -h direct-server-ip -p 5432 -U atlan_user -d production_db

# Compare with load balancer connection
psql -h load-balancer.company.com -p 5432 -U atlan_user -d production_db
```

#### Check Proxy Configuration

```bash
# Test HTTP proxy (if applicable)
curl -x proxy.company.com:8080 http://your-extractor-app.company.com:5432

# Check proxy logs
sudo tail -f /var/log/squid/access.log | grep your-extractor-app.company.com
```

## Monitoring and Prevention

### Connection Monitoring

```yaml
# Set up connection monitoring
monitoring:
  connection_health:
    enabled: true
    check_interval: "30s"
    timeout: "10s"
    retry_attempts: 3

  metrics:
    - "connection_success_rate"
    - "connection_latency"
    - "connection_pool_usage"
    - "query_execution_time"
```

### Automated Health Checks

```bash
#!/bin/bash
# Automated connectivity health check script

EXTRACTOR_HOST="your-extractor-app.company.com"
EXTRACTOR_PORT="5432"
EXTRACTOR_USER="atlan_user"
EXTRACTOR_DB="production_db"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Test network connectivity
test_network() {
    if ping -c 1 -W 5 $EXTRACTOR_HOST > /dev/null 2>&1; then
        log_message "✓ Network connectivity: OK"
        return 0
    else
        log_message "✗ Network connectivity: FAILED"
        return 1
    fi
}

# Test port connectivity
test_port() {
    if nc -z -w 5 $EXTRACTOR_HOST $EXTRACTOR_PORT; then
        log_message "✓ Port connectivity: OK"
        return 0
    else
        log_message "✗ Port connectivity: FAILED"
        return 1
    fi
}

# Test database connection
test_database() {
    if PGPASSWORD=$EXTRACTOR_PASS psql -h $EXTRACTOR_HOST -p $EXTRACTOR_PORT -U $EXTRACTOR_USER -d $EXTRACTOR_DB -c "SELECT 1;" > /dev/null 2>&1; then
        log_message "✓ Database connection: OK"
        return 0
    else
        log_message "✗ Database connection: FAILED"
        return 1
    fi
}

# Run all tests
main() {
    log_message "Starting connectivity health check..."

    test_network
    network_status=$?

    test_port
    port_status=$?

    test_database
    db_status=$?

    if [ $network_status -eq 0 ] && [ $port_status -eq 0 ] && [ $db_status -eq 0 ]; then
        log_message "✓ All connectivity checks passed"
        exit 0
    else
        log_message "✗ One or more connectivity checks failed"
        exit 1
    fi
}

# Run the health check
main
```

### Alerting Configuration

```yaml
# Configure alerts for connectivity issues
alerts:
  - name: "connection_failure"
    condition: "connection_success_rate < 0.9"
    duration: "5m"
    severity: "critical"
    message: "High connection failure rate detected"

  - name: "high_latency"
    condition: "connection_latency > 1000" # 1 second
    duration: "10m"
    severity: "warning"
    message: "High connection latency detected"

  - name: "pool_exhaustion"
    condition: "connection_pool_usage > 0.9"
    duration: "2m"
    severity: "warning"
    message: "Connection pool near exhaustion"
```

## Getting Help

### Information to Gather

When seeking help with connectivity issues, gather the following information:

1. **Error Messages**
   - Complete error messages from logs
   - Error codes and timestamps
   - Frequency of occurrence

2. **Network Information**
   - Source and destination IP addresses
   - Network topology (firewalls, load balancers, proxies)
   - DNS configuration

3. **Configuration Details**
   - Connection configuration (sanitized)
   - SSL/TLS settings
   - Timeout and retry settings

4. **Diagnostic Results**
   - Results of diagnostic commands
   - Network traces (if available)
   - Server logs (if accessible)

### Escalation Process

1. **Self-Diagnosis**: Use this troubleshooting guide
2. **Community Support**: Post in community forums with diagnostic information
3. **Professional Support**: Contact support with complete diagnostic bundle
4. **Engineering Escalation**: For complex network or infrastructure issues

### Support Bundle Generation

```bash
# Generate comprehensive support bundle
atlan-connector support-bundle \
  --name extractor-app \
  --include-logs \
  --include-config \
  --include-diagnostics \
  --output connectivity-support.zip
```

This support bundle will include all relevant information needed to diagnose connectivity issues effectively.
