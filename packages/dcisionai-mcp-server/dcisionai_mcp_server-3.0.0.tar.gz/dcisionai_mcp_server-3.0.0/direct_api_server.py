#!/usr/bin/env python3
"""
Direct HTTP API for DcisionAI MCP Tools
This bypasses the MCP protocol and calls tools directly
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env.staging
env_path = os.path.join(os.path.dirname(__file__), '../..', '.env.staging')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Add the fastapi-server directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the MCP tools directly
from dcisionai_mcp_server.tools import (
    classify_intent,
    analyze_data,
    build_model,
    solve_optimization,
    # select_solver,  # DEPRECATED - HiGHS is hardcoded as primary
    explain_optimization,
    simulate_scenarios,
    execute_optimization_workflow,
    benchmark_models,
    execute_complete_workflow
)

# Import the new DcisionAI tool (V2 solver with LLM narratives)
from dcisionai_mcp_server.tools_modules.dcisionai_tool import dcisionai_solve

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log environment variable loading status
if os.path.exists(env_path):
    logger.info(f"✅ Loaded environment variables from {env_path}")
else:
    logger.warning(f"⚠️ Environment file not found: {env_path}")

app = FastAPI(title="DcisionAI Direct HTTP API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ToolRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}

class ToolResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Any
    result: Any = None
    error: Any = None

@app.post("/mcp")
async def handle_tool_request(request: ToolRequest) -> ToolResponse:
    """Handle tool requests directly"""
    try:
        logger.info(f"🔍 Handling tool request: {request.name}")
        
        # Map tool names to functions
        tool_functions = {
            "classify_intent": classify_intent,
            "analyze_data": analyze_data,
            "build_model": build_model,
            "solve_optimization": solve_optimization,
            # "select_solver": select_solver,  # DEPRECATED
            "explain_optimization": explain_optimization,
            "simulate_scenarios": simulate_scenarios,
            "execute_optimization_workflow": execute_optimization_workflow,
            "benchmark_models": benchmark_models,
            "execute_complete_workflow": execute_complete_workflow,
            "dcisionai_solve": dcisionai_solve  # NEW: V2 solver with LLM narratives
        }
        
        if request.name not in tool_functions:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {request.name}")
        
        # Call the tool function
        tool_func = tool_functions[request.name]
        
        # Extract arguments
        args = request.arguments
        
        # Call the tool
        if request.name == "classify_intent":
            result = await tool_func(
                problem_description=args.get("problem_description", ""),
                context=args.get("context")
            )
        elif request.name == "analyze_data":
            logger.info(f"🔍 Direct API Server: analyze_data called with args: {args}")
            logger.info(f"🔍 Direct API Server: intent_data = {args.get('intent_data')}")
            result = await tool_func(
                problem_description=args.get("problem_description", ""),
                intent_data=args.get("intent_data"),
                model_preference=args.get("model_preference", "anthropic")
            )
        elif request.name == "build_model":
            result = await tool_func(
                problem_description=args.get("problem_description", ""),
                intent_data=args.get("intent_data"),
                data_analysis=args.get("data_analysis"),
                solver_selection=args.get("solver_selection"),
                validate_output=args.get("validate_output", True),
                model_preference=args.get("model_preference", "anthropic")
            )
        elif request.name == "solve_optimization":
            result = await tool_func(
                problem_description=args.get("problem_description", ""),
                context=args.get("context")
            )
        # elif request.name == "select_solver":  # DEPRECATED
        #     result = await tool_func(
        #         problem_description=args.get("problem_description", ""),
        #         context=args.get("context")
        #     )
        elif request.name == "explain_optimization":
            result = await tool_func(
                problem_description=args.get("problem_description", ""),
                context=args.get("context")
            )
        elif request.name == "simulate_scenarios":
            result = await tool_func(
                problem_description=args.get("problem_description", ""),
                context=args.get("context")
            )
        elif request.name == "execute_optimization_workflow":
            result = await tool_func(
                problem_description=args.get("problem_description", "")
            )
        elif request.name == "benchmark_models":
            result = await tool_func(
                models=args.get("models", ["fine-tuned", "gpt-4o", "claude-3-5-sonnet"]),
                test_cases=args.get("test_cases")
            )
        elif request.name == "execute_complete_workflow":
            result = await tool_func(
                problem_description=args.get("problem_description", ""),
                model_preference=args.get("model_preference", "fine-tuned"),
                tools_to_call=args.get("tools_to_call"),
                fmco_features=args.get("fmco_features"),
                architecture=args.get("architecture", "auto"),
                tuning_config=args.get("tuning_config")
            )
        elif request.name == "dcisionai_solve":
            result = await tool_func(
                problem_description=args.get("problem_description", "")
            )
        else:
            result = await tool_func(**args)
        
        logger.info(f"✅ Tool {request.name} executed successfully")
        
        return ToolResponse(
            id=1,
            result=result
        )
        
    except Exception as e:
        logger.error(f"❌ Tool execution error: {e}")
        return ToolResponse(
            id=1,
            error={
                "code": -32603,
                "message": f"Tool execution failed: {str(e)}"
            }
        )

@app.get("/tools")
async def list_tools():
    """List available tools"""
    return {
        "tools": [
            {
                "name": "classify_intent",
                "description": "Classify user intent for optimization requests",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "problem_description": {"type": "string"},
                        "context": {"type": "string"}
                    },
                    "required": ["problem_description"]
                }
            },
            {
                "name": "analyze_data",
                "description": "Analyze data readiness for optimization",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "problem_description": {"type": "string"},
                        "intent_data": {"type": "object"},
                        "model_preference": {"type": "string", "enum": ["anthropic", "openai"], "default": "anthropic"}
                    },
                    "required": ["problem_description"]
                }
            },
            {
                "name": "build_model",
                "description": "Build optimization model",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "problem_description": {"type": "string"},
                        "intent_data": {"type": "object"},
                        "data_analysis": {"type": "object"},
                        "solver_selection": {"type": "object"},
                        "validate_output": {"type": "boolean", "default": True},
                        "model_preference": {
                            "type": "string",
                            "enum": ["anthropic", "openai", "fine-tuned", "gpt-4o", "claude"],
                            "default": "anthropic"
                        }
                    },
                    "required": ["problem_description"]
                }
            },
            {
                "name": "solve_optimization",
                "description": "Solve optimization problem",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "problem_description": {"type": "string"},
                        "context": {"type": "string"}
                    },
                    "required": ["problem_description"]
                }
            },
            # {
            #     "name": "select_solver",  # DEPRECATED
            #     "description": "Select appropriate solver",
            #     "inputSchema": {
            #         "type": "object",
            #         "properties": {
            #             "problem_description": {"type": "string"},
            #             "context": {"type": "string"}
            #         },
            #         "required": ["problem_description"]
            #     }
            # },
            {
                "name": "explain_optimization",
                "description": "Explain optimization results",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "problem_description": {"type": "string"},
                        "context": {"type": "string"}
                    },
                    "required": ["problem_description"]
                }
            },
            {
                "name": "simulate_scenarios",
                "description": "Simulate optimization scenarios",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "problem_description": {"type": "string"},
                        "context": {"type": "string"}
                    },
                    "required": ["problem_description"]
                }
            },
            {
                "name": "execute_optimization_workflow",
                "description": "Execute complete optimization workflow",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "problem_description": {"type": "string"}
                    },
                    "required": ["problem_description"]
                }
            },
            {
                "name": "benchmark_models",
                "description": "Benchmark different LLM models across various metrics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "models": {
                            "type": "array",
                            "items": {"type": "string"},
                            "default": ["fine-tuned", "gpt-4o", "claude-3-5-sonnet"]
                        },
                        "test_cases": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Optional custom test cases"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "execute_complete_workflow",
                "description": "Execute the complete optimization workflow (Intent → Data → Model → Solver → Solve → Simulate)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "problem_description": {
                            "type": "string",
                            "description": "The optimization problem description"
                        },
                        "model_preference": {
                            "type": "string",
                            "enum": ["fine-tuned", "gpt-4o", "claude-3-5-sonnet"],
                            "default": "fine-tuned",
                            "description": "LLM model preference for the workflow"
                        }
                    },
                    "required": ["problem_description"]
                }
            }
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "DcisionAI Direct HTTP API is running"}

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting DcisionAI Direct HTTP API on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
