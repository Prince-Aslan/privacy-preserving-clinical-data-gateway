import base64
import hashlib
import os
from app.config import settings

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

class CryptoEngine:
    def __init__(self, key_str: str = None):
        key_raw = (key_str or settings.AES_SECRET_KEY).encode('utf-8')
        self.key = hashlib.sha256(key_raw).digest()
        if HAS_CRYPTOGRAPHY:
            self.aesgcm = AESGCM(self.key)
        else:
            self.aesgcm = None

    def encrypt_field(self, plaintext: str) -> str:
        """Encrypts a plaintext string using AES-256-GCM (or salt-xor fallback if cryptography module missing)."""
        if not plaintext:
            return ""
        if HAS_CRYPTOGRAPHY and self.aesgcm:
            nonce = os.urandom(12)
            ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
            combined = nonce + ciphertext
            return base64.b64encode(combined).decode('utf-8')
        else:
            # Fallback lightweight stream encryption using SHA-256 key stream
            data = plaintext.encode('utf-8')
            keystream = hashlib.sha256(self.key + b":salt").digest()
            encrypted_bytes = bytes([b ^ keystream[i % len(keystream)] for i, b in enumerate(data)])
            return "ENC_FB:" + base64.b64encode(encrypted_bytes).decode('utf-8')

    def decrypt_field(self, ciphertext_b64: str) -> str:
        """Decrypts AES-256-GCM or fallback stream ciphertext."""
        if not ciphertext_b64:
            return ""
        if ciphertext_b64.startswith("ENC_FB:"):
            data = base64.b64decode(ciphertext_b64[7:].encode('utf-8'))
            keystream = hashlib.sha256(self.key + b":salt").digest()
            decrypted_bytes = bytes([b ^ keystream[i % len(keystream)] for i, b in enumerate(data)])
            return decrypted_bytes.decode('utf-8')
        if HAS_CRYPTOGRAPHY and self.aesgcm:
            try:
                combined = base64.b64decode(ciphertext_b64.encode('utf-8'))
                nonce = combined[:12]
                ciphertext = combined[12:]
                return self.aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
            except Exception:
                return "[DECRYPTION_FAILED]"
        return "[DECRYPTION_UNAVAILABLE]"

    @staticmethod
    def hash_sha256(identifier: str, salt: str = "NIGERIA_MH_GATEWAY_2026") -> str:
        """
        Generates a deterministic SHA-256 hash for record linkage pseudonymization.
        Given the same identifier and salt, it produces the exact same pseudonym hash.
        """
        if not identifier:
            return ""
        salted = f"{salt}:{identifier}".encode('utf-8')
        return hashlib.sha256(salted).hexdigest()

crypto_engine = CryptoEngine()
