from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

# Application models
class ApplicationBase(BaseModel):
    name: str
    description: Optional[str] = None
    appKey: str
    authenticationMethod: Optional[str] = None
    healthCheckUrl: Optional[str] = None

class ApplicationUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Application name")
    description: Optional[str] = Field(None, description="Application description")
    healthCheckUrl: Optional[str] = Field(None, description="URL for health checking")

class ApplicationResponse(ApplicationBase):
    id: str
    status: str
    createdAt: datetime
    updatedAt: datetime
    userId: str

    class Config:
        from_attributes = True

# Environment models
class EnvironmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    baseDomain: Optional[str] = None

class EnvironmentCreate(EnvironmentBase):
    applicationId: str

class EnvironmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    baseDomain: Optional[str] = None

class EnvironmentResponse(EnvironmentBase):
    id: str
    status: str
    createdAt: datetime
    updatedAt: datetime
    applicationId: str

    class Config:
        from_attributes = True

# Endpoint models
class EndpointBase(BaseModel):
    name: str
    path: str
    method: str
    description: Optional[str] = None
    isPublic: bool = False
    pathParams: Optional[Dict[str, Any]] = None
    queryParams: Optional[Dict[str, Any]] = None
    requestBody: Optional[Dict[str, Any]] = None
    responseBody: Optional[Dict[str, Any]] = None

class EndpointResponse(BaseModel):
    id: str
    name: str
    path: str
    method: str
    description: Optional[str] = None
    isPublic: bool = False
    pathParams: Optional[Dict[str, Any]] = None
    queryParams: Optional[Dict[str, Any]] = None
    requestBody: Optional[Dict[str, Any]] = None
    responseBody: Optional[Dict[str, Any]] = None
    createdAt: datetime
    updatedAt: datetime
    applicationId: str
    environmentId: Optional[str] = None

    class Config:
        from_attributes = True
        
# Endpoint registration models
class EndpointRegistration(BaseModel):
    """Model for endpoint registration"""
    name: str
    path: str
    method: str
    description: Optional[str] = None
    isPublic: bool = False
    pathParams: Optional[Dict[str, Any]] = None
    queryParams: Optional[Dict[str, Any]] = None
    requestBody: Optional[Dict[str, Any]] = None
    responseBody: Optional[Dict[str, Any]] = None

class ApplicationEndpointsRegistration(BaseModel):
    """Model for registering multiple endpoints for an application"""
    app_key: str
    environment: str = "production"
    endpoints: List[EndpointRegistration]

class RegistrationResult(BaseModel):
    """Result of endpoint registration"""
    added: int = 0
    updated: int = 0
    deleted: int = 0
    message: str

# API Key models
class ApiKeyBase(BaseModel):
    name: str
    
class ApiKeyCreate(ApiKeyBase):
    applicationId: str
    environmentId: str
    userId: str
    expiresAt: Optional[datetime] = None

class ApiKeyResponse(ApiKeyBase):
    id: str
    token: str
    status: str
    expiresAt: Optional[datetime] = None
    lastUsed: Optional[datetime] = None
    createdAt: datetime
    updatedAt: datetime
    applicationId: str
    environmentId: str
    userId: str

    class Config:
        from_attributes = True

# Security models
class EnvironmentSecurityBase(BaseModel):
    rateLimitEnabled: bool = False
    rateLimitRequests: Optional[int] = None
    rateLimitWindow: Optional[int] = None
    vaultKey: Optional[str] = None

class EnvironmentSecurityCreate(EnvironmentSecurityBase):
    environmentId: str

# Note: EnvironmentSecurityUpdate is intentionally removed - 
# this service should not allow updates to environment security settings

class EnvironmentSecurityResponse(EnvironmentSecurityBase):
    id: str
    environmentId: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# Audit Log models
class AuditLogCreate(BaseModel):
    action: str
    details: Optional[str] = None
    ipAddress: Optional[str] = None
    userAgent: Optional[str] = None
    applicationId: Optional[str] = None

class AuditLogResponse(AuditLogCreate):
    id: str
    createdAt: datetime

    class Config:
        from_attributes = True

# Token models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Response models with nested relationships
class ApplicationWithEndpoints(ApplicationResponse):
    endpoints: List[EndpointResponse] = []
    environments: List[EnvironmentResponse] = []

class ApplicationsWithEndpoints(BaseModel):
    applications: List[ApplicationWithEndpoints] = []

class EndpointsWithEnvironmentResponse(BaseModel):
    """Response model for endpoints with environment data"""
    environment: EnvironmentResponse
    endpoints: List[EndpointResponse] = []
    
class ApplicationWithEnvironmentDetail(BaseModel):
    """Model for environment data that is included in application responses"""
    id: str
    name: str
    description: Optional[str] = None
    baseDomain: Optional[str] = None
    status: str
    createdAt: datetime
    updatedAt: datetime
    applicationId: str

class ApplicationWithEnvironmentDetailSecure(BaseModel):
    """Model for environment data with security details for admin responses"""
    id: str
    name: str
    description: Optional[str] = None
    baseDomain: Optional[str] = None
    status: str
    createdAt: datetime
    updatedAt: datetime
    applicationId: str
    security: Optional[EnvironmentSecurityResponse] = None
    
