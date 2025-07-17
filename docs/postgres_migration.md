# Migrating from Redis to PostgreSQL

This guide will help you migrate your MCP Registry from Redis to PostgreSQL.

## Prerequisites

1. A PostgreSQL database server
2. Python 3.9+
3. The latest version of the MCP Registry codebase

## Step 1: Set Up PostgreSQL

1. Create a new PostgreSQL database:
   ```sql
   CREATE DATABASE mcp_registry;
   ```

2. Configure your `.env` file with the PostgreSQL connection string:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/mcp_registry
   ```

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 3: Generate Prisma Client

```bash
prisma generate
```

## Step 4: Apply Database Schema

```bash
prisma db push
```

## Step 5: Migrate Data (Optional)

If you have existing data in Redis, you can use the migration script to transfer it to PostgreSQL:

```bash
python migrate_redis_to_postgres.py
```

The migration script reads data from Redis and creates corresponding entries in PostgreSQL.

## Step 6: Run the PostgreSQL Server

```bash
python run_postgres_server.py
```

## API Changes

### Endpoint Registration

**Redis Version**:
```
POST /register/endpoint
{
  "app_key": "myapp",
  "uri": "/api/do-something",
  "description": "Does something useful",
  "pathParams": {"param1": {"type": "string"}},
  "queryParams": {"param2": {"type": "integer"}},
  "requestBody": {"name": {"type": "string"}},
  "method": "POST"
}
```

**PostgreSQL Version**:
```
POST /register/endpoints
{
  "app_key": "myapp",
  "environment": "production",
  "endpoints": [
    {
      "name": "Do Something",
      "path": "/api/do-something",
      "method": "POST",
      "description": "Does something useful",
      "isPublic": false,
      "authType": "API_KEY",
      "pathParams": {"param1": {"type": "string"}},
      "queryParams": {"param2": {"type": "integer"}},
      "requestBody": {"name": {"type": "string"}}
    }
  ]
}
```

### Authentication

**Redis Version**:
```
# Header: X-API-KEY: your-admin-key
```

**PostgreSQL Version**:
```
# Headers:
X-API-Key: your-api-key
X-App-Key: your-app-key
X-Environment: production
```

## Benefits of PostgreSQL

1. **Data Integrity**: PostgreSQL enforces relationships between entities and prevents orphaned records.
2. **Schema Enforcement**: All data must conform to the defined schema.
3. **Transactional Support**: Multiple operations can be performed in a single transaction.
4. **Query Capabilities**: PostgreSQL provides powerful querying capabilities.
5. **Scalability**: PostgreSQL can handle large amounts of data efficiently.

## Troubleshooting

### Connection Issues

If you have trouble connecting to PostgreSQL, check:
- The PostgreSQL server is running
- The `DATABASE_URL` is correct
- Network connectivity to the database server

### Migration Issues

If the migration fails:
- Check that both Redis and PostgreSQL are accessible
- Ensure you have sufficient permissions on both databases
- Review the error message for specific issues

### Runtime Errors

If you encounter errors running the PostgreSQL server:
- Check the logs for specific error messages
- Ensure all dependencies are installed
- Verify the database schema was applied correctly
