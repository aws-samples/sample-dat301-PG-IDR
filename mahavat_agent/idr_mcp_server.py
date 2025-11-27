#!/usr/bin/env python3
"""
IDR MCP Server
Provides incident management tools via MCP protocol
Knowledge base retrieval is handled by Bedrock KB Retrieval MCP Server
"""

import os
import json
import boto3
from typing import Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'dat301-ws-incidents')

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

# Create MCP server
app = Server("idr-mcp-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available IDR tools"""
    return [
        Tool(
            name="list_incidents",
            description="List all incidents from DynamoDB. Optionally filter by status (PENDING, RESOLVED).",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status: PENDING or RESOLVED",
                        "enum": ["PENDING", "RESOLVED"]
                    }
                }
            }
        ),
        Tool(
            name="get_incident_details",
            description="Get detailed information about a specific incident by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "incident_id": {
                        "type": "string",
                        "description": "The incident ID"
                    }
                },
                "required": ["incident_id"]
            }
        ),
        Tool(
            name="update_incident_status",
            description="Update the status of an incident to RESOLVED. ONLY use this AFTER verifying the remediation was successful.",
            inputSchema={
                "type": "object",
                "properties": {
                    "incident_id": {
                        "type": "string",
                        "description": "The incident ID to update"
                    },
                    "resolution": {
                        "type": "string",
                        "description": "Resolution notes describing what was changed"
                    }
                },
                "required": ["incident_id", "resolution"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    
    try:
        if name == "list_incidents":
            return await list_incidents(arguments.get("status"))
        
        elif name == "get_incident_details":
            return await get_incident_details(arguments["incident_id"])
        
        elif name == "update_incident_status":
            return await update_incident_status(
                arguments["incident_id"],
                arguments["resolution"]
            )
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Error in {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def list_incidents(status: Optional[str] = None) -> list[TextContent]:
    """List incidents from DynamoDB"""
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        
        if status:
            response = table.scan(
                FilterExpression='incident_status = :status',
                ExpressionAttributeValues={':status': status}
            )
        else:
            response = table.scan()
        
        incidents = response.get('Items', [])
        
        if not incidents:
            return [TextContent(type="text", text="No incidents found.")]
        
        result = f"Found {len(incidents)} incidents:\n\n"
        for inc in incidents:
            result += f"**{inc.get('incident_id', 'N/A')}**\n"
            result += f"- Type: {inc.get('incident_type', 'Unknown')}\n"
            result += f"- Identifier: {inc.get('incident_identifier', 'Unknown')}\n"
            result += f"- Status: {inc.get('incident_status', 'Unknown')}\n"
            result += f"- Alarm: {inc.get('alarm_name', 'N/A')}\n"
            result += f"- Reason: {inc.get('alarm_reason', 'N/A')}\n"
            result += f"- Created: {inc.get('created_at', 'N/A')}\n\n"
        
        return [TextContent(type="text", text=result)]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing incidents: {str(e)}")]

async def get_incident_details(incident_id: str) -> list[TextContent]:
    """Get incident details"""
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        
        # Query using pk
        response = table.query(
            KeyConditionExpression='pk = :pk',
            ExpressionAttributeValues={':pk': f'INCIDENT#{incident_id}'}
        )
        
        items = response.get('Items', [])
        if not items:
            return [TextContent(type="text", text=f"Incident {incident_id} not found.")]
        
        incident = items[0]
        result = json.dumps(incident, indent=2, default=str)
        return [TextContent(type="text", text=result)]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting incident: {str(e)}")]

async def update_incident_status(incident_id: str, resolution: str) -> list[TextContent]:
    """Update incident status to RESOLVED"""
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        
        # First get the item to find the sk
        response = table.query(
            KeyConditionExpression='pk = :pk',
            ExpressionAttributeValues={':pk': f'INCIDENT#{incident_id}'}
        )
        
        items = response.get('Items', [])
        if not items:
            return [TextContent(type="text", text=f"Incident {incident_id} not found.")]
        
        sk = items[0]['sk']
        
        from datetime import datetime
        table.update_item(
            Key={'pk': f'INCIDENT#{incident_id}', 'sk': sk},
            UpdateExpression='SET incident_status = :status, updated_at = :updated_at, resolution = :resolution',
            ExpressionAttributeValues={
                ':status': 'RESOLVED',
                ':updated_at': datetime.utcnow().isoformat(),
                ':resolution': resolution
            }
        )
        
        return [TextContent(type="text", text=f"Successfully updated incident {incident_id} to RESOLVED")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error updating incident: {str(e)}")]

async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
