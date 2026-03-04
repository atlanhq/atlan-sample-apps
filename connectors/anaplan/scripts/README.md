# scripts/

## GenerateCACertCredentials.java

Standalone utility that produces the `encodedData` and `encodedSignedData` values
required when configuring **CA Certificate** authentication for the Anaplan connector.

### Prerequisites

- Java 8 or later (`java -version`)
- An RSA private key in **PKCS#8 PEM** format — the file must begin with
  `-----BEGIN PRIVATE KEY-----`.
  If your key is in traditional (PKCS#1) format (`-----BEGIN RSA PRIVATE KEY-----`),
  convert it first:
  ```bash
  openssl pkcs8 -topk8 -inform PEM -outform PEM -nocrypt \
    -in private_key.pem -out private_key_pkcs8.pem
  ```

### Compile

```bash
javac GenerateCACertCredentials.java
```

### Run

```bash
java GenerateCACertCredentials <username> <private_key_pkcs8.pem>
```

**Arguments**

| Argument | Description |
|---|---|
| `<username>` | The Anaplan account username (email address) |
| `<private_key_pkcs8.pem>` | Path to the PKCS#8 PEM private key file |

### Output

```
encodedData:       <Base64-encoded username>
encodedSignedData: <Base64-encoded SHA512withRSA signature>
```

Copy these two values into the Anaplan connector credential fields:

| Output field | Credential field |
|---|---|
| `encodedData` | **Username** |
| `encodedSignedData` | **Password** |
