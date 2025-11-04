#!/usr/bin/env python3
"""
HTTP Wrapper for DcisionAI MCP Server - Direct Call Version
============================================================

Calls MCP tools directly (no subprocess) for maximum performance and simplicity.
This is the production-ready approach.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / '.env.staging'
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"✅ Loaded environment from {env_path}")
else:
    logger.warning(f"⚠️  No .env.staging found at {env_path}")

app = FastAPI(title="DcisionAI MCP HTTP Server - Direct")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Any
    method: str
    params: Dict[str, Any] = {}

class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Any
    result: Any = None
    error: Any = None

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {"status": "healthy", "service": "DcisionAI MCP Server"}

@app.post("/mcp")
async def handle_mcp_request(request: MCPRequest) -> MCPResponse:
    """Handle MCP requests by calling tools directly"""
    try:
        logger.info(f"🔍 Handling MCP request: {request.method}")
        
        if request.method == "tools/call":
            tool_name = request.params.get("name")
            arguments = request.params.get("arguments", {})
            
            logger.info(f"🔧 Calling tool: {tool_name} with args: {list(arguments.keys())}")
            
            # Route to the appropriate tool
            if tool_name in ["execute_complete_workflow", "execute_complete_workflow_tool"]:
                # Full workflow (multi-step: intent → data → model → optimization)
                from dcisionai_mcp_server.tools import execute_complete_workflow
                result = await execute_complete_workflow(**arguments)
                return MCPResponse(jsonrpc=request.jsonrpc, id=request.id, result=result)
            
            elif tool_name in ["solve_express", "lmea_express", "execute_express_workflow"]:
                # Express Mode (single-shot: problem → V2 Solver → solution)
                # CLEAN ARCHITECTURE: Direct call to V2 Solver, no intermediate layers
                from dcisionai_mcp_server.models.dcisionai_solver_v2 import DcisionAISolverV2
                solver = DcisionAISolverV2()
                result = await solver.solve_auto(
                    problem_description=arguments.get("problem_description"),
                    max_generations=arguments.get("max_generations", 200)
                )
                return MCPResponse(jsonrpc=request.jsonrpc, id=request.id, result=result)
            
            elif tool_name in ["dcisionai_solve", "dcisionai_solver", "solve_v2"]:
                # DcisionAI-Solver V2 (Universal solver with domain injection)
                from dcisionai_mcp_server.models.dcisionai_solver_v2 import DcisionAISolverV2
                solver = DcisionAISolverV2()
                result = await solver.solve(
                    problem_description=arguments.get("problem_description"),
                    domain_id=arguments.get("domain_id", "retail_layout"),
                    max_time_seconds=arguments.get("max_time_seconds", 30)
                )
                return MCPResponse(jsonrpc=request.jsonrpc, id=request.id, result=result)
            
            else:
                return MCPResponse(
                    jsonrpc=request.jsonrpc,
                    id=request.id,
                    error={"code": -32601, "message": f"Tool not found: {tool_name}"}
                )
        
        elif request.method == "tools/list":
            # Return list of available tools
            tools = [
                {"name": "execute_complete_workflow", "description": "Execute complete optimization workflow"}
            ]
            return MCPResponse(jsonrpc=request.jsonrpc, id=request.id, result={"tools": tools})
        
        elif request.method == "initialize":
            # Return initialization response
            return MCPResponse(
                jsonrpc=request.jsonrpc,
                id=request.id,
                result={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "serverInfo": {"name": "dcisionai-http-direct", "version": "1.0.0"}
                }
            )
        
        else:
            return MCPResponse(
                jsonrpc=request.jsonrpc,
                id=request.id,
                error={"code": -32601, "message": f"Method not found: {request.method}"}
            )
            
    except Exception as e:
        logger.error(f"❌ Error handling request: {e}", exc_info=True)
        return MCPResponse(
            jsonrpc=request.jsonrpc,
            id=request.id,
            error={"code": -32603, "message": str(e)}
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "DcisionAI MCP HTTP Server (Direct) is running"}

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting DcisionAI MCP HTTP Server (Direct Mode) on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

