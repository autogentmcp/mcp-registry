# API Key Security Implementation

## Overview

The MCP Registry now supports hashed API keys for enhanced security. API keys are stored in the database using bcrypt hashing (compatible with Node.js `bcrypt.hash(apiKey, 10)`) and verified using Python's bcrypt library.

## Changes Made

### 1. Updated Authentication Logic

#### Files Modified:
- `src/mcp_registry/auth.py`
- `src/mcp_registry/server.py`
- `src/mcp_registry/endpoint_registration.py`

#### Key Changes:
- Added bcrypt import to all authentication modules
- Replaced direct token lookup with bcrypt verification
- Updated API key verification to hash the provided key and compare with stored hashes
- Added proper error handling for bcrypt verification failures

### 2. Authentication Flow

The new authentication flow works as follows:

1. **Client Request**: Client sends a plain text API key in the `X-API-Key` header along with app key and environment
2. **Database Lookup**: System fetches API keys for the specific application and environment combination
3. **Verification**: System uses `bcrypt.checkpw()` to verify the provided key against each stored hash
4. **Success/Failure**: If any hash matches, authentication succeeds; otherwise, it fails

**Important**: API keys are now validated against specific environments. Each API key is tied to both an application and an environment, providing better security isolation.

### 3. Code Example

```python
# Old approach (vulnerable)
api_key_obj = await prisma.apikey.find_unique(
    where={"token": api_key}
)

# New approach (secure with environment validation)
api_keys = await prisma.apikey.find_many(
    where={
        "applicationId": app.id,
        "environmentId": env.id  # Environment-specific validation
    }
)

valid_api_key = None
for stored_key in api_keys:
    if bcrypt.checkpw(api_key.encode('utf-8'), stored_key.token.encode('utf-8')):
        valid_api_key = stored_key
        break
```

### 4. Compatibility

This implementation is fully compatible with Node.js applications that use:
```javascript
const hashedKey = await bcrypt.hash(apiKey, 10);
```

### 5. Security Benefits

- **No Plain Text Storage**: API keys are never stored in plain text
- **Bcrypt Protection**: Uses industry-standard bcrypt hashing with salt
- **Environment Isolation**: API keys are validated against specific environments
- **Brute Force Resistance**: Bcrypt's computational cost makes brute force attacks impractical
- **Cross-Platform Compatibility**: Works with both Node.js and Python applications
- **Proper Authorization**: Ensures API keys can only access their intended environment

## Testing

The implementation includes a test script (`test_bcrypt.py`) that verifies:
- Correct hashing of API keys
- Successful verification of valid keys
- Rejection of invalid keys

## Dependencies

Added to `requirements.txt`:
```
bcrypt>=4.0.0
```

## Migration Notes

If you have existing API keys in plain text, you'll need to:
1. Hash them using bcrypt with salt rounds of 10
2. Update the database with the hashed values
3. Ensure client applications continue to send the original plain text keys

The system will automatically handle the verification of hashed keys against plain text inputs.
