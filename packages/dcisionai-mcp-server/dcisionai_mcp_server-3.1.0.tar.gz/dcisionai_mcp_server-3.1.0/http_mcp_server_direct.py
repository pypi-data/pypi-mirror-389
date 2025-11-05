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

# Set default Supabase credentials (internal infrastructure)
# Users don't need to provide these - it's DcisionAI's backend
# Railway env vars will override these defaults if set
if "SUPABASE_URL" not in os.environ:
    os.environ["SUPABASE_URL"] = "https://nbhrvwegrveoiurnwbij.supabase.co"
if "SUPABASE_API_KEY" not in os.environ:
    os.environ["SUPABASE_API_KEY"] = "sb_secret_Rp3EG4cJlCg9ZU5cGlLZ5g_SimVHcgy"

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
    return {"status": "ok", "message": "DcisionAI Direct HTTP API is running"}

@app.get("/version")
async def version_check():
    """Version endpoint to verify deployment"""
    return {
        "version": "3.0.25",
        "service": "DcisionAI MCP Server - Direct",
        "deployment": "railway",
        "updated": "2025-11-04T05:15:00Z"
    }

@app.post("/migrate/add-generator-methods")
async def migrate_add_generator_methods():
    """Add synthetic_generator_method to FinServ configs in Supabase"""
    try:
        from supabase import create_client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_API_KEY")
        
        if not url or not key:
            return {"status": "error", "message": "Missing Supabase credentials"}
        
        supabase = create_client(url, key)
        
        generator_methods = {
            'customer_onboarding': 'generate_customer_onboarding',
            'pe_exit_timing': 'generate_pe_exit_timing',
            'hf_rebalancing': 'generate_hf_rebalancing'
        }
        
        results = {}
        
        for domain_id, method in generator_methods.items():
            try:
                # Get current config
                result = supabase.table('domain_configs').select('*').eq('domain', domain_id).execute()
                
                if not result.data:
                    results[domain_id] = "not_found"
                    continue
                
                config = result.data[0]
                parsing_config = config.get('parsing_config', {})
                
                # Add synthetic_generator_method if missing
                if 'synthetic_generator_method' not in parsing_config:
                    parsing_config['synthetic_generator_method'] = method
                    
                    # Update in Supabase
                    supabase.table('domain_configs').update({
                        'parsing_config': parsing_config
                    }).eq('domain', domain_id).execute()
                    
                    results[domain_id] = f"added: {method}"
                else:
                    results[domain_id] = f"already_exists: {parsing_config['synthetic_generator_method']}"
            
            except Exception as e:
                results[domain_id] = f"error: {str(e)}"
        
        return {"status": "success", "results": results}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/mcp")
async def handle_mcp_request(request: MCPRequest) -> MCPResponse:
    """Handle MCP requests by calling tools directly"""
    try:
        logger.info(f"🔍 Handling MCP request: {request.method}")
        logger.info(f"🔍 Request params: {request.params}")
        
        if request.method == "tools/call":
            tool_name = request.params.get("name")
            arguments = request.params.get("arguments", {})
            
            logger.info(f"🔧 Calling tool: {tool_name} with args: {list(arguments.keys())}")
            
            # Route to the appropriate tool
            if tool_name in ["dcisionai_workflow", "execute_complete_workflow", "execute_complete_workflow_tool"]:
                # Full workflow (multi-step: intent → data → model → optimization)
                from dcisionai_mcp_server.tools import execute_complete_workflow
                result = await execute_complete_workflow(**arguments)
                return MCPResponse(jsonrpc=request.jsonrpc, id=request.id, result=result)
            
            elif tool_name in ["dcisionai_solve", "solve_express", "lmea_express", "execute_express_workflow"]:
                # Express Mode (single-shot: problem → V2 Solver → solution)
                # CLEAN ARCHITECTURE: Direct call to V2 Solver, no intermediate layers
                from dcisionai_mcp_server.models.dcisionai_solver_v2 import DcisionAISolverV2
                solver = DcisionAISolverV2()
                result = await solver.solve_auto(
                    problem_description=arguments.get("problem_description"),
                    max_generations=arguments.get("max_generations", 200)
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
                {
                    "name": "dcisionai_solve",
                    "description": "🚀 DcisionAI Express: Lightning-fast optimization solver (problem → solution in seconds). Best for quick decisions.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "problem_description": {
                                "type": "string",
                                "description": "Natural language description of your optimization problem (e.g., 'Optimize my portfolio with $10k', 'Schedule 5 employees across 3 shifts')"
                            },
                            "max_generations": {
                                "type": "integer",
                                "description": "Maximum solver iterations (default: 200)",
                                "default": 200
                            }
                        },
                        "required": ["problem_description"]
                    }
                },
                {
                    "name": "dcisionai_workflow",
                    "description": "🎯 DcisionAI Complete: Full workflow with multi-step analysis, validation, and detailed explanations. Best for complex decisions.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "problem_description": {
                                "type": "string",
                                "description": "Natural language description of your optimization problem"
                            }
                        },
                        "required": ["problem_description"]
                    }
                }
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
                    "serverInfo": {"name": "DcisionAI MCP Server", "version": "3.0.6"}
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

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting DcisionAI MCP HTTP Server (Direct Mode) on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

