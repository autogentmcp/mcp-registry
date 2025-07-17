# MCP Registry API Curl Examples

This directory contains example curl commands to demonstrate how to interact with the MCP Registry API.

## Available Examples

### Application Management

- **update_application.sh** / **update_application.bat** - Update an application's metadata
  - Updates an application's name, description, and healthCheckUrl
  - Uses PUT request to `/applications/{app_key}`

### Endpoint Management

- **register_endpoints.sh** / **register_endpoints.bat** - Register endpoints for an application
  - Registers multiple endpoints in a single request
  - Uses POST request to `/register/endpoints`
  - Includes complete endpoint definitions with path parameters, request/response schema, etc.
  - Requires both app key and API key for authentication

## How to Use

### On Linux/Mac:
1. Make the script executable:
   ```bash
   chmod +x update_application.sh
   chmod +x register_endpoints.sh
   ```

2. Edit the variables at the top of the script to match your environment:
   - `APP_KEY` - Your application's unique key
   - `API_KEY` - Your API key (for endpoints that require it)
   - `API_URL` - The URL of the MCP Registry API (default is http://localhost:8000)
   - `ENVIRONMENT` - The environment name (default is "production")

3. Run the script:
   ```bash
   ./update_application.sh
   ./register_endpoints.sh
   ```

### On Windows:
1. Edit the variables at the top of the batch file to match your environment:
   - `APP_KEY` - Your application's unique key
   - `API_KEY` - Your API key (for endpoints that require it)
   - `API_URL` - The URL of the MCP Registry API (default is http://localhost:8000)
   - `ENVIRONMENT` - The environment name (default is "production")

2. Run the batch file:
   ```cmd
   update_application.bat
   register_endpoints.bat
   ```

## Notes

- These examples assume that:
  - The MCP Registry server is running on localhost port 8000
  - You have an existing application with a valid app key
  - You have generated an API key for authentication
  - You have created the necessary environments

- For production use, you should:
  - Use HTTPS instead of HTTP
  - Implement proper error handling
  - Consider using a more robust API client instead of curl for complex workflows
