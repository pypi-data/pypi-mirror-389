#!/usr/bin/env python3
"""
DcisionAI MCP Server - Main Entry Point (V2)
============================================

This is the main entry point for the DcisionAI MCP Server when run as a module.

NOTE: For FastMCP Cloud deployment, this file should NOT be used.
FastMCP Cloud imports the 'mcp' object directly from mcp_server_v2.py.

This file is only for local testing/development with stdio transport.
"""

import sys
import logging

# Prevent running this module for FastMCP Cloud
print("⚠️  WARNING: __main__.py should not be used for FastMCP Cloud deployment", file=sys.stderr)
print("ℹ️  FastMCP Cloud should import: dcisionai_mcp_server.mcp_server_v2:mcp", file=sys.stderr)
print("ℹ️  For local testing, use: python -m dcisionai_mcp_server.mcp_server_v2", file=sys.stderr)

sys.exit(1)
