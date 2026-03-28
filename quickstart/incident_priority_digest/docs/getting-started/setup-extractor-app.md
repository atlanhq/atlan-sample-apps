# Setup Extractor App

This guide walks you through the process of setting up and configuring your [EXTRACTOR_APP_NAME] connector in Atlan.

> **Note**: All configuration examples in this document are for illustration purposes only. Adapt them to your specific environment and requirements.

## Overview

The [EXTRACTOR_APP_NAME] connector allows Atlan to extract metadata from your [EXTRACTOR_APP_NAME] instance, providing comprehensive data discovery and cataloging capabilities.

## Prerequisites

- [ ] [EXTRACTOR_APP_NAME] instance with appropriate access permissions
- [ ] Network connectivity between Atlan and [EXTRACTOR_APP_NAME]
- [ ] Valid credentials for [EXTRACTOR_APP_NAME] access

## Step 1: Gather Connection Information

Before configuring the connector, collect the following information:

### Required Parameters

- **Host/Server**: `[Your EXTRACTOR_APP_NAME server address]`
- **Port**: `[Default port number]`
- **Database/Schema**: `[Target database or schema name]`

### Authentication Details

- **Username**: `[Service account username]`
- **Password**: `[Service account password]`
- **Authentication Method**: `[e.g., Basic Auth, OAuth, API Key]`

### Optional Parameters

- **Connection Timeout**: `[Timeout in seconds]`
- **SSL Configuration**: `[SSL/TLS settings if required]`
- **Additional Parameters**: `[Any connector-specific parameters]`

## Step 2: Configure the Connector

### In Atlan Admin Center

1. Navigate to **Admin Center** → **Connectors**
2. Click **Add Connector** and select **[EXTRACTOR_APP_NAME]**
3. Fill in the connection details:

```yaml
# Example configuration
connection:
  host: "your-extractor-app.company.com"
  port: 5432
  database: "production_db"
  username: "atlan_service_user"
  password: "secure_password"
  ssl_mode: "require"
```

### Connection Settings

| Parameter | Description                   | Required | Example                     |
| --------- | ----------------------------- | -------- | --------------------------- |
| Host      | Server hostname or IP address | ✅       | `extractor-app.example.com` |
| Port      | Connection port               | ✅       | `5432`                      |
| Database  | Target database name          | ✅       | `production`                |
| Username  | Authentication username       | ✅       | `atlan_user`                |
| Password  | Authentication password       | ✅       | `••••••••`                  |
| SSL Mode  | SSL connection mode           | ❌       | `require`                   |

## Step 3: Test Connection

1. Click **Test Connection** to verify connectivity
2. Review any error messages and adjust settings if needed
3. Ensure all required permissions are granted

### Common Connection Issues

- **Connection Timeout**: Check network connectivity and firewall rules
- **Authentication Failed**: Verify username and password
- **Permission Denied**: Ensure the user has required database permissions

## Step 4: Configure Extraction Settings

### Metadata Extraction Options

- **Tables**: ✅ Extract table metadata
- **Views**: ✅ Extract view definitions
- **Columns**: ✅ Extract column information
- **Indexes**: ❌ Skip index metadata
- **Constraints**: ✅ Extract constraint information

### Filtering Options

```yaml
# Include/exclude patterns
include_schemas:
  - "public"
  - "analytics"
exclude_tables:
  - "temp_*"
  - "staging_*"
```

## Step 5: Schedule Extraction

Configure when and how often metadata extraction should run:

- **Frequency**: `Daily` | `Weekly` | `Monthly` | `Custom`
- **Time**: `02:00 AM UTC` (recommended for off-peak hours)
- **Incremental Updates**: `Enabled` (for faster subsequent runs)

## Step 6: Save and Deploy

1. Review all configuration settings
2. Click **Save Configuration**
3. Deploy the connector to start metadata extraction

## Verification

After deployment, verify the setup:

1. Check the connector status in the Admin Center
2. Monitor the first extraction run
3. Verify metadata appears in the Atlan catalog

## Next Steps

- [Setup Private Network Link](./setup-private-network-link.md) for enhanced security
- [Configure crawling settings](../crawling/crawl-extractor-app.md) for advanced metadata extraction
- [Review what gets crawled](../references/what-does-atlan-crawl.md) to understand the metadata scope

## Troubleshooting

If you encounter issues:

- Check the [Troubleshooting Guide](../troubleshooting/connectivity-troubleshooting.md)
- Review [Preflight Checks](../references/preflight-checks.md)
- Contact support with connector logs