class ApplicationWithEnvironmentEndpoints(ApplicationResponse):
    """Response model for application with environment and endpoints"""
    environment: Optional[ApplicationWithEnvironmentDetail] = None
    endpoints: List[EndpointResponse] = []

class ApplicationWithEnvironmentEndpointsSecure(ApplicationResponse):
    """Response model for application with environment (including security) and endpoints"""
    environment: Optional[ApplicationWithEnvironmentDetailSecure] = None
    endpoints: List[EndpointResponse] = []

# Health Check Models
class HealthCheckLogResponse(BaseModel):
    """Response model for health check logs"""
    id: str
    applicationId: str
    environmentId: Optional[str] = None
    status: str  # 'success', 'failure', 'error'
    statusCode: Optional[int] = None
    responseTime: Optional[float] = None
    message: Optional[str] = None
    createdAt: datetime

    class Config:
        from_attributes = True

class EnvironmentHealthStatusResponse(BaseModel):
    """Response model for environment health status"""
    id: str
    name: str
    healthStatus: str  # 'ACTIVE', 'DEGRADED', 'INACTIVE', 'UNKNOWN'
    lastHealthCheckAt: Optional[datetime] = None

    class Config:
        from_attributes = True

class ApplicationHealthStatusResponse(BaseModel):
    """Response model for application health status"""
    id: str
    name: str
    healthStatus: str  # 'ACTIVE', 'DEGRADED', 'INACTIVE', 'UNKNOWN'
    lastHealthCheckAt: Optional[datetime] = None
    consecutiveFailures: int
    consecutiveSuccesses: int
    healthCheckUrl: Optional[str] = None
    environments: List[EnvironmentHealthStatusResponse] = []

    class Config:
        from_attributes = True

# Data Agent Models
class DataAgentBase(BaseModel):
    name: str
    description: Optional[str] = None
    connectionType: str  # "bigquery", "databricks", "postgres", "mysql", "sqlite", etc.

class DataAgentCreate(DataAgentBase):
    pass  # Only needs the base fields: name, description, connectionType

class DataAgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    connectionType: Optional[str] = None
    status: Optional[str] = None

class DataAgentResponse(DataAgentBase):
    id: str
    status: str  # ACTIVE, INACTIVE, CONNECTING, ERROR
    createdAt: datetime
    updatedAt: datetime
    userId: str

    class Config:
        from_attributes = True

# Data Agent Table Models
class DataAgentTableColumnBase(BaseModel):
    columnName: str
    dataType: str
    isNullable: bool = True
    defaultValue: Optional[str] = None
    comment: Optional[str] = None
    isIndexed: bool = False
    isPrimaryKey: bool = False
    isForeignKey: bool = False
    referencedTable: Optional[str] = None
    referencedColumn: Optional[str] = None
    aiDescription: Optional[str] = None

class DataAgentTableColumnResponse(DataAgentTableColumnBase):
    id: str
    tableId: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

class DataAgentTableBase(BaseModel):
    tableName: str
    schemaName: Optional[str] = None
    displayName: Optional[str] = None
    description: Optional[str] = None
    rowCount: Optional[int] = None
    isActive: bool = True

class DataAgentTableResponse(DataAgentTableBase):
    id: str
    dataAgentId: str
    analysisStatus: str  # PENDING, ANALYZING, COMPLETED, FAILED
    analysisResult: Optional[Dict[str, Any]] = None
    createdAt: datetime
    updatedAt: datetime
    columns: List[DataAgentTableColumnResponse] = []

    class Config:
        from_attributes = True

# Data Agent Relation Models
class DataAgentRelationBase(BaseModel):
    sourceTableId: str
    targetTableId: str
    relationshipType: str  # "one_to_one", "one_to_many", "many_to_many"
    sourceColumn: str
    targetColumn: str
    description: Optional[str] = None
    example: Optional[str] = None
    confidence: Optional[float] = None
    isVerified: bool = False

class DataAgentRelationCreate(DataAgentRelationBase):
    dataAgentId: str

class DataAgentRelationUpdate(BaseModel):
    relationshipType: Optional[str] = None
    sourceColumn: Optional[str] = None
    targetColumn: Optional[str] = None
    description: Optional[str] = None
    example: Optional[str] = None
    confidence: Optional[float] = None
    isVerified: Optional[bool] = None

class DataAgentRelationResponse(DataAgentRelationBase):
    id: str
    dataAgentId: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# Comprehensive Data Agent Response with nested data
class DataAgentWithTablesResponse(DataAgentResponse):
    tables: List[DataAgentTableResponse] = []
    relations: List[DataAgentRelationResponse] = []

# Environment-specific Data Agent Response Models
class DataAgentWithEnvironmentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    connectionType: str  # The database type for this data agent
    status: str
    userId: str
    createdAt: datetime
    updatedAt: datetime
    
    # Environment details
    environments: List[Dict] = []  # List of environments for this data agent
    tables: List[DataAgentTableResponse] = []  # Tables from specific environment if filtered
    relations: List[DataAgentRelationResponse] = []  # Relations from specific environment if filtered

    class Config:
        from_attributes = True

# Analysis Request/Response Models
class DataAgentAnalysisRequest(BaseModel):
    analysisType: str  # "tables", "relationships", "full"
    targetTables: Optional[List[str]] = None  # Specific tables to analyze

class DataAgentAnalysisResponse(BaseModel):
    analysisId: str
    status: str  # "started", "completed", "failed"
    message: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
