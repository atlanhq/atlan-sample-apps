# Setup Private Network Link

This guide explains how to configure a private network link between Atlan and your [EXTRACTOR_APP_NAME] instance for enhanced security and performance.

> **Note**: All configuration examples in this document are for illustration purposes only. Adapt them to your specific environment and requirements.

## Overview

A private network link provides:

- **Enhanced Security**: Traffic doesn't traverse the public internet
- **Better Performance**: Reduced latency and improved throughput
- **Network Isolation**: Dedicated connection path
- **Compliance**: Meets strict security and regulatory requirements

## Prerequisites

- [ ] [EXTRACTOR_APP_NAME] instance deployed in a private network
- [ ] Network administrator access
- [ ] Understanding of your network topology
- [ ] Firewall and routing configuration permissions

## Network Architecture Options

### Option 1: VPC Peering (AWS)

For AWS-hosted [EXTRACTOR_APP_NAME] instances:

```yaml
# VPC Peering Configuration
vpc_peering:
  atlan_vpc: "vpc-12345678"
  extractor_vpc: "vpc-87654321"
  region: "us-east-1"
  route_tables:
    - "rtb-12345678"
    - "rtb-87654321"
```

**Setup Steps:**

1. Create VPC peering connection request
2. Accept peering connection in target VPC
3. Update route tables for both VPCs
4. Configure security groups

### Option 2: Private Endpoints (Azure)

For Azure-hosted [EXTRACTOR_APP_NAME] instances:

```yaml
# Private Endpoint Configuration
private_endpoint:
  resource_group: "extractor-app-rg"
  vnet: "extractor-app-vnet"
  subnet: "private-endpoint-subnet"
  service_connection: "extractor-app-connection"
```

**Setup Steps:**

1. Create private endpoint in your VNet
2. Configure DNS resolution
3. Update network security groups
4. Test connectivity

### Option 3: VPN Connection

For on-premises [EXTRACTOR_APP_NAME] instances:

```yaml
# VPN Configuration
vpn_connection:
  type: "site-to-site"
  gateway_ip: "203.0.113.1"
  shared_key: "your-shared-key"
  local_networks:
    - "10.0.0.0/16"
  remote_networks:
    - "192.168.0.0/16"
```

## Configuration Steps

### Step 1: Network Planning

1. **Identify Network Ranges**
   - Atlan network: `10.0.0.0/16`
   - [EXTRACTOR_APP_NAME] network: `192.168.0.0/16`
   - Ensure no IP conflicts

2. **Plan Routing**
   - Define routing rules
   - Identify required ports and protocols
   - Plan DNS resolution strategy

### Step 2: Firewall Configuration

Configure firewall rules to allow traffic:

```bash
# Example firewall rules
# Allow Atlan to connect to [EXTRACTOR_APP_NAME]
iptables -A INPUT -s 10.0.0.0/16 -p tcp --dport 5432 -j ACCEPT

# Allow return traffic
iptables -A OUTPUT -d 10.0.0.0/16 -p tcp --sport 5432 -j ACCEPT
```

### Required Ports

| Service              | Port | Protocol | Direction | Purpose             |
| -------------------- | ---- | -------- | --------- | ------------------- |
| [EXTRACTOR_APP_NAME] | 5432 | TCP      | Inbound   | Database connection |
| HTTPS                | 443  | TCP      | Outbound  | API calls           |
| DNS                  | 53   | UDP      | Outbound  | Name resolution     |

### Step 3: DNS Configuration

Configure DNS resolution for private endpoints:

```yaml
# DNS Configuration
dns_zones:
  - name: "extractor-app.private"
    records:
      - name: "db"
        type: "A"
        value: "192.168.1.10"
```

### Step 4: Security Groups/NSGs

Configure security groups to control access:

```yaml
# Security Group Rules
security_rules:
  - name: "allow-atlan-access"
    direction: "inbound"
    protocol: "tcp"
    port: "5432"
    source: "10.0.0.0/16"
    action: "allow"
```

## Testing Connectivity

### Step 1: Basic Connectivity Test

```bash
# Test network connectivity
ping 192.168.1.10

# Test port connectivity
telnet 192.168.1.10 5432
```

### Step 2: Application-Level Testing

```bash
# Test database connection
psql -h 192.168.1.10 -p 5432 -U atlan_user -d production
```

### Step 3: Performance Testing

```bash
# Test network performance
iperf3 -c 192.168.1.10 -p 5201
```

## Monitoring and Maintenance

### Network Monitoring

Set up monitoring for:

- **Connection Status**: Monitor VPN/peering connection health
- **Latency**: Track network round-trip times
- **Throughput**: Monitor data transfer rates
- **Error Rates**: Track connection failures

### Maintenance Tasks

- **Regular Health Checks**: Verify connectivity weekly
- **Certificate Renewal**: Update VPN certificates before expiry
- **Route Table Updates**: Maintain routing configurations
- **Security Review**: Audit firewall rules quarterly

## Security Best Practices

### Network Security

- **Principle of Least Privilege**: Only allow required ports and protocols
- **Network Segmentation**: Isolate [EXTRACTOR_APP_NAME] traffic
- **Encryption**: Use TLS/SSL for all data in transit
- **Access Logging**: Log all network access attempts

### Authentication

- **Service Accounts**: Use dedicated service accounts
- **Certificate-Based Auth**: Prefer certificates over passwords
- **Regular Rotation**: Rotate credentials regularly
- **Multi-Factor Authentication**: Enable MFA where supported

## Troubleshooting

### Common Issues

1. **Connection Timeouts**
   - Check firewall rules
   - Verify routing configuration
   - Test DNS resolution

2. **Authentication Failures**
   - Verify credentials
   - Check certificate validity
   - Review access permissions

3. **Performance Issues**
   - Monitor network latency
   - Check bandwidth utilization
   - Optimize connection pooling

### Diagnostic Commands

```bash
# Network diagnostics
traceroute 192.168.1.10
nslookup extractor-app.private
netstat -an | grep 5432

# Connection testing
nc -zv 192.168.1.10 5432
openssl s_client -connect 192.168.1.10:5432
```

## Next Steps

After setting up the private network link:

1. [Configure the extractor app connector](./setup-extractor-app.md) using private endpoints
2. [Set up crawling](../crawling/crawl-extractor-app.md) with optimized network settings
3. [Monitor performance](../troubleshooting/connectivity-troubleshooting.md) and optimize as needed

## Support

For network-related issues:

- Contact your network administrator
- Review [connectivity troubleshooting](../troubleshooting/connectivity-troubleshooting.md)
- Check vendor documentation for [EXTRACTOR_APP_NAME] networking requirements
