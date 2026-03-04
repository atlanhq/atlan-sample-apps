import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.KeyFactory;
import java.security.PrivateKey;
import java.security.Signature;
import java.security.spec.PKCS8EncodedKeySpec;
import java.util.Base64;

/**
 * Generates the encodedData and encodedSignedData credential values required
 * for Anaplan CA Certificate authentication.
 *
 * Usage:
 *   javac GenerateCACertCredentials.java
 *   java GenerateCACertCredentials <username> <private_key.pem>
 *
 * The private key must be in PKCS#8 PEM format (begins with
 * "-----BEGIN PRIVATE KEY-----").
 */
public class GenerateCACertCredentials {

    public static void main(String[] args) throws Exception {
        if (args.length != 2) {
            System.err.println("Usage: java GenerateCACertCredentials <username> <private_key.pem>");
            System.exit(1);
        }

        String username = args[0];
        String keyFilePath = args[1];

        // 1. encodedData = Base64(username bytes)
        byte[] usernameBytes = username.getBytes(StandardCharsets.UTF_8);
        String encodedData = Base64.getEncoder().encodeToString(usernameBytes);

        // 2. Load PKCS#8 private key
        PrivateKey privateKey = loadPrivateKey(keyFilePath);

        // 3. encodedSignedData = Base64(SHA512withRSA signature over username bytes)
        Signature sig = Signature.getInstance("SHA512withRSA");
        sig.initSign(privateKey);
        sig.update(usernameBytes);
        byte[] signatureBytes = sig.sign();
        String encodedSignedData = Base64.getEncoder().encodeToString(signatureBytes);

        System.out.println("encodedData:       " + encodedData);
        System.out.println("encodedSignedData: " + encodedSignedData);
    }

    private static PrivateKey loadPrivateKey(String pemFilePath) throws Exception {
        String pem = new String(Files.readAllBytes(Paths.get(pemFilePath)), StandardCharsets.UTF_8);
        if (pem.contains("-----BEGIN RSA PRIVATE KEY-----")) {
            throw new IllegalArgumentException(
                "Key is in PKCS#1 format (BEGIN RSA PRIVATE KEY). "
                + "Please convert to PKCS#8 with: openssl pkcs8 -topk8 -inform PEM -outform PEM -in key.pem -out key_pkcs8.pem -nocrypt");
        }
        String stripped = pem
                .replace("-----BEGIN PRIVATE KEY-----", "")
                .replace("-----END PRIVATE KEY-----", "")
                .replaceAll("\\s+", "");
        byte[] derBytes = Base64.getDecoder().decode(stripped);
        PKCS8EncodedKeySpec keySpec = new PKCS8EncodedKeySpec(derBytes);
        KeyFactory kf = KeyFactory.getInstance("RSA");
        return kf.generatePrivate(keySpec);
    }
}
