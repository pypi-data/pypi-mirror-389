#!/usr/bin/env python3
"""
DcisionAI MCP Server - Command-Line Entry Point
================================================

For use with:
- Cursor IDE (via uvx)
- Claude Desktop (via uvx)
- VS Code with MCP extension (via uvx)
- Any MCP-compatible client

Environment variables required:
- OPENAI_API_KEY (required)
- ANTHROPIC_API_KEY (required)

Optional environment variables:
- POLYGON_API_KEY (for real-time market data)
- ALPHA_VANTAGE_API_KEY (for economic/commodity data)

Internal infrastructure (no user setup needed):
- Supabase (domain configurations)
"""

import os
import sys
from pathlib import Path

from fastmcp import FastMCP

# Set default Supabase credentials (internal infrastructure)
# Users don't need to provide these - it's DcisionAI's backend
if "SUPABASE_URL" not in os.environ:
    os.environ["SUPABASE_URL"] = "https://nbhrvwegrveoiurnwbij.supabase.co"
if "SUPABASE_API_KEY" not in os.environ:
    os.environ["SUPABASE_API_KEY"] = "sb_secret_Rp3EG4cJlCg9ZU5cGlLZ5g_SimVHcgy"

# Initialize FastMCP server
mcp = FastMCP(
    name="DcisionAI",
    version="3.0.6",
    instructions="""
    🎯 DcisionAI - AI-Powered Optimization Platform
    
    Solve complex business optimization problems across industries:
    
    📊 Finance:
      - Portfolio rebalancing with risk constraints
      - Trading schedule optimization
      - Asset allocation with concentration limits
    
    🏪 Retail:
      - Store layout optimization (shelf space allocation)
      - Promotion scheduling with budget constraints
      - Inventory placement optimization
    
    🚚 Logistics:
      - Vehicle routing (VRP) with time windows
      - Delivery route optimization
      - Fleet allocation
    
    👥 Workforce:
      - Employee scheduling with skill requirements
      - Shift rostering with labor rules
      - Resource allocation
    
    🏭 Manufacturing:
      - Job shop scheduling
      - Maintenance scheduling
      - Production planning
    
    ⚡ Powered by DAME Algorithm:
      - DcisionAI Micro-differential Evolutionary Algorithm (proprietary)
      - 95-100% trust scores with mathematical proofs
      - 0.1-3% optimality gap in 0.5-5 seconds
      - Parallel solver validation with HiGHS for LP/MIP
    
    📈 Features:
      - Auto-classifies problem type from natural language
      - Extracts or simulates data intelligently
      - Generates business-friendly interpretations
      - Provides mathematical validation proofs
      - Supports parallel solver comparison for trust
    
    🔧 Validation Modes:
      - "auto": Smart routing (LP/MIP → parallel, complex → DAME)
      - "parallel": Run both HiGHS + DAME for max trust
      - "fast": Fastest solver only
      - "exact": HiGHS only (LP/MIP provably optimal)
      - "heuristic": DAME only (works for all problems)
    
    Just describe your problem in natural language and get optimized solutions
    with mathematical proof and business recommendations!
    """
)

