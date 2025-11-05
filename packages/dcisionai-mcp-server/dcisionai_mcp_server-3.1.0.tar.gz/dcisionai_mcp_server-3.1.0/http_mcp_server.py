#!/usr/bin/env python3
"""
HTTP Wrapper for DcisionAI MCP Server - Production Grade
=========================================================

Maintains a persistent MCP server process for optimal performance:
- Single long-running subprocess (no startup overhead per request)
- Thread-safe request handling with locks
- Graceful shutdown and error recovery
- Sub-100ms response times
"""

import asyncio
import atexit
import json
import logging
import os
import subprocess
import sys
from threading import Lock
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global MCP server process management
mcp_process: Optional[subprocess.Popen] = None
mcp_lock = Lock()
mcp_initialized = False

app = FastAPI(title="DcisionAI MCP HTTP Server")

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

def start_mcp_server():
    """Start the persistent MCP server process"""
    global mcp_process, mcp_initialized
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logger.info("🚀 Starting persistent MCP server process...")
        
        mcp_process = subprocess.Popen(
            [sys.executable, "-m", "dcisionai_mcp_server.mcp_server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=current_dir,
            bufsize=0  # Unbuffered for real-time communication
        )
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "dcisionai-http-proxy",
                    "version": "1.0.0"
                }
            }
        }
        
        mcp_process.stdin.write(json.dumps(init_request) + "\n")
        mcp_process.stdin.flush()
        
        # Read initialization response
        init_response = mcp_process.stdout.readline()
        if init_response:
            init_data = json.loads(init_response.strip())
            if "error" not in init_data or init_data["error"] is None:
                mcp_initialized = True
                logger.info("✅ MCP server initialized successfully")
            else:
                logger.error(f"❌ MCP initialization error: {init_data.get('error')}")
        
    except Exception as e:
        logger.error(f"❌ Failed to start MCP server: {e}")
        raise

def stop_mcp_server():
    """Stop the persistent MCP server process"""
    global mcp_process, mcp_initialized
    
    if mcp_process:
        logger.info("🛑 Stopping MCP server process...")
        try:
            mcp_process.terminate()
            mcp_process.wait(timeout=5)
        except:
            mcp_process.kill()
        finally:
            mcp_process = None
            mcp_initialized = False
        logger.info("✅ MCP server stopped")

# Register cleanup on exit
atexit.register(stop_mcp_server)

@app.on_event("startup")
async def startup_event():
    """Start the MCP server when FastAPI starts"""
    start_mcp_server()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the MCP server when FastAPI shuts down"""
    stop_mcp_server()

@app.post("/mcp")
async def handle_mcp_request(request: MCPRequest) -> MCPResponse:
    """Handle MCP requests via HTTP using the persistent MCP server"""
    global mcp_process, mcp_initialized
    
    if not mcp_process or not mcp_initialized:
        logger.error("❌ MCP server not initialized")
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    try:
        logger.info(f"🔍 Handling MCP request: {request.method}")
        
        # Prepare the MCP request
        mcp_request = {
            "jsonrpc": request.jsonrpc,
            "id": request.id,
            "method": request.method,
            "params": request.params
        }
        
        # Thread-safe communication with the MCP server
        with mcp_lock:
            # Send the request
            request_json = json.dumps(mcp_request) + "\n"
            mcp_process.stdin.write(request_json)
            mcp_process.stdin.flush()
            
            # Read the response
            response_line = mcp_process.stdout.readline()
            
            if not response_line:
                logger.error("❌ No response from MCP server")
                raise HTTPException(status_code=500, detail="No response from MCP server")
            
            try:
                response_data = json.loads(response_line.strip())
                logger.info(f"✅ MCP response received for method: {request.method}")
                return MCPResponse(**response_data)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse MCP response: {e}")
                logger.error(f"Raw response: {response_line}")
                raise HTTPException(status_code=500, detail=f"Failed to parse MCP response: {e}")
                
    except Exception as e:
        logger.error(f"❌ MCP request error: {e}")
        
        # Try to restart the MCP server if it crashed
        if mcp_process and mcp_process.poll() is not None:
            logger.warning("⚠️ MCP server crashed, attempting to restart...")
            stop_mcp_server()
            start_mcp_server()
            raise HTTPException(status_code=503, detail="MCP server restarting, please retry")
        
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = "ok" if (mcp_process and mcp_initialized) else "mcp_not_ready"
    return {
        "status": status,
        "message": "DcisionAI MCP HTTP Server is running",
        "mcp_initialized": mcp_initialized
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting DcisionAI MCP HTTP Server (Production Mode) on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
