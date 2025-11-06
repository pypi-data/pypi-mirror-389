"""
vMCP (Virtual Model Context Protocol) models with proper inheritance and type safety.

This module contains all vMCP-related request and response models that extend
the base shared models to provide type-safe API endpoints.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
from enum import Enum

from vmcp.shared.models import (
    BaseResponse,
    PaginatedResponse,
    ErrorResponse,
    ServerInfo,
    CapabilitiesInfo,
    ConnectionStatus,
    TransportType,
    AuthType,
    AuthConfig,
    ToolInfo,
    ResourceInfo,
    PromptInfo,
)

from vmcp.shared.vmcp_content_models import (
    SystemPrompt,
    EnvironmentVariable,
    CustomPrompt,
    CustomTool,
    CustomResource,
    CustomResourceTemplate,
    CustomWidget,
    UploadedFile,
    VMCPConfigData,
)

from vmcp.shared.validators import (
    validate_server_id,
    validate_server_name,
    validate_description,
    validate_boolean_field,
    validate_optional_string,
    validate_required_string,
)

# ============================================================================
# BASE VMCP MODELS
# ============================================================================

class VMCPBaseRequest(BaseModel):
    """Base request model for vMCP operations."""
    
    # class Config:
    #     json_schema_extra = {
    #         "example": {
    #             "description": "Base vMCP request"
    #         }
    #     }

class VMCPBaseResponse(BaseResponse[Any]):
    """Base response model for vMCP operations."""
    
    # class Config:
    #     json_schema_extra = {
    #         "example": {
    #             "success": True,
    #             "message": "vMCP operation completed successfully",
    #             "data": {}
    #         }
    #     }

class VMCPConfigBase(ServerInfo):
    """Base vMCP configuration model."""
    
    user_id: str = Field(..., description="User ID who owns this vMCP")
    system_prompt: Optional[SystemPrompt] = Field(None, description="System prompt configuration")
    vmcp_config: Optional[VMCPConfigData] = Field(None, description="vMCP configuration")
    custom_prompts: List[CustomPrompt] = Field(default_factory=list, description="Custom prompts")
    custom_tools: List[CustomTool] = Field(default_factory=list, description="Custom tools")
    custom_context: List[str] = Field(default_factory=list, description="Custom context")
    custom_resources: List[CustomResource] = Field(default_factory=list, description="Custom resources")
    custom_resource_templates: List[CustomResourceTemplate] = Field(default_factory=list, description="Custom resource templates")
    custom_widgets: List[CustomWidget] = Field(default_factory=list, description="Custom widgets")
    environment_variables: List[EnvironmentVariable] = Field(default_factory=list, description="Environment variables")
    uploaded_files: List[UploadedFile] = Field(default_factory=list, description="Uploaded files")
    custom_resource_uris: List[str] = Field(default_factory=list, description="Custom resource URIs")
    
    @validator('user_id')
    def validate_user_id(cls, v):
        return validate_required_string(v, 'user_id', 255)
    
    @validator('description')
    def validate_description(cls, v):
        return validate_description(v)

# ============================================================================
# VMCP REQUEST MODELS
# ============================================================================

class VMCPCreateRequest(VMCPBaseRequest):
    """Request model for creating a vMCP."""
    
    name: str = Field(..., description="vMCP name")
    description: Optional[str] = Field(None, description="vMCP description")
    system_prompt: Optional[SystemPrompt] = Field(None, description="System prompt object with text and variables")
    vmcp_config: Optional[VMCPConfigData] = Field(None, description="vMCP configuration")
    custom_prompts: Optional[List[CustomPrompt]] = Field(default_factory=list, description="Custom prompts")
    custom_tools: Optional[List[CustomTool]] = Field(default_factory=list, description="Custom tools")
    custom_context: Optional[List[str]] = Field(default_factory=list, description="Custom context")
    custom_resources: Optional[List[CustomResource]] = Field(default_factory=list, description="Custom resources")
    custom_resource_templates: Optional[List[CustomResourceTemplate]] = Field(default_factory=list, description="Custom resource templates")
    custom_resource_uris: Optional[List[str]] = Field(default_factory=list, description="Custom resource URIs")
    environment_variables: Optional[List[EnvironmentVariable]] = Field(default_factory=list, description="Environment variables")
    uploaded_files: Optional[List[UploadedFile]] = Field(default_factory=list, description="Uploaded files")
    
    class Config:
        extra = "allow"  # Allow extra fields for backward compatibility
    
    @validator('name')
    def validate_name(cls, v):
        return validate_server_name(v)
    
    @validator('description')
    def validate_description(cls, v):
        return validate_description(v)
    
    # class Config:
    #     json_schema_extra = {
    #         "example": {
    #             "name": "My vMCP",
    #             "description": "A sample vMCP configuration",
    #             "system_prompt": {
    #                 "text": "You are a helpful assistant",
    #                 "variables": []
    #             },
    #             "vmcp_config": {
    #                 "selected_servers": []
    #             },
    #             "custom_prompts": [],
    #             "custom_tools": [],
    #             "environment_variables": []
    #         }
    #     }

class VMCPUdateRequest(VMCPBaseRequest):
    """Request model for updating a vMCP."""
    
    name: Optional[str] = Field(None, description="vMCP name")
    description: Optional[str] = Field(None, description="vMCP description")
    system_prompt: Optional[SystemPrompt] = Field(None, description="System prompt object with text and variables")
    vmcp_config: Optional[VMCPConfigData] = Field(None, description="vMCP configuration")
    custom_prompts: Optional[List[CustomPrompt]] = Field(default_factory=list, description="Custom prompts")
    custom_tools: Optional[List[CustomTool]] = Field(default_factory=list, description="Custom tools")
    custom_context: Optional[List[str]] = Field(default_factory=list, description="Custom context")
    custom_resources: Optional[List[CustomResource]] = Field(default_factory=list, description="Custom resources")
    custom_resource_templates: Optional[List[CustomResourceTemplate]] = Field(default_factory=list, description="Custom resource templates")
    custom_resource_uris: Optional[List[str]] = Field(default_factory=list, description="Custom resource URIs")
    environment_variables: Optional[List[EnvironmentVariable]] = Field(default_factory=list, description="Environment variables")
    uploaded_files: Optional[List[UploadedFile]] = Field(default_factory=list, description="Uploaded files")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata")
    
    class Config:
        extra = "allow"  # Allow extra fields for backward compatibility
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            return validate_server_name(v)
        return v
    
    @validator('description')
    def validate_description(cls, v):
        return validate_description(v)

class VMCPToolCallRequest(VMCPBaseRequest):
    """Request model for calling a vMCP tool."""
    
    tool_name: str = Field(..., description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    
    @validator('tool_name')
    def validate_tool_name(cls, v):
        return validate_server_name(v)  # Reuse server name validation for tool names
    
    class Config:
        json_schema_extra = {
            "example": {
                "tool_name": "search_tool",
                "arguments": {
                    "query": "search term",
                    "limit": 10
                }
            }
        }

class VMCPResourceRequest(VMCPBaseRequest):
    """Request model for reading a vMCP resource."""
    
    uri: str = Field(..., description="Resource URI to read")
    
    @validator('uri')
    def validate_uri(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("URI must be a non-empty string")
        if len(v) > 2000:
            raise ValueError("URI must be less than 2000 characters")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "uri": "file:///path/to/resource.txt"
            }
        }

class VMCPResourceTemplateRequest(VMCPBaseRequest):
    """Request model for using a vMCP resource template."""
    
    template_name: str = Field(..., description="Name of the resource template")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Template parameters")
    
    @validator('template_name')
    def validate_template_name(cls, v):
        return validate_server_name(v)  # Reuse server name validation for template names
    
    class Config:
        json_schema_extra = {
            "example": {
                "template_name": "file_template",
                "parameters": {
                    "path": "/path/to/file",
                    "format": "text"
                }
            }
        }

class VMCPPromptRequest(VMCPBaseRequest):
    """Request model for getting a vMCP prompt."""
    
    prompt_id: str = Field(..., description="ID of the prompt to get")
    arguments: Optional[Dict[str, Any]] = Field(None, description="Prompt arguments")
    
    @validator('prompt_id')
    def validate_prompt_id(cls, v):
        return validate_server_name(v)  # Reuse server name validation for prompt IDs
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt_id": "summarize_prompt",
                "arguments": {
                    "text": "Text to summarize",
                    "max_length": 100
                }
            }
        }

class VMCPEnvironmentVariablesRequest(VMCPBaseRequest):
    """Request model for updating vMCP environment variables."""
    
    environment_variables: List[Dict[str, Any]] = Field(..., description="List of environment variables to save")
    
    @validator('environment_variables')
    def validate_environment_variables(cls, v):
        if not isinstance(v, list):
            raise ValueError("Environment variables must be a list")
        
        for i, env_var in enumerate(v):
            if not isinstance(env_var, dict):
                raise ValueError(f"Environment variable {i} must be a dictionary")
            
            if 'name' not in env_var or 'value' not in env_var:
                raise ValueError(f"Environment variable {i} must have 'name' and 'value' fields")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "environment_variables": [
                    {
                        "name": "API_KEY",
                        "value": "secret_key",
                        "description": "API key for external service"
                    }
                ]
            }
        }

class VMCPShareState(str, Enum):
    """Enum for vMCP sharing states."""
    
    PUBLIC = "public"
    SHARED = "shared"
    PRIVATE = "private"

class VMCPShareRequest(VMCPBaseRequest):
    """Request model for sharing a vMCP."""
    
    vmcp_id: str = Field(..., description="vMCP ID to share")
    state: VMCPShareState = Field(..., description="Sharing state")
    tags: Optional[List[str]] = Field(None, description="Tags for the shared vMCP")
    
    @validator('vmcp_id')
    def validate_vmcp_id(cls, v):
        return validate_server_id(v)
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("Tags must be a list")
            
            for i, tag in enumerate(v):
                if not isinstance(tag, str):
                    raise ValueError(f"Tag {i} must be a string")
                if len(tag) > 50:
                    raise ValueError(f"Tag {i} must be less than 50 characters")
        
        return v
    
    class Config:
        extra = "forbid"  # Reject any extra fields
        json_schema_extra = {
            "example": {
                "vmcp_id": "vmcp_123",
                "state": "public",
                "tags": ["productivity", "ai"]
            }
        }

class VMCPInstallRequest(VMCPBaseRequest):
    """Request model for installing a public vMCP."""
    
    public_vmcp_id: str = Field(..., description="Public vMCP ID to install")
    
    @validator('public_vmcp_id')
    def validate_public_vmcp_id(cls, v):
        return validate_server_id(v)
    
    class Config:
        json_schema_extra = {
            "example": {
                "public_vmcp_id": "public_vmcp_123"
            }
        }

# ============================================================================
# VMCP RESPONSE MODELS
# ============================================================================

class VMCPInfo(VMCPConfigBase):
    """Response model for vMCP information."""
    
    total_tools: Optional[int] = Field(None, description="Total number of tools")
    total_resources: Optional[int] = Field(None, description="Total number of resources")
    total_resource_templates: Optional[int] = Field(None, description="Total number of resource templates")
    total_prompts: Optional[int] = Field(None, description="Total number of prompts")
    creator_id: Optional[str] = Field(None, description="Creator user ID")
    creator_username: Optional[str] = Field(None, description="Creator username")
    
    # Sharing fields
    is_public: bool = Field(False, description="Whether vMCP is public")
    public_tags: List[str] = Field(default_factory=list, description="Public tags")
    public_at: Optional[str] = Field(None, description="When vMCP was made public")
    is_wellknown: bool = Field(False, description="Whether vMCP is well-known")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "vmcp_123",
                "name": "My vMCP",
                "description": "A sample vMCP",
                "status": "active",
                "user_id": "user_123",
                "total_tools": 5,
                "total_resources": 3,
                "total_prompts": 2,
                "is_public": False,
                "public_tags": [],
                "metadata": {}
            }
        }

class VMCPCreateResponse(BaseModel):
    """Response model for vMCP creation matching original router structure."""
    
    success: bool = Field(True, description="Whether the operation was successful")
    vMCP: VMCPInfo = Field(..., description="Created vMCP information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "vMCP": {
                    "id": "vmcp_123",
                    "name": "My vMCP",
                    "status": "active",
                    "user_id": "user_123"
                }
            }
        }

class VMCPUpdateResponse(BaseModel):
    """Response model for vMCP update matching original router structure."""
    
    success: bool = Field(True, description="Whether the operation was successful")
    vMCP: Dict[str, Any] = Field(..., description="Updated vMCP information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "vMCP": {
                    "id": "vmcp_123",
                    "name": "My vMCP",
                    "status": "active",
                    "user_id": "user_123"
                }
            }
        }

class VMCPDeleteResponse(VMCPBaseResponse):
    """Response model for vMCP deletion."""
    
    data: Dict[str, str] = Field(..., description="Deletion operation details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "vMCP 'My vMCP' deleted successfully",
                "data": {
                    "vmcp_id": "vmcp_123",
                    "vmcp_name": "My vMCP"
                }
            }
        }

class VMCPDetailsResponse(BaseModel):
    """Response model for vMCP details matching original router structure."""
    
    # Since the original router returns vmcp_config.to_dict(), we need to be flexible
    # We'll use a generic dict structure that can accommodate all fields
    id: str = Field(..., description="vMCP ID")
    name: str = Field(..., description="vMCP name")
    user_id: int = Field(..., description="User ID")
    description: Optional[str] = Field(None, description="vMCP description")
    system_prompt: Optional[SystemPrompt] = Field(None, description="System prompt")
    vmcp_config: VMCPConfigData = Field(default_factory=VMCPConfigData, description="vMCP configuration")
    custom_prompts: List[CustomPrompt] = Field(default_factory=list, description="Custom prompts")
    custom_tools: List[CustomTool] = Field(default_factory=list, description="Custom tools")
    custom_context: List[str] = Field(default_factory=list, description="Custom context")
    custom_resources: List[CustomResource] = Field(default_factory=list, description="Custom resources")
    custom_resource_templates: List[CustomResourceTemplate] = Field(default_factory=list, description="Custom resource templates")
    custom_widgets: List[CustomWidget] = Field(default_factory=list, description="Custom widgets")
    uploaded_files: List[UploadedFile] = Field(default_factory=list, description="Uploaded files")
    custom_resource_uris: List[str] = Field(default_factory=list, description="Custom resource URIs")
    total_tools: Optional[int] = Field(None, description="Total number of tools")
    total_resources: Optional[int] = Field(None, description="Total number of resources")
    total_resource_templates: Optional[int] = Field(None, description="Total number of resource templates")
    total_prompts: Optional[int] = Field(None, description="Total number of prompts")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    creator_id: Optional[int] = Field(None, description="Creator ID")
    creator_username: Optional[Union[str, int]] = Field(None, description="Creator username")
    is_public: bool = Field(False, description="Whether vMCP is public")
    public_tags: List[str] = Field(default_factory=list, description="Public tags")
    public_at: Optional[str] = Field(None, description="When vMCP was made public")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    environment_variables: List[EnvironmentVariable] = Field(default_factory=list, description="Environment variables")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "vmcp_123",
                "name": "My vMCP",
                "user_id": 1,
                "description": "A sample vMCP",
                "vmcp_config": {},
                "custom_prompts": [],
                "custom_tools": [],
                "total_tools": 0,
                "total_resources": 0,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00",
                "is_public": False,
                "metadata": {}
            }
        }

class VMCPListData(BaseModel):
    """Data structure for vMCP list response matching original router structure."""
    private: List[Dict[str, Any]] = Field(..., description="List of private vMCPs")
    public: List[Dict[str, Any]] = Field(default_factory=list, description="List of public vMCPs")

class VMCPListResponse(BaseModel):
    """Response model for vMCP list matching original router structure."""
    
    private: List[Dict[str, Any]] = Field(..., description="List of private vMCPs")
    public: List[Dict[str, Any]] = Field(default_factory=list, description="List of public vMCPs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "private": [
                    {
                        "id": "vmcp_123",
                        "name": "My vMCP",
                        "status": "active",
                        "user_id": "user_123"
                    }
                ],
                "public": []
            }
        }

class VMCPCapabilitiesResponse(VMCPBaseResponse):
    """Response model for vMCP capabilities."""
    
    data: Dict[str, Any] = Field(..., description="vMCP capabilities details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "vMCP capabilities retrieved successfully",
                "data": {
                    "tools": [
                        {
                            "name": "search_tool",
                            "description": "Search for information",
                            "server": "server1"
                        }
                    ],
                    "resources": [
                        {
                            "uri": "file:///path/to/resource",
                            "description": "A file resource",
                            "server": "server1"
                        }
                    ],
                    "prompts": [
                        {
                            "name": "summarize_prompt",
                            "description": "Summarize text content",
                            "server": "server1"
                        }
                    ],
                    "total_tools": 1,
                    "total_resources": 1,
                    "total_prompts": 1
                }
            }
        }

class VMCPRefreshResponse(VMCPBaseResponse):
    """Response model for vMCP refresh operations."""
    
    data: Dict[str, Any] = Field(..., description="Refresh operation details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "vMCP refreshed successfully",
                "data": {
                    "vmcp_id": "vmcp_123",
                    "servers_updated": 2,
                    "capabilities_updated": True
                }
            }
        }

class VMCPToolCallResponse(VMCPBaseResponse):
    """Response model for vMCP tool call execution."""
    
    data: Dict[str, Any] = Field(..., description="Tool call execution details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Tool executed successfully",
                "data": {
                    "vmcp_id": "vmcp_123",
                    "tool": "search_tool",
                    "result": "Search results here"
                }
            }
        }

class VMCPResourceResponse(VMCPBaseResponse):
    """Response model for vMCP resource read operations."""
    
    data: Dict[str, Any] = Field(..., description="Resource read details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Resource read successfully",
                "data": {
                    "vmcp_id": "vmcp_123",
                    "uri": "file:///path/to/resource",
                    "contents": "Resource content here"
                }
            }
        }

class VMCPResourceTemplateResponse(VMCPBaseResponse):
    """Response model for vMCP resource template operations."""
    
    data: Dict[str, Any] = Field(..., description="Resource template operation details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Resource template processed successfully",
                "data": {
                    "vmcp_id": "vmcp_123",
                    "template_name": "file_template",
                    "result": "Processed template result"
                }
            }
        }

class VMCPPromptResponse(VMCPBaseResponse):
    """Response model for vMCP prompt operations."""
    
    data: Dict[str, Any] = Field(..., description="Prompt operation details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Prompt retrieved successfully",
                "data": {
                    "vmcp_id": "vmcp_123",
                    "prompt_id": "summarize_prompt",
                    "messages": ["System message", "User message"]
                }
            }
        }

class VMCPEnvironmentVariablesResponse(VMCPBaseResponse):
    """Response model for vMCP environment variables operations."""
    
    data: Dict[str, Any] = Field(..., description="Environment variables operation details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Environment variables updated successfully",
                "data": {
                    "vmcp_id": "vmcp_123",
                    "variables_count": 3,
                    "variables": [
                        {
                            "name": "API_KEY",
                            "value": "secret_key",
                            "description": "API key for external service"
                        }
                    ]
                }
            }
        }

class VMCPShareResponse(VMCPBaseResponse):
    """Response model for vMCP sharing operations."""
    
    data: Dict[str, Any] = Field(..., description="Sharing operation details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "vMCP shared successfully",
                "data": {
                    "vmcp_id": "vmcp_123",
                    "state": "public",
                    "tags": ["productivity", "ai"],
                    "public_url": "https://example.com/public/vmcp_123"
                }
            }
        }

class VMCPInstallResponse(VMCPBaseResponse):
    """Response model for vMCP installation operations."""
    
    data: VMCPInfo = Field(..., description="Installed vMCP information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "vMCP installed successfully",
                "data": {
                    "id": "vmcp_123",
                    "name": "Installed vMCP",
                    "status": "active",
                    "user_id": "user_123"
                }
            }
        }

# ============================================================================
# STATS MODELS
# ============================================================================

class StatsFilterRequest(BaseModel):
    """Request model for filtering stats."""
    
    agent_name: Optional[str] = Field(None, description="Filter by agent name")
    vmcp_name: Optional[str] = Field(None, description="Filter by vMCP name")
    method: Optional[str] = Field(None, description="Filter by method name")
    search: Optional[str] = Field(None, description="Search across all fields")
    page: int = Field(1, description="Page number for pagination")
    limit: int = Field(50, description="Number of items per page")
    
    @validator('page')
    def validate_page(cls, v):
        if v < 1:
            raise ValueError("Page must be at least 1")
        return v
    
    @validator('limit')
    def validate_limit(cls, v):
        if v < 1 or v > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "My Agent",
                "vmcp_name": "My vMCP",
                "method": "tool_call",
                "search": "search term",
                "page": 1,
                "limit": 50
            }
        }

class LogEntry(BaseModel):
    """Model for log entry."""
    
    timestamp: str = Field(..., description="Log timestamp")
    method: str = Field(..., description="Method name")
    agent_name: str = Field(..., description="Agent name")
    agent_id: str = Field(..., description="Agent ID")
    user_id: int = Field(..., description="User ID")
    client_id: str = Field(..., description="Client ID")
    operation_id: str = Field(..., description="Operation ID")
    mcp_server: Optional[str] = Field(None, description="MCP server name")
    mcp_method: Optional[str] = Field(None, description="MCP method name")
    original_name: Optional[str] = Field(None, description="Original name")
    arguments: Optional[Any] = Field(None, description="Method arguments")
    result: Optional[Any] = Field(None, description="Method result")
    vmcp_id: Optional[str] = Field(None, description="vMCP ID")
    vmcp_name: Optional[str] = Field(None, description="vMCP name")
    total_tools: Optional[int] = Field(None, description="Total tools count")
    total_resources: Optional[int] = Field(None, description="Total resources count")
    total_resource_templates: Optional[int] = Field(None, description="Total resource templates count")
    total_prompts: Optional[int] = Field(None, description="Total prompts count")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-01T00:00:00Z",
                "method": "tool_call",
                "agent_name": "My Agent",
                "agent_id": "agent_123",
                "user_id": 1,
                "client_id": "client_123",
                "operation_id": "op_123",
                "mcp_server": "server1",
                "mcp_method": "call_tool",
                "vmcp_id": "vmcp_123",
                "vmcp_name": "My vMCP",
                "total_tools": 5
            }
        }

class StatsResponse(BaseModel):
    """Response model for stats."""
    
    logs: List[LogEntry] = Field(..., description="List of log entries")
    pagination: Dict[str, Any] = Field(..., description="Pagination metadata")
    stats: Dict[str, Any] = Field(..., description="Statistics summary")
    filter_options: Dict[str, List[str]] = Field(..., description="Available filter options")
    
    class Config:
        json_schema_extra = {
            "example": {
                "logs": [],
                "pagination": {
                    "page": 1,
                    "limit": 50,
                    "total": 0,
                    "pages": 0
                },
                "stats": {
                    "total_logs": 0,
                    "total_agents": 0,
                    "total_vmcps": 0
                },
                "filter_options": {
                    "agent_names": [],
                    "vmcp_names": [],
                    "methods": []
                }
            }
        }

class StatsSummary(BaseModel):
    """Model for stats summary."""
    
    total_logs: int = Field(..., description="Total number of logs")
    total_agents: int = Field(..., description="Total number of agents")
    total_vmcps: int = Field(..., description="Total number of vMCPs")
    total_tool_calls: int = Field(..., description="Total number of tool calls")
    total_resource_calls: int = Field(..., description="Total number of resource calls")
    total_prompt_calls: int = Field(..., description="Total number of prompt calls")
    unique_methods: List[str] = Field(..., description="List of unique methods")
    agent_breakdown: Dict[str, int] = Field(..., description="Agent breakdown")
    vmcp_breakdown: Dict[str, int] = Field(..., description="vMCP breakdown")
    method_breakdown: Dict[str, int] = Field(..., description="Method breakdown")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_logs": 1000,
                "total_agents": 10,
                "total_vmcps": 5,
                "total_tool_calls": 500,
                "total_resource_calls": 200,
                "total_prompt_calls": 100,
                "unique_methods": ["tool_call", "resource_read", "prompt_get"],
                "agent_breakdown": {"Agent1": 300, "Agent2": 200},
                "vmcp_breakdown": {"vMCP1": 400, "vMCP2": 300},
                "method_breakdown": {"tool_call": 500, "resource_read": 200}
            }
        }

# ============================================================================
# LEGACY COMPATIBILITY
# ============================================================================

# Keep the old dataclass for backward compatibility (will be deprecated)
from dataclasses import dataclass, field, asdict
from copy import deepcopy

@dataclass
class PublicVMCPInfo(BaseModel):
    """Public vMCP information for sharing."""
    
    creator_id: str = Field(..., description="Creator user ID")
    creator_username: str = Field(..., description="Creator username")
    install_count: int = Field(0, description="Number of installations")
    rating: Optional[float] = Field(None, description="Average rating")
    rating_count: int = Field(0, description="Number of ratings")
    
    class Config:
        json_schema_extra = {
            "example": {
                "creator_id": "user_123",
                "creator_username": "john_doe",
                "install_count": 50,
                "rating": 4.5,
                "rating_count": 20
            }
        }

@dataclass
class VMCPRegistryConfig:
    """vMCP Registry configuration dataclass - DEPRECATED, use VMCPInfo instead."""
    
    id: str
    name: str
    user_id: str
    description: Optional[str] = None
    vmcp_config: Optional[Dict[str, Any]] = field(default_factory=dict)
    environment_variables: Optional[List[Dict[str, Any]]] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    creator_id: Optional[str] = None
    creator_username: Optional[str] = None
    total_tools: Optional[int] = None
    total_resources: Optional[int] = None
    total_resource_templates: Optional[int] = None
    total_prompts: Optional[int] = None
    public_info: Optional[PublicVMCPInfo] = None
    is_public: bool = False
    public_tags: List[str] = field(default_factory=list)
    public_at: Optional[str] = None
    is_wellknown: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        
        if self.public_info:
            data['public_info'] = asdict(self.public_info)
        
        if self.vmcp_config and 'selected_servers' in self.vmcp_config:
            selected_servers = self.vmcp_config['selected_servers']
            if isinstance(selected_servers, list):
                serialized_servers = []
                for server in selected_servers:
                    if hasattr(server, 'to_dict'):
                        serialized_servers.append(server.to_dict())
                    else:
                        serialized_servers.append(server)
                data['vmcp_config']['selected_servers'] = serialized_servers
        
        return data

@dataclass
class VMCPConfig:
    """vMCP configuration dataclass - DEPRECATED, use VMCPInfo instead."""
    
    id: str
    name: str
    user_id: str
    description: Optional[str] = None
    system_prompt: Optional[Dict[str, Any]] = None
    vmcp_config: Optional[Dict[str, Any]] = field(default_factory=dict)
    custom_prompts: List[Dict[str, Any]] = field(default_factory=list)
    custom_tools: List[Dict[str, Any]] = field(default_factory=list)
    custom_context: List[str] = field(default_factory=list)
    custom_resources: List[Dict[str, Any]] = field(default_factory=list)
    custom_resource_templates: List[Dict[str, Any]] = field(default_factory=list)
    custom_widgets: List[Dict[str, Any]] = field(default_factory=list)
    environment_variables: List[Dict[str, Any]] = field(default_factory=list)
    uploaded_files: List[Dict[str, Any]] = field(default_factory=list)
    custom_resource_uris: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    creator_id: Optional[str] = None
    creator_username: Optional[str] = None
    total_tools: Optional[int] = None
    total_resources: Optional[int] = None
    total_resource_templates: Optional[int] = None
    total_prompts: Optional[int] = None
    public_info: Optional[PublicVMCPInfo] = None
    is_public: bool = False
    public_tags: List[str] = field(default_factory=list)
    public_at: Optional[str] = None
    is_wellknown: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set default timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VMCPConfig':
        """Create VMCPConfig from dictionary."""
        processed_data = data.copy()
        
        if 'created_at' in processed_data and isinstance(processed_data['created_at'], str):
            try:
                processed_data['created_at'] = datetime.fromisoformat(processed_data['created_at'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                processed_data['created_at'] = None
        
        if 'updated_at' in processed_data and isinstance(processed_data['updated_at'], str):
            try:
                processed_data['updated_at'] = datetime.fromisoformat(processed_data['updated_at'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                processed_data['updated_at'] = None
        
        return cls(**processed_data)
    
    def to_dict(self, include_environment_variables: bool = True) -> Dict[str, Any]:
        """Convert VMCPConfig to dictionary for JSON serialization."""
        vmcp_dict = {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "vmcp_config": self.vmcp_config,
            "custom_prompts": self.custom_prompts,
            "custom_tools": self.custom_tools,
            "custom_context": self.custom_context,
            "custom_resources": self.custom_resources,
            "custom_resource_templates": self.custom_resource_templates,
            "custom_widgets": self.custom_widgets,
            "uploaded_files": self.uploaded_files,
            "custom_resource_uris": self.custom_resource_uris,
            "total_tools": self.total_tools,
            "total_resources": self.total_resources,
            "total_resource_templates": self.total_resource_templates,
            "total_prompts": self.total_prompts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "creator_id": self.creator_id,
            "creator_username": self.creator_username,
            "is_public": self.is_public,
            "public_tags": self.public_tags,
            "public_at": self.public_at,
            "metadata": self.metadata
        }
        
        if include_environment_variables:
            vmcp_dict["environment_variables"] = self.environment_variables
        
        return vmcp_dict
    
    def to_vmcp_registry_config(self) -> VMCPRegistryConfig:
        """Convert to VMCPRegistryConfig for registry operations."""
        registry_vmcp_config = deepcopy(self.vmcp_config) if self.vmcp_config else {}
        
        if 'selected_servers' in registry_vmcp_config:
            from vmcp.mcps.models import MCPRegistryConfig
            selected_servers = registry_vmcp_config['selected_servers']
            if isinstance(selected_servers, list):
                registry_servers = []
                for server in selected_servers:
                    if isinstance(server, dict):
                        from vmcp.mcps.models import MCPServerConfig
                        loaded_server = MCPServerConfig.from_dict(server)
                        registry_servers.append(loaded_server.to_mcp_registry_config())
                    else:
                        registry_servers.append(server)
                registry_vmcp_config['selected_servers'] = registry_servers
        
        return VMCPRegistryConfig(
            id=self.id,
            name=self.name,
            user_id=self.user_id,
            description=self.description,
            vmcp_config=registry_vmcp_config,
            environment_variables=self.environment_variables,
            created_at=self.created_at,
            updated_at=self.updated_at,
            creator_id=self.creator_id,
            creator_username=self.creator_username,
            total_tools=self.total_tools,
            total_resources=self.total_resources,
            total_resource_templates=self.total_resource_templates,
            total_prompts=self.total_prompts,
            public_info=self.public_info,
            is_public=self.is_public,
            public_tags=self.public_tags,
            public_at=self.public_at,
            is_wellknown=self.is_wellknown,
            metadata=self.metadata,
        )

class VMCPAddServerResponse(BaseModel):
    """Response model for adding server to vMCP matching original router structure."""
    
    success: bool = Field(True, description="Whether the operation was successful")
    message: str = Field(..., description="Success message")
    vmcp_config: Dict[str, Any] = Field(..., description="Updated vMCP configuration")
    server: Dict[str, Any] = Field(..., description="Added server information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Server 'test-server' added to vMCP successfully",
                "vmcp_config": {
                    "id": "vmcp_123",
                    "name": "My vMCP"
                },
                "server": {
                    "server_id": "server_123",
                    "name": "test-server"
                }
            }
        }

class VMCPRemoveServerResponse(BaseModel):
    """Response model for removing server from vMCP matching original router structure."""
    
    success: bool = Field(True, description="Whether the operation was successful")
    message: str = Field(..., description="Success message")
    vmcp_config: Dict[str, Any] = Field(..., description="Updated vMCP configuration")
    server: Optional[Dict[str, Any]] = Field(None, description="Removed server information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Server 'test-server' removed from vMCP successfully",
                "vmcp_config": {
                    "id": "vmcp_123",
                    "name": "My vMCP"
                },
                "server": None
            }
        }