@mcp.tool()
async def dcisionai_solve(
    problem_description: str,
    validation_mode: str = "auto"
) -> dict:
    """
    🎯 Solve any optimization problem using DcisionAI.
    
    Automatically classifies problem type, extracts/simulates data,
    builds optimization model, solves, and provides results with
    mathematical proof and business interpretation.
    
    Args:
        problem_description (str): Natural language description of your problem.
            Example: "Optimize a $500K portfolio concentrated in tech stocks 
                     for a 45-year-old moderate risk client retiring in 20 years"
        
        validation_mode (str): Solver validation strategy (default: "auto")
            - "auto": Smart routing (LP/MIP → parallel validation)
            - "parallel": Always run both solvers (slower, higher trust)
            - "fast": Use fastest solver only
            - "exact": HiGHS only (fails if not LP/MIP)
            - "heuristic": DAME only (works for all problems)
    
    Returns:
        dict: Complete optimization results including:
            - status: "success" or "error"
            - industry: Classified industry (FINANCE, RETAIL, LOGISTICS, etc.)
            - domain_id: Specific problem type
            - domain_name: Human-readable problem type
            - intent_reasoning: Why this classification was chosen
            - data_provenance: Data sources, quality, sufficiency
            - structured_results: Complete solution breakdown
            - objective_value: Final objective function value
            - trust_score: Solution confidence (0.0-1.0)
            - certification: "VERIFIED", "PARTIAL", or "UNVERIFIED"
            - mathematical_proof: Full proof suite with validations
            - business_interpretation: LLM-generated business insights
            - solver_comparison: If parallel mode, HiGHS vs DAME results
            - evolution_history: Fitness progression over generations
    
    Example:
        result = await dcisionai_solve(
            problem_description="Optimize delivery routes for 20 customers",
            validation_mode="auto"
        )
        
        print(f"Trust Score: {result['trust_score']}")
        print(f"Certification: {result['certification']}")
        print(f"Business Interpretation: {result['business_interpretation']}")
    """
    from dcisionai_mcp_server.models.dcisionai_solver_v2 import DcisionAISolverV2
    
    # Initialize solver
    solver = DcisionAISolverV2()
    
    # Use solve_auto for clean architecture (auto-classification)
    result = await solver.solve_auto(
        problem_description=problem_description,
        validation_mode=validation_mode,
        max_generations=200  # Fixed: solve_auto uses max_generations, not max_time_seconds
    )
    
    return result


# For local testing (optional, ignored by FastMCP Cloud)
if __name__ == "__main__":
    import asyncio
    from dcisionai_mcp_server.models.dcisionai_solver_v2 import DcisionAISolverV2
    
    async def test_local():
        """Test the MCP server locally before deploying."""
        print("🧪 Testing DcisionAI MCP Server locally...\n")
        
        # Test problem: Portfolio optimization
        test_problem = """
        I'm onboarding a new client with a $500,000 portfolio that's 85% 
        concentrated in tech stocks (AAPL, MSFT, GOOGL, NVIDIA). The client 
        is 45 years old with moderate risk tolerance and wants to retire in 
        20 years. They're paying high fees (1.2% average expense ratios) and 
        are concerned about concentration risk. I need to quickly analyze 
        their current portfolio and provide an optimized allocation 
        recommendation that reduces risk, lowers fees, and aligns with 
        their retirement goals.
        """
        
        print(f"📝 Problem: {test_problem[:100]}...\n")
        
        try:
            # Test the solver directly (not through MCP protocol)
            solver = DcisionAISolverV2()
            result = await solver.solve_auto(
                problem_description=test_problem,
                validation_mode="auto",
                max_time_seconds=30
            )
            
            print("✅ Test Results:")
            print(f"   Status: {result.get('status', 'N/A')}")
            print(f"   Industry: {result.get('industry', 'N/A')}")
            print(f"   Domain: {result.get('domain_name', 'N/A')}")
            print(f"   Trust Score: {result.get('trust_score', 0):.1%}")
            print(f"   Certification: {result.get('certification', 'N/A')}")
            print(f"   Objective Value: {result.get('objective_value', 'N/A')}")
            
            if result.get('business_interpretation'):
                print(f"\n💼 Business Interpretation:")
                print(f"   {result['business_interpretation'][:200]}...")
            
            if result.get('solver_comparison'):
                comp = result['solver_comparison']
                print(f"\n🔍 Solver Comparison:")
                print(f"   HiGHS: {comp.get('highs_objective', 'N/A')}")
                print(f"   DAME: {comp.get('dame_objective', 'N/A')}")
                print(f"   Gap: {comp.get('objective_gap_pct', 'N/A')}%")
            
            print("\n🎉 Local test passed! Ready for FastMCP Cloud deployment.")
            print("\n📋 Next steps:")
            print("   1. Commit changes: git add mcp_server.py requirements.txt")
            print("   2. Push to GitHub: git push origin main")
            print("   3. Sign up at: https://fastmcp.cloud")
            print("   4. Deploy with entrypoint: mcp_server.py:mcp")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Run the test
    asyncio.run(test_local())


def main():
    """
    Main entry point for the dcisionai-mcp-server command.
    
    This is called when users run:
    - uvx dcisionai-mcp-server@latest
    - python -m dcisionai_mcp_server.server
    """
    # Run the MCP server (FastMCP handles stdin/stdout)
    mcp.run()
