"""
DcisionAI MCP Server - Optimization Intelligence for AI Workflows

This package provides optimization capabilities through the Model Context Protocol (MCP),
enabling AI agents to solve complex optimization problems across multiple industries.

Key Features:
- 7 Industry Workflows: Manufacturing, Healthcare, Retail, Marketing, Financial, Logistics, Energy
- Qwen 30B Integration: Advanced mathematical optimization
- Real-Time Results: Actual optimization solutions with mathematical proofs
- MCP Protocol: Seamless integration with AI development environments

Example Usage:
    from dcisionai_mcp_server import mcp
    
    # Execute a manufacturing optimization workflow
    result = mcp.execute_workflow(
        industry="manufacturing",
        workflow_id="production_planning"
    )
"""

__version__ = "2.4.0"
__author__ = "DcisionAI"
__email__ = "contact@dcisionai.com"
__description__ = "Optimization Intelligence for AI Workflows via Model Context Protocol (MCP)"

# Import main components (lazy loading to avoid config validation on import)
try:
    # V2: Single-tool production MCP server for FastMCP Cloud
    from .mcp_server_v2 import mcp
    
    # Legacy tools (deprecated, but kept for backward compatibility)
    # NOTE: These individual tools are replaced by dcisionai_solve in V2
    from .tools import (
        classify_intent,
        analyze_data,
        build_model,
        solve_optimization,
        explain_optimization,
        get_workflow_templates,
        execute_workflow
    )
    
    # Legacy run_server (not needed for FastMCP Cloud)
    run_server = None
except Exception as e:
    # If import fails due to missing config, provide helpful error
    import warnings
    warnings.warn(f"Some components could not be imported: {e}. Make sure to configure the MCP server properly.")
    
    # Provide None values for failed imports
    mcp = None
    run_server = None
    classify_intent = None
    analyze_data = None
    build_model = None
    solve_optimization = None
    explain_optimization = None
    get_workflow_templates = None
    execute_workflow = None

# Export main components
__all__ = [
    "mcp",
    "run_server",
    "classify_intent",
    "analyze_data", 
    "build_model",
    "solve_optimization",
    "explain_optimization",
    "get_workflow_templates",
    "execute_workflow"
]