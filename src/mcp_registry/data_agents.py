"""
Data Agents API endpoints for the MCP Registry.

This module provides endpoints for managing data agents, including:
- CRUD operations for data agents
- Table discovery and import
- AI-powered analysis
- Relationship management
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from .config import settings
from .database import get_prisma
from .auth import verify_admin_key
from .models import (
    DataAgentCreate,
    DataAgentUpdate,
    DataAgentResponse,
    DataAgentWithTablesResponse,
    DataAgentWithEnvironmentResponse,
    DataAgentTableResponse,
    DataAgentRelationCreate,
    DataAgentRelationUpdate,
    DataAgentRelationResponse,
    DataAgentAnalysisRequest,
    DataAgentAnalysisResponse
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/data-agents", tags=["data-agents"])


@router.get("/", response_model=List[DataAgentResponse])
async def list_data_agents(
    admin_key: str = Depends(verify_admin_key),
    status: Optional[str] = None
):
    """
    List all data agents in the system.
    Requires admin authentication.
    
    Args:
        status: Optional filter by status (ACTIVE, INACTIVE, CONNECTING, ERROR)
    """
    async with get_prisma() as prisma:
        where_clause = {}
        if status:
            where_clause["status"] = status
            
        data_agents = await prisma.dataagent.find_many(
            where=where_clause,
            order={"createdAt": "desc"}
        )
        return data_agents


# New endpoints as requested - placed before /{agent_id} to avoid path conflicts
@router.get("/list", response_model=List[DataAgentResponse])
async def get_data_agents_list(
    environment: str,
    admin_key: str = Depends(verify_admin_key)
):
    """
    Get a simple list of all data agents for a specific environment.
    Data agents are independent entities with name, description, and connectionType.
    Each data agent can have multiple environments.
    Only returns data agents that have the specified environment.
    """
    async with get_prisma() as prisma:
        # Get all data agents that have the specified environment
        data_agents = await prisma.dataagent.find_many(
            where={
                "environments": {
                    "some": {
                        "name": environment
                    }
                }
            },
            order={"createdAt": "desc"}
        )
        return data_agents


@router.get("/with-environment-details", response_model=List[DataAgentWithEnvironmentResponse])
async def get_data_agents_with_environment_details(
    environment: str,
    admin_key: str = Depends(verify_admin_key)
):
    """
    Get data agents with their environment details, tables, and relations.
    
    Args:
        environment: Required environment name (e.g., production, staging).
                    Only returns data agents that have this environment,
                    and only shows tables/relations for this specific environment.
    """
    async with get_prisma() as prisma:
        # Get all data agents that have the specified environment
        data_agents = await prisma.dataagent.find_many(
            where={
                "environments": {
                    "some": {
                        "name": environment
                    }
                }
            },
            include={
                "environments": True  # Get all environments for each data agent
            },
            order={"createdAt": "desc"}
        )
        
        result = []
        for agent in data_agents:
            # Find the target environment (we know it exists because of our query filter)
            target_environment = next(
                (env for env in agent.environments if env.name == environment), 
                None
            )
            # This should not happen due to our query filter, but safety check
            if not target_environment:
                continue
            
            # Get tables and relations for the specific environment
            where_tables = {"dataAgentId": agent.id, "environmentId": target_environment.id}
            where_relations = {"dataAgentId": agent.id, "environmentId": target_environment.id}
            
            # Fetch tables and relations
            tables = await prisma.dataagenttable.find_many(
                where=where_tables,
                include={"columns": True}
            )
            
            relations = await prisma.dataagentrelation.find_many(
                where=where_relations
            )
            
            agent_dict = {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "status": agent.status,
                "connectionType": agent.connectionType,
                "userId": agent.userId,
                "createdAt": agent.createdAt,
                "updatedAt": agent.updatedAt,
                "environments": [target_environment.__dict__],  # Only show the specific environment
                "tables": tables or [],
                "relations": relations or []
            }
            result.append(agent_dict)
            
        return result


@router.get("/{agent_id}/environment-details", response_model=DataAgentWithEnvironmentResponse)
async def get_data_agent_environment_details(
    agent_id: str,
    environment: str,
    admin_key: str = Depends(verify_admin_key)
):
    """
    Get details of a specific data agent for a specific environment.
    
    Args:
        agent_id: Required ID of the data agent
        environment: Required environment name (e.g., production, staging)
                    Only returns data for this specific environment
    """
    async with get_prisma() as prisma:
        # Get the specific data agent with its environments
        data_agent = await prisma.dataagent.find_unique(
            where={"id": agent_id},
            include={
                "environments": True
            }
        )
        
        if not data_agent:
            raise HTTPException(
                status_code=404,
                detail=f"Data agent with ID {agent_id} not found"
            )
        
        # Find the target environment
        target_environment = next(
            (env for env in data_agent.environments if env.name == environment), 
            None
        )
        
        if not target_environment:
            raise HTTPException(
                status_code=404,
                detail=f"Environment '{environment}' not found for data agent '{data_agent.name}'"
            )
        
        # Get tables and relations for the specific environment
        tables = await prisma.dataagenttable.find_many(
            where={
                "dataAgentId": agent_id,
                "environmentId": target_environment.id
            },
            include={"columns": True}
        )
        
        relations = await prisma.dataagentrelation.find_many(
            where={
                "dataAgentId": agent_id,
                "environmentId": target_environment.id
            }
        )
        
        # Build the response
        agent_dict = {
            "id": data_agent.id,
            "name": data_agent.name,
            "description": data_agent.description,
            "status": data_agent.status,
            "connectionType": data_agent.connectionType,
            "userId": data_agent.userId,
            "createdAt": data_agent.createdAt,
            "updatedAt": data_agent.updatedAt,
            "environments": [target_environment.__dict__],  # Only the specific environment
            "tables": tables or [],
            "relations": relations or []
        }
        
        return agent_dict


@router.get("/{agent_id}", response_model=DataAgentWithTablesResponse)
async def get_data_agent(
    agent_id: str,
    admin_key: str = Depends(verify_admin_key),
    include_tables: bool = True,
    include_relations: bool = True
):
    """
    Get a specific data agent with optional nested data.
    Requires admin authentication.
    
    Args:
        agent_id: The ID of the data agent
        include_tables: Whether to include table data
        include_relations: Whether to include relationship data
    """
    async with get_prisma() as prisma:
        # Build include clause based on parameters
        include_clause = {}
        if include_tables:
            include_clause["tables"] = {
                "include": {"columns": True}
            }
        if include_relations:
            include_clause["relations"] = True
            
        data_agent = await prisma.dataagent.find_unique(
            where={"id": agent_id},
            include=include_clause
        )
        
        if not data_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data agent not found"
            )
            
        return data_agent


@router.post("/", response_model=DataAgentResponse)
async def create_data_agent(
    data_agent: DataAgentCreate,
    admin_key: str = Depends(verify_admin_key)
):
    """
    Create a new data agent.
    Requires admin authentication.
    """
    # For now, we'll use a dummy user ID - in a real implementation,
    # this would come from the authenticated user
    dummy_user_id = "system_user"
    
    async with get_prisma() as prisma:
        # Check if a user exists, if not create a system user
        user = await prisma.user.find_first(where={"role": "ADMIN"})
        if user:
            user_id = user.id
        else:
            # Create a system user for data agents
            user = await prisma.user.create(data={
                "email": "system@dataagents.local",
                "name": "System User",
                "role": "ADMIN",
                "password": "system_password_placeholder"
            })
            user_id = user.id
            
        new_agent = await prisma.dataagent.create(data={
            "name": data_agent.name,
            "description": data_agent.description,
            "connectionType": data_agent.connectionType,
            "userId": user_id,
            "status": "INACTIVE"  # Start as inactive until connection is tested
        })
        
        return new_agent


@router.put("/{agent_id}", response_model=DataAgentResponse)
async def update_data_agent(
    agent_id: str,
    update_data: DataAgentUpdate,
    admin_key: str = Depends(verify_admin_key)
):
    """
    Update an existing data agent.
    Requires admin authentication.
    """
    async with get_prisma() as prisma:
        # Check if data agent exists
        existing_agent = await prisma.dataagent.find_unique(where={"id": agent_id})
        if not existing_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data agent not found"
            )
            
        # Build update data
        update_dict = {}
        if update_data.name is not None:
            update_dict["name"] = update_data.name
        if update_data.description is not None:
            update_dict["description"] = update_data.description
        if update_data.connectionType is not None:
            update_dict["connectionType"] = update_data.connectionType
        if update_data.status is not None:
            update_dict["status"] = update_data.status
            
        updated_agent = await prisma.dataagent.update(
            where={"id": agent_id},
            data=update_dict
        )
        
        return updated_agent


@router.delete("/{agent_id}")
async def delete_data_agent(
    agent_id: str,
    admin_key: str = Depends(verify_admin_key)
):
    """
    Delete a data agent and all associated data.
    Requires admin authentication.
    """
    async with get_prisma() as prisma:
        # Check if data agent exists
        existing_agent = await prisma.dataagent.find_unique(where={"id": agent_id})
        if not existing_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data agent not found"
            )
            
        # Delete the data agent (cascade will handle related records)
        await prisma.dataagent.delete(where={"id": agent_id})
        
        return {"message": "Data agent deleted successfully"}


@router.get("/{agent_id}/tables", response_model=List[DataAgentTableResponse])
async def list_agent_tables(
    agent_id: str,
    admin_key: str = Depends(verify_admin_key),
    include_columns: bool = True
):
    """
    List all tables for a specific data agent.
    Requires admin authentication.
    """
    async with get_prisma() as prisma:
        # Verify data agent exists
        agent = await prisma.dataagent.find_unique(where={"id": agent_id})
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data agent not found"
            )
            
        include_clause = {"columns": True} if include_columns else {}
        
        tables = await prisma.dataagentTable.find_many(
            where={"dataAgentId": agent_id},
            include=include_clause,
            order={"tableName": "asc"}
        )
        
        return tables


@router.get("/{agent_id}/relations", response_model=List[DataAgentRelationResponse])
async def list_agent_relations(
    agent_id: str,
    admin_key: str = Depends(verify_admin_key),
    verified_only: bool = False
):
    """
    List all relationships for a specific data agent.
    Requires admin authentication.
    
    Args:
        agent_id: The ID of the data agent
        verified_only: If True, return only verified relationships
    """
    async with get_prisma() as prisma:
        # Verify data agent exists
        agent = await prisma.dataagent.find_unique(where={"id": agent_id})
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data agent not found"
            )
            
        where_clause = {"dataAgentId": agent_id}
        if verified_only:
            where_clause["isVerified"] = True
            
        relations = await prisma.dataagentRelation.find_many(
            where=where_clause,
            order={"confidence": "desc"}
        )
        
        return relations


@router.post("/{agent_id}/relations", response_model=DataAgentRelationResponse)
async def create_agent_relation(
    agent_id: str,
    relation_data: DataAgentRelationCreate,
    admin_key: str = Depends(verify_admin_key)
):
    """
    Create a new relationship for a data agent.
    Requires admin authentication.
    """
    async with get_prisma() as prisma:
        # Verify data agent exists
        agent = await prisma.dataagent.find_unique(where={"id": agent_id})
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data agent not found"
            )
            
        # Verify source and target tables exist and belong to this agent
        source_table = await prisma.dataagentTable.find_unique(
            where={"id": relation_data.sourceTableId}
        )
        target_table = await prisma.dataagentTable.find_unique(
            where={"id": relation_data.targetTableId}
        )
        
        if not source_table or source_table.dataAgentId != agent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid source table ID"
            )
            
        if not target_table or target_table.dataAgentId != agent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid target table ID"
            )
            
        # Create the relationship
        new_relation = await prisma.dataagentRelation.create(data={
            "dataAgentId": agent_id,
            "sourceTableId": relation_data.sourceTableId,
            "targetTableId": relation_data.targetTableId,
            "relationshipType": relation_data.relationshipType,
            "sourceColumn": relation_data.sourceColumn,
            "targetColumn": relation_data.targetColumn,
            "description": relation_data.description,
            "example": relation_data.example,
            "confidence": relation_data.confidence,
            "isVerified": relation_data.isVerified
        })
        
        return new_relation


@router.post("/{agent_id}/test-connection")
async def test_data_agent_connection(
    agent_id: str,
    admin_key: str = Depends(verify_admin_key)
):
    """
    Test the connection for a data agent.
    Requires admin authentication.
    """
    async with get_prisma() as prisma:
        # Get the data agent
        agent = await prisma.dataagent.find_unique(where={"id": agent_id})
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data agent not found"
            )
            
        # For now, we'll simulate a connection test
        # In a real implementation, this would test the actual database connection
        try:
            # Update status to CONNECTING
            await prisma.dataagent.update(
                where={"id": agent_id},
                data={
                    "status": "CONNECTING"
                }
            )
            
            # Simulate connection test based on connection type
            connection_type = agent.connectionType.lower()
            
            # This is a placeholder - real implementation would test actual connections
            if connection_type in ["postgres", "mysql", "sqlite", "bigquery", "databricks"]:
                # Simulate successful connection
                await prisma.dataagent.update(
                    where={"id": agent_id},
                    data={
                        "status": "ACTIVE"
                    }
                )
                
                return {
                    "status": "success",
                    "message": f"Successfully connected to {connection_type} data source",
                    "connectionType": connection_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                # Unsupported connection type
                await prisma.dataagent.update(
                    where={"id": agent_id},
                    data={"status": "ERROR"}
                )
                
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "message": f"Unsupported connection type: {connection_type}",
                        "connectionType": connection_type
                    }
                )
                
        except Exception as e:
            # Connection failed
            await prisma.dataagent.update(
                where={"id": agent_id},
                data={"status": "ERROR"}
            )
            
            logger.error(f"Connection test failed for agent {agent_id}: {str(e)}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"Connection test failed: {str(e)}",
                    "connectionType": agent.connectionType
                }
            )


@router.post("/{agent_id}/analyze", response_model=DataAgentAnalysisResponse)
async def analyze_data_agent(
    agent_id: str,
    analysis_request: DataAgentAnalysisRequest,
    admin_key: str = Depends(verify_admin_key)
):
    """
    Trigger AI analysis for a data agent.
    Requires admin authentication.
    
    This is a placeholder endpoint - real implementation would integrate with LLM services.
    """
    async with get_prisma() as prisma:
        # Verify data agent exists
        agent = await prisma.dataagent.find_unique(where={"id": agent_id})
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data agent not found"
            )
            
        # For now, we'll simulate the analysis process
        # In a real implementation, this would trigger actual AI analysis
        analysis_id = f"analysis_{agent_id}_{int(datetime.utcnow().timestamp())}"
        
        # Update the agent's analysis timestamp
        await prisma.dataagent.update(
            where={"id": agent_id},
            data={
                "status": "ACTIVE"  # Update status to show analysis is complete
            }
        )
        
        return DataAgentAnalysisResponse(
            analysisId=analysis_id,
            status="started",
            message=f"Analysis of type '{analysis_request.analysisType}' has been started for data agent",
            results=None
        )
