#!/bin/bash

# Application Update Curl Example
# This demonstrates how to update an application using the update endpoint

# Variables
APP_KEY="your-app-key"
API_KEY="your-api-key"
API_URL="http://localhost:8000/applications/$APP_KEY"

# Payload - Update name, description and health check URL
PAYLOAD='{
    "name": "Updated App Name",
    "description": "Updated application description",
    "healthCheckUrl": "https://myapp.example.com/health"
}'

# Execute the request
curl -X PUT "$API_URL" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: $API_KEY" \
     -H "X-App-Key: $APP_KEY" \
     -d "$PAYLOAD"

echo -e "\n\nCommand explanation:"
echo "- PUT request to update an application"
echo "- APP_KEY: The unique key identifying your application (in URL path and header)"
echo "- API_KEY: Authentication key for API access (in header)"
echo "- Payload contains only the fields allowed to be updated:"
echo "  * name: The new name for the application"
echo "  * description: The new description"
echo "  * healthCheckUrl: URL for health checking"
