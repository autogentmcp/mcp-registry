# Example: Secure Registry and Proxy Architecture

# 1. Registry stores only metadata and secret references
# Example endpoint registration payload (sent from portal to registry):
endpoint_data = {
    "app_key": "myapp",
    "endpoint_uri": "/api/do-something",
    "endpoint_description": "Does something",
    "parameter_details": {},
    "security": {
        "type": "api_key",
        "header": "X-API-KEY",
        "secret_ref": "myapp_api_key"  # This is a reference, not the actual secret
    }
}

# 2. Portal stores the actual secret securely (e.g., in Akeyless, Vault, or encrypted DB)
# The secret_ref is mapped to the real secret in the secure store.

# 3. Proxy/router logic (Python example):
import os
import httpx

# Example: Load secret from environment or secret manager
SECRET_MAP = {
    "myapp_api_key": os.getenv("MYAPP_API_KEY")  # Or fetch from Vault/Akeyless
}

def get_secret(secret_ref):
    return SECRET_MAP.get(secret_ref)

async def call_secured_endpoint(endpoint, params=None):
    headers = {}
    security = endpoint.get("security", {})
    if security.get("type") == "api_key":
        secret = get_secret(security.get("secret_ref"))
        if secret:
            headers[security.get("header")] = secret
    # Add more security types as needed (e.g., signature, OAuth)
    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint["endpoint_uri"], headers=headers, params=params)
        return resp

# 4. The registry only ever sees the secret_ref, never the actual secret.
#    The proxy/router is responsible for securely loading and using the secret at runtime.

# --- Secure secret encryption/decryption example ---
from cryptography.fernet import Fernet

# 1. Generate a key (do this once and store it securely, e.g., as an env var)
# key = Fernet.generate_key()
# print(key)
FERNET_KEY = os.getenv("FERNET_KEY")  # Set this in your environment securely
fernet = Fernet(FERNET_KEY) if FERNET_KEY else None

# 2. Encrypt a secret before storing in Redis

def encrypt_secret(secret: str) -> str:
    if not fernet:
        raise RuntimeError("Fernet key not set!")
    return fernet.encrypt(secret.encode()).decode()

# 3. Decrypt a secret after retrieving from Redis

def decrypt_secret(token: str) -> str:
    if not fernet:
        raise RuntimeError("Fernet key not set!")
    return fernet.decrypt(token.encode()).decode()

# Example usage:
# encrypted = encrypt_secret("my-very-secret-key")
# decrypted = decrypt_secret(encrypted)
# print("Encrypted:", encrypted)
# print("Decrypted:", decrypted)

# In your registration, store the encrypted secret (not the raw value)
# In your proxy/router, decrypt before use
