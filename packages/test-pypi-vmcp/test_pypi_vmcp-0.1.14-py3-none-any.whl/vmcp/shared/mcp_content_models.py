"""
MCP-specific content models for type safety.

This module contains Pydantic models for MCP-specific data structures
that were previously represented as generic Dict/List[Dict] types.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
from datetime import datetime

class _PermissiveBaseModel(BaseModel):
    """Base class with extra="allow" for backward compatibility."""
    class Config:
        extra = "allow"

# ============================================================================
# MCP CAPABILITIES MODELS
# ============================================================================

class MCPCapabilities(_PermissiveBaseModel):
    """MCP server capabilities information."""
    
    tools: bool = Field(False, description="Whether server supports tools")
    resources: bool = Field(False, description="Whether server supports resources")
    prompts: bool = Field(False, description="Whether server supports prompts")
    tools_count: Optional[int] = Field(None, description="Number of available tools")
    resources_count: Optional[int] = Field(None, description="Number of available resources")
    prompts_count: Optional[int] = Field(None, description="Number of available prompts")
    logging: Optional[bool] = Field(None, description="Whether server supports logging")
    experimental: Optional[Dict[str, Any]] = Field(None, description="Experimental capabilities")

# ============================================================================
# MCP TOOL MODELS
# ============================================================================

class MCPToolArgument(_PermissiveBaseModel):
    """MCP tool argument definition."""
    
    name: str = Field(..., description="Argument name")
    type: str = Field(..., description="Argument type")
    description: Optional[str] = Field(None, description="Argument description")
    required: bool = Field(False, description="Whether argument is required")
    default: Optional[Any] = Field(None, description="Default value")

class MCPToolInfo(_PermissiveBaseModel):
    """MCP tool information."""
    
    name: str = Field(..., description="Tool name")
    description: Optional[str] = Field(None, description="Tool description")
    inputSchema: Optional[Dict[str, Any]] = Field(None, description="Input schema")
    outputSchema: Optional[Dict[str, Any]] = Field(None, description="Output schema")
    server: Optional[str] = Field(None, description="Server that provides this tool")
    server_id: Optional[str] = Field(None, description="Server ID")

class MCPToolCallResult(_PermissiveBaseModel):
    """MCP tool call execution result."""
    
    tool_name: str = Field(..., description="Name of the tool that was called")
    server: Optional[str] = Field(None, description="Server that executed the tool")
    server_id: Optional[str] = Field(None, description="Server ID")
    result: Any = Field(..., description="Tool execution result")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")

# ============================================================================
# MCP RESOURCE MODELS
# ============================================================================

class MCPResourceInfo(_PermissiveBaseModel):
    """MCP resource information."""
    
    uri: str = Field(..., description="Resource URI")
    name: Optional[str] = Field(None, description="Resource name")
    description: Optional[str] = Field(None, description="Resource description")
    mimeType: Optional[str] = Field(None, description="MIME type")
    size: Optional[int] = Field(None, description="Resource size in bytes")
    server: Optional[str] = Field(None, description="Server that provides this resource")
    server_id: Optional[str] = Field(None, description="Server ID")

class MCPResourceContent(_PermissiveBaseModel):
    """MCP resource content."""
    
    uri: str = Field(..., description="Resource URI")
    server: Optional[str] = Field(None, description="Server that provided the resource")
    server_id: Optional[str] = Field(None, description="Server ID")
    contents: Any = Field(..., description="Resource content")
    mimeType: Optional[str] = Field(None, description="MIME type of the content")
    size: Optional[int] = Field(None, description="Content size in bytes")

# ============================================================================
# MCP PROMPT MODELS
# ============================================================================

class MCPPromptArgument(_PermissiveBaseModel):
    """MCP prompt argument definition."""
    
    name: str = Field(..., description="Argument name")
    description: Optional[str] = Field(None, description="Argument description")
    required: bool = Field(False, description="Whether argument is required")

class MCPPromptInfo(_PermissiveBaseModel):
    """MCP prompt information."""
    
    name: str = Field(..., description="Prompt name")
    description: Optional[str] = Field(None, description="Prompt description")
    arguments: Optional[List[MCPPromptArgument]] = Field(None, description="Prompt arguments")
    server: Optional[str] = Field(None, description="Server that provides this prompt")
    server_id: Optional[str] = Field(None, description="Server ID")

class MCPPromptResult(_PermissiveBaseModel):
    """MCP prompt execution result."""
    
    prompt_name: str = Field(..., description="Name of the prompt that was executed")
    server: Optional[str] = Field(None, description="Server that executed the prompt")
    server_id: Optional[str] = Field(None, description="Server ID")
    messages: List[Dict[str, Any]] = Field(..., description="Generated messages")
    error: Optional[str] = Field(None, description="Error message if execution failed")

# ============================================================================
# MCP SERVER STATUS MODELS
# ============================================================================

class MCPServerStatus(_PermissiveBaseModel):
    """MCP server status information."""
    
    server_id: str = Field(..., description="Server ID")
    name: str = Field(..., description="Server name")
    status: str = Field(..., description="Connection status")
    last_updated: Optional[datetime] = Field(None, description="Last status update")
    last_connected: Optional[datetime] = Field(None, description="Last connection time")
    last_error: Optional[str] = Field(None, description="Last error message")
    requires_auth: bool = Field(False, description="Whether server requires authentication")

class MCPConnectionInfo(_PermissiveBaseModel):
    """MCP connection operation details."""
    
    server_id: str = Field(..., description="Server ID")
    server_name: str = Field(..., description="Server name")
    status: str = Field(..., description="Connection status")
    requires_auth: bool = Field(False, description="Whether server requires authentication")
    auth_url: Optional[str] = Field(None, description="Authentication URL if required")
    error: Optional[str] = Field(None, description="Error message if connection failed")

class MCPPingInfo(_PermissiveBaseModel):
    """MCP ping operation details."""
    
    server: str = Field(..., description="Server name or ID")
    server_id: Optional[str] = Field(None, description="Server ID")
    alive: bool = Field(..., description="Whether server is alive")
    timestamp: datetime = Field(..., description="Ping timestamp")
    response_time: Optional[float] = Field(None, description="Response time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if ping failed")

# ============================================================================
# MCP STATISTICS MODELS
# ============================================================================

class MCPServerStats(_PermissiveBaseModel):
    """MCP server statistics."""
    
    total: int = Field(0, description="Total number of servers")
    connected: int = Field(0, description="Number of connected servers")
    disconnected: int = Field(0, description="Number of disconnected servers")
    auth_required: int = Field(0, description="Number of servers requiring authentication")
    errors: int = Field(0, description="Number of servers with errors")

class MCPCapabilitiesStats(_PermissiveBaseModel):
    """MCP capabilities statistics."""
    
    tools: int = Field(0, description="Total number of tools")
    resources: int = Field(0, description="Total number of resources")
    prompts: int = Field(0, description="Total number of prompts")

class MCPSystemStats(_PermissiveBaseModel):
    """MCP system statistics."""
    
    servers: MCPServerStats = Field(..., description="Server statistics")
    capabilities: MCPCapabilitiesStats = Field(..., description="Capabilities statistics")

# ============================================================================
# MCP REGISTRY MODELS
# ============================================================================

class MCPRegistryConfig(_PermissiveBaseModel):
    """MCP registry configuration."""
    
    name: Optional[str] = Field(None, description="Server name")
    transport_type: Optional[str] = Field(None, description="Transport type")
    description: Optional[str] = Field(None, description="Server description")
    url: Optional[str] = Field(None, description="Server URL")
    command: Optional[str] = Field(None, description="Command for stdio servers")
    args: Optional[List[str]] = Field(None, description="Command arguments")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers")

class MCPServerConfig(_PermissiveBaseModel):
    """MCP server configuration."""
    
    name: Optional[str] = Field(None, description="Server name")
    transport_type: Optional[str] = Field(None, description="Transport type")
    description: Optional[str] = Field(None, description="Server description")
    url: Optional[str] = Field(None, description="Server URL")
    command: Optional[str] = Field(None, description="Command for stdio servers")
    args: Optional[List[str]] = Field(None, description="Command arguments")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers")
    auth: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")

class MCPRegistryStats(_PermissiveBaseModel):
    """MCP registry statistics."""
    
    downloads: Optional[int] = Field(None, description="Number of downloads")
    rating: Optional[float] = Field(None, description="Server rating")
    last_updated: Optional[datetime] = Field(None, description="Last update time")
    version: Optional[str] = Field(None, description="Server version")

# ============================================================================
# MCP DISCOVERY MODELS
# ============================================================================

class MCPDiscoveredTool(_PermissiveBaseModel):
    """Discovered MCP tool."""
    
    name: str = Field(..., description="Tool name (may be prefixed)")
    original_name: str = Field(..., description="Original tool name")
    server: str = Field(..., description="Server name")
    server_id: str = Field(..., description="Server ID")
    description: Optional[str] = Field(None, description="Tool description")
    inputSchema: Optional[Dict[str, Any]] = Field(None, description="Input schema")

class MCPToolsDiscovery(_PermissiveBaseModel):
    """MCP tools discovery result."""
    
    tools: List[MCPDiscoveredTool] = Field(..., description="List of discovered tools")
    total_tools: int = Field(..., description="Total number of tools")
    connected_servers: int = Field(..., description="Number of connected servers")
    server_details: Optional[Dict[str, Any]] = Field(None, description="Server details")
