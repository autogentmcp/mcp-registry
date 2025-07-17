@echo off
REM Register Endpoints Curl Example for Windows
REM This demonstrates how to register multiple endpoints for an application

REM Variables
set APP_KEY=your-app-key
set API_KEY=your-api-key
set API_URL=http://localhost:8000/register/endpoints
set ENVIRONMENT=production

REM Execute the request (Windows curl requires escaped quotes)
curl -X POST "%API_URL%" ^
     -H "Content-Type: application/json" ^
     -H "X-App-Key: %APP_KEY%" ^
     -H "X-API-Key: %API_KEY%" ^
     -d "{\"app_key\": \"%APP_KEY%\", \"environment\": \"%ENVIRONMENT%\", \"endpoints\": [{\"name\": \"Get User\", \"path\": \"/api/users/{id}\", \"method\": \"GET\", \"description\": \"Retrieve user details by ID\", \"isPublic\": false, \"pathParams\": {\"id\": {\"type\": \"string\", \"description\": \"User ID\"}}, \"queryParams\": null, \"requestBody\": null, \"responseBody\": {\"type\": \"object\", \"properties\": {\"id\": {\"type\": \"string\"}, \"name\": {\"type\": \"string\"}, \"email\": {\"type\": \"string\"}}}}, {\"name\": \"Create User\", \"path\": \"/api/users\", \"method\": \"POST\", \"description\": \"Create a new user\", \"isPublic\": false, \"pathParams\": null, \"queryParams\": null, \"requestBody\": {\"type\": \"object\", \"required\": [\"name\", \"email\"], \"properties\": {\"name\": {\"type\": \"string\"}, \"email\": {\"type\": \"string\"}}}, \"responseBody\": {\"type\": \"object\", \"properties\": {\"id\": {\"type\": \"string\"}, \"name\": {\"type\": \"string\"}, \"email\": {\"type\": \"string\"}}}}]}"

echo.
echo Command explanation:
echo - POST request to register multiple endpoints for an application
echo - APP_KEY: The unique key identifying your application
echo - API_KEY: Authentication key for API access
echo - ENVIRONMENT: The target environment (production, staging, etc.)
echo - Payload contains app_key, environment, and an array of endpoint definitions
