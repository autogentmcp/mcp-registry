@echo off
REM Application Update Curl Example for Windows
REM This demonstrates how to update an application using the update endpoint

REM Variables
set APP_KEY=your-app-key
set API_KEY=your-api-key
set API_URL=http://localhost:8000/applications/%APP_KEY%

REM Execute the request (Windows curl requires escaped quotes)
curl -X PUT "%API_URL%" ^
     -H "Content-Type: application/json" ^
     -H "X-API-Key: %API_KEY%" ^
     -H "X-App-Key: %APP_KEY%" ^
     -d "{\"name\": \"Updated App Name\", \"description\": \"Updated application description\", \"healthCheckUrl\": \"https://myapp.example.com/health\"}"

echo.
echo Command explanation:
echo - PUT request to update an application
echo - APP_KEY: The unique key identifying your application (in URL path and header)
echo - API_KEY: Authentication key for API access (in header)
echo - Payload contains only the fields allowed to be updated:
echo   * name: The new name for the application
echo   * description: The new description
echo   * healthCheckUrl: URL for health checking
