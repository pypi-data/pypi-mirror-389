#!/usr/bin/env python3
"""
Session-Aware Workflow Orchestrator
Uses Supabase session management for persistent workflow state
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.session_manager import session_manager
from .prompt_custodian_orchestrator import PromptCustodianOrchestrator

logger = logging.getLogger(__name__)

class SessionAwareOrchestrator:
    """
    Workflow orchestrator that uses Supabase session management
    Provides persistent state, natural delays, and debugging capabilities
    """
    
    def __init__(self):
        self.session_manager = session_manager
        self.base_orchestrator = PromptCustodianOrchestrator()
    
    async def execute_complete_workflow(
        self, 
        problem_description: str,
        model_preference: str = "fine-tuned",
        tools_to_call: Optional[list] = None,
        fmco_features: Optional[Dict[str, Any]] = None,
        architecture: str = "auto",
        tuning_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute workflow with session management
        Each step is persisted to Supabase with natural delays
        
        Args:
            problem_description: The optimization problem description
            model_preference: LLM model preference
            tools_to_call: List of tools to execute (e.g., ['intent', 'data', 'model'])
                         If None, executes all tools in sequence
        """
        
        # Debug: Log what was passed in
        logger.info(f"🔍 DEBUG: tools_to_call parameter = {tools_to_call}")
        logger.info(f"🔍 DEBUG: tools_to_call type = {type(tools_to_call)}")
        
        # Default tools sequence if not specified
        if tools_to_call is None:
            tools_to_call = ['intent', 'data', 'model', 'optimization']
            logger.info("⚠️ tools_to_call was None, using default: ['intent', 'data', 'model', 'optimization']")
        
        logger.info(f"🔧 Tools to execute: {tools_to_call}")
        
        # Handle FMCO features with resource management (DISABLED - Phase 2 features in garage)
        if fmco_features:
            logger.warning("⚠️ FMCO Phase 2 features are currently disabled (moved to garage)")
            logger.info("Phase 2 features require GPU/Pinecone and are not yet enabled in production")
            # Disable all FMCO features
            for feature in fmco_features:
                fmco_features[feature] = False
        
        # Create session
        session_id = self.session_manager.create_session(problem_description, model_preference)
        logger.info(f"🚀 Starting session-aware workflow: {session_id}")
        
        try:
            # Execute tools based on tools_to_call configuration
            for i, tool_name in enumerate(tools_to_call, 1):
                logger.info(f"📋 Step {i}: Executing {tool_name} tool...")
                
                if tool_name == 'intent':
                    result = await self._execute_intent_step(session_id, problem_description)
                elif tool_name == 'data':
                    # Get intent result from previous step
                    session = self.session_manager.get_session(session_id)
                    intent_result = session.get('steps', {}).get('intent', {})
                    result = await self._execute_data_step(session_id, problem_description, intent_result)
                elif tool_name == 'model':
                    # Get previous results
                    session = self.session_manager.get_session(session_id)
                    intent_result = session.get('steps', {}).get('intent', {})
                    data_result = session.get('steps', {}).get('data', {})
                    result = await self._execute_model_step(session_id, problem_description, intent_result, data_result)
                elif tool_name == 'solver' or tool_name == 'optimization':
                    # Get previous results
                    session = self.session_manager.get_session(session_id)
                    intent_result = session.get('steps', {}).get('intent', {})
                    data_result = session.get('steps', {}).get('data', {})
                    model_result = session.get('steps', {}).get('model', {})
                    result = await self._execute_optimization_step(session_id, problem_description, intent_result, data_result, model_result)
                else:
                    logger.warning(f"⚠️ Unknown tool: {tool_name}")
                    continue
                
                # Check for errors
                if result.get("status") == "error":
                    logger.error(f"❌ {tool_name} tool failed: {result.get('error')}")
                    self.session_manager.update_session_status(session_id, "failed")
                    return self._build_session_response(session_id, "failed", f"{tool_name} tool failed")
                
                # Add delay between tools to avoid rate limiting
                await asyncio.sleep(1)
                logger.info(f"✅ {tool_name} tool completed successfully")
            
            # Mark workflow as completed
            self.session_manager.update_session_status(session_id, "completed")
            logger.info(f"🎉 Session-aware workflow completed: {session_id}")
            
            return self._build_session_response(session_id, "completed")
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            self.session_manager.update_session_status(session_id, "failed")
            self.session_manager.add_session_error(session_id, str(e))
            return self._build_session_response(session_id, "failed", str(e))
    
    async def _execute_intent_step(self, session_id: str, problem_description: str) -> Dict[str, Any]:
        """Execute intent classification step with session persistence"""
        try:
            # Use the original working method directly (bypass complex prompt system)
            from ..tools_modules.intent_classifier import IntentClassifier
            from ..core.pinecone_client import PineconeKnowledgeBase
            
            # Initialize intent classifier with minimal dependencies
            try:
                knowledge_base = PineconeKnowledgeBase()
                cache = {}
                intent_classifier = IntentClassifier(knowledge_base, cache)
                
                # Use the original working simplified method
                intent_result = await intent_classifier.classify_intent_simplified(
                    problem_description, 
                    model_preference="fine-tuned"
                )
                
                logger.info("✅ Used original working intent classification method")
                
            except Exception as e:
                logger.warning(f"⚠️ Pinecone not available, using fallback: {e}")
                # Fallback: create minimal intent classifier
                intent_classifier = IntentClassifier(None, {})
                intent_result = await intent_classifier.classify_intent_simplified(
                    problem_description, 
                    model_preference="fine-tuned"
                )
            
            # Persist to session
            self.session_manager.update_session_step(session_id, "intent", intent_result)
            
            # Natural delay (database write + processing time)
            await asyncio.sleep(2)
            
            return intent_result
            
        except Exception as e:
            logger.error(f"❌ Intent step failed: {e}")
            error_result = {"status": "error", "error": str(e)}
            self.session_manager.update_session_step(session_id, "intent", error_result)
            return error_result
    
    async def _execute_data_step(self, session_id: str, problem_description: str, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data analysis step with session persistence"""
        try:
            # Call the base orchestrator's data step
            data_result = await self.base_orchestrator._execute_data_analysis_step(
                problem_description, intent_result, "gpt-4"
            )
            
            # Persist to session
            self.session_manager.update_session_step(session_id, "data", data_result)
            
            # Natural delay (database write + processing time)
            await asyncio.sleep(2)
            
            return data_result
            
        except Exception as e:
            logger.error(f"❌ Data step failed: {e}")
            error_result = {"status": "error", "error": str(e)}
            self.session_manager.update_session_step(session_id, "data", error_result)
            return error_result
    
    async def _execute_model_step(self, session_id: str, problem_description: str, intent_result: Dict[str, Any], data_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute model building step with session persistence"""
        try:
            # Call the base orchestrator's model step
            model_result = await self.base_orchestrator._execute_model_building_step(
                problem_description, intent_result, data_result, "fine-tuned"
            )
            
            # Persist to session
            self.session_manager.update_session_step(session_id, "model", model_result)
            
            # Natural delay (database write + processing time)
            await asyncio.sleep(2)
            
            return model_result
            
        except Exception as e:
            logger.error(f"❌ Model step failed: {e}")
            error_result = {"status": "error", "error": str(e)}
            self.session_manager.update_session_step(session_id, "model", error_result)
            return error_result
    
    async def _execute_optimization_step(self, session_id: str, problem_description: str, intent_result: Dict[str, Any], data_result: Dict[str, Any], model_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute optimization solving step with session persistence"""
        try:
            # Call the base orchestrator's optimization step
            optimization_result = await self.base_orchestrator._execute_optimization_step(
                problem_description, intent_result, data_result, model_result
            )
            
            # Persist to session
            self.session_manager.update_session_step(session_id, "optimization", optimization_result)
            
            # Natural delay (solver execution time)
            await asyncio.sleep(2)
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"❌ Optimization step failed: {e}")
            error_result = {"status": "error", "error": str(e)}
            self.session_manager.update_session_step(session_id, "optimization", error_result)
            return error_result
    
    def _build_session_response(self, session_id: str, status: str, error: Optional[str] = None) -> Dict[str, Any]:
        """Build response with session information"""
        session = self.session_manager.get_session(session_id)
        
        response = {
            "session_id": session_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "execution_strategy": "session_aware_sequential",
            "provider_distribution": {
                "intent": "claude",
                "data": "gpt-4",
                "model": "fine-tuned"
            }
        }
        
        if session:
            response.update({
                "steps": session.get("steps", {}),
                "reasoning_chain": session.get("reasoning_chain", {}),
                "summary": session.get("summary", {}),
                "errors": session.get("errors", [])
            })
        
        if error:
            response["error"] = error
        
        return response
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current session status"""
        session = self.session_manager.get_session(session_id)
        if not session:
            return {"status": "not_found", "error": "Session not found"}
        
        return {
            "session_id": session_id,
            "status": session.get("status", "unknown"),
            "steps": session.get("steps", {}),
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at"),
            "errors": session.get("errors", [])
        }
    
    async def resume_session(self, session_id: str) -> Dict[str, Any]:
        """Resume a workflow session from where it left off"""
        session = self.session_manager.get_session(session_id)
        if not session:
            return {"status": "not_found", "error": "Session not found"}
        
        if session.get("status") == "completed":
            return self._build_session_response(session_id, "completed")
        
        # Resume from the last completed step
        steps = session.get("steps", {})
        
        if "intent" not in steps:
            # Start from intent
            return await self._execute_intent_step(session_id, session.get("problem_description", ""))
        elif "data" not in steps:
            # Resume from data
            intent_result = steps["intent"]
            return await self._execute_data_step(session_id, session.get("problem_description", ""), intent_result)
        elif "model" not in steps:
            # Resume from model
            intent_result = steps["intent"]
            data_result = steps["data"]
            return await self._execute_model_step(session_id, session.get("problem_description", ""), intent_result, data_result)
        else:
            # All steps completed
            self.session_manager.update_session_status(session_id, "completed")
            return self._build_session_response(session_id, "completed")
    
    # DISABLED: FMCO Phase 2 feature (moved to garage)
    # async def _integrate_latest_papers(self):
    #     """Integrate latest FMCO papers into knowledge base"""
    #     try:
    #         from ..tools_modules.garage.fmco_paper_integration import FMCOPaperIntegrator
    #         
    #         integrator = FMCOPaperIntegrator()
    #         result = await integrator.run_automated_integration(days_back=7, max_papers=10)
    #         
    #         if result.get("status") == "success":
    #             logger.info(f"✅ Integrated {result['successful_integrations']} papers")
    #         else:
    #             logger.warning(f"⚠️ Paper integration failed: {result.get('message')}")
    #             
    #     except Exception as e:
    #         logger.error(f"❌ Paper integration error: {e}")
