"""
Orchestrators for DcisionAI MCP Server
======================================

Production orchestration system for optimization workflows.

Active Orchestrators:
--------------------

1. SessionAwareOrchestrator - Primary entry point for UI workflows
   - Session state management (in-memory or Supabase)
   - FMCO features integration
   - Tool selection via tools_to_call parameter
   - Sequential execution with rate limiting
   - Provider distribution (Claude/GPT-4/Fine-tuned)

2. PromptCustodianOrchestrator - Centralized prompt management
   - LangChain SequentialChain approach
   - Chain-of-Thought (CoT) reasoning
   - Domain-specific prompt templates

3. CentralizedPromptManager - COSTAR framework prompts
   - Zero-shot & Few-shot CoT
   - Unique delimiters for security
   - Prompt chaining

Production Flow:
---------------
UI Request → execute_complete_workflow()
              ↓
           SessionAwareOrchestrator (305 lines)
              ├─ Session management
              ├─ Tool selection (tools_to_call)
              ├─ FMCO features
              ↓
           PromptCustodianOrchestrator (349 lines)
              ├─ Centralized prompts
              ├─ Chain-of-Thought
              ↓
           CentralizedPromptManager (764 lines)
              ├─ COSTAR framework
              ↓
           Individual Tools
              ├─ IntentClassifier
              ├─ DataAnalyzer
              ├─ ModelBuilder
              └─ etc.

Archived Orchestrators:
----------------------
- ToolOrchestrator → archive/obsolete_orchestrators/tool_orchestrator.py
  (Legacy/simple workflow - not used by production UI)
"""

from .prompt_manager import CentralizedPromptManager
from .prompt_custodian_orchestrator import PromptCustodianOrchestrator
from .session_aware_orchestrator import SessionAwareOrchestrator

__all__ = [
    'CentralizedPromptManager',
    'PromptCustodianOrchestrator',
    'SessionAwareOrchestrator'
]

