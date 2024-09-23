import crypto from "crypto";
import { atob, btoa } from "abab";
// Function to derive a key from a secret string using PBKDF2
function deriveKeyFromSecret(secret, salt, keyLength = 32) {
    return crypto.pbkdf2Sync(secret, salt, 100000, keyLength, 'sha256');  // 100000 iterations of SHA-256
}

// Function to encrypt data using AES-GCM
export function encryptWithSecret(plaintext, secret) {
    const iv = crypto.randomBytes(12);  // 96-bit IV for AES-GCM
    const salt = crypto.randomBytes(16); // 128-bit salt for PBKDF2
    const key = deriveKeyFromSecret(secret, salt);

    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
    let encrypted = cipher.update(plaintext, 'utf8');
    encrypted = Buffer.concat([encrypted, cipher.final()]);

    const authTag = cipher.getAuthTag();
    let final =  {
        encrypted: encrypted.toString('hex'),
        authTag: authTag.toString('hex'),
        iv: iv.toString('hex'),
        salt: salt.toString('hex')
    };

    return btoa(JSON.stringify(final));
}

// Function to decrypt data using AES-GCM
export function decryptWithSecret(encryptedData, secret) {
    const { encrypted, authTag, iv, salt } = JSON.parse(atob(encryptedData));

    const key = deriveKeyFromSecret(secret, Buffer.from(salt, 'hex'));

    const decipher = crypto.createDecipheriv('aes-256-gcm', key, Buffer.from(iv, 'hex'));
    decipher.setAuthTag(Buffer.from(authTag, 'hex'));

    let decrypted = decipher.update(Buffer.from(encrypted, 'hex'));
    decrypted = Buffer.concat([decrypted, decipher.final()]);

    return decrypted.toString('utf8');
}