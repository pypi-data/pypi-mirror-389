#!/usr/bin/env python3
"""
Refactored Workflow Orchestrator - Centralized Prompt Custodian
Based on LangChain's Chain-of-Thought approach with centralized prompt management
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from .prompt_manager import CentralizedPromptManager

logger = logging.getLogger(__name__)

class PromptCustodianOrchestrator:
    """
    Workflow orchestrator that acts as custodian of all prompts and Chain-of-Thought reasoning
    Based on LangChain's SequentialChain approach
    """
    
    def __init__(self):
        # Initialize centralized prompt manager
        self.prompt_manager = CentralizedPromptManager()
        
        # Initialize tool clients
        self._initialize_tool_clients()
        
        # Workflow state
        self.workflow_id = None
        self.start_time = None
        
    def _initialize_tool_clients(self):
        """Initialize clients for each tool without Pinecone dependencies"""
        try:
            from ..tools_modules.intent_classifier import IntentClassifier
            # No Pinecone - use None for knowledge base
            self.intent_classifier = IntentClassifier(None, {})
            logger.info("✅ Intent Classifier initialized (no Pinecone)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Intent Classifier: {e}")
            self.intent_classifier = None
        
        try:
            from ..tools_modules.data_analyzer import DataAnalyzer
            # No Pinecone - use None for knowledge base
            self.data_analyzer = DataAnalyzer(None)
            logger.info("✅ Data Analyzer initialized (no Pinecone)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Data Analyzer: {e}")
            self.data_analyzer = None
        
        try:
            from ..tools_modules.model_builder import ModelBuilder
            # FMCO model builder doesn't take knowledge base parameter
            self.model_builder = ModelBuilder()
            logger.info("✅ Model Builder initialized (FMCO-based)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Model Builder: {e}")
            self.model_builder = None
        
        try:
            from ..tools_modules.optimization_solver import OptimizationSolver
            self.optimization_solver = OptimizationSolver()
            logger.info("✅ Optimization Solver initialized (HybridSolver-based)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Optimization Solver: {e}")
            self.optimization_solver = None
    
    async def execute_complete_workflow(
        self, 
        problem_description: str,
        model_preference: str = "fine-tuned"
    ) -> Dict[str, Any]:
        """
        Execute the complete optimization workflow with centralized prompt management
        Based on LangChain's SequentialChain approach
        """
        
        # Initialize workflow
        self.workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.now()
        
        logger.info(f"🚀 Starting Chain-of-Thought workflow: {self.workflow_id}")
        
        # Initialize workflow results
        workflow_results = {
            "workflow_id": self.workflow_id,
            "start_time": self.start_time.isoformat(),
            "status": "running",
            "steps": {},
            "reasoning_chain": {},
            "errors": [],
            "summary": {}
        }
        
        try:
            # Step 1: Intent Classification with CoT (Claude)
            logger.info("📋 Step 1: Intent Classification with Chain-of-Thought (Claude)...")
            intent_result = await self._execute_intent_classification_step(
                problem_description, "claude"
            )
            workflow_results["steps"]["intent"] = intent_result
            
            # Wait between calls to avoid rate limiting
            await asyncio.sleep(1)
            
            if intent_result.get("status") == "error":
                workflow_results["errors"].append("Intent classification failed")
                workflow_results["status"] = "failed"
                return workflow_results
            
            # Step 2: Data Analysis with CoT (GPT-4)
            logger.info("📊 Step 2: Data Analysis with Chain-of-Thought (GPT-4)...")
            data_result = await self._execute_data_analysis_step(
                problem_description, intent_result, "gpt-4"
            )
            workflow_results["steps"]["data"] = data_result
            
            # Wait between calls to avoid rate limiting
            await asyncio.sleep(1)
            
            if data_result.get("status") == "error":
                workflow_results["errors"].append("Data analysis failed")
                workflow_results["status"] = "failed"
                return workflow_results
            
            # Step 3: Model Building with CoT (Fine-tuned)
            logger.info("🏗️ Step 3: Model Building with Chain-of-Thought (Fine-tuned)...")
            model_result = await self._execute_model_building_step(
                problem_description, intent_result, data_result, "fine-tuned"
            )
            workflow_results["steps"]["model"] = model_result
            
            # Wait between calls to avoid rate limiting
            await asyncio.sleep(1)
            
            if model_result.get("status") == "error":
                workflow_results["errors"].append("Model building failed")
                workflow_results["status"] = "failed"
                return workflow_results
            
            # Add reasoning chain to results
            workflow_results["reasoning_chain"] = self.prompt_manager.get_reasoning_chain()
            
            # Add provider distribution information
            workflow_results["provider_distribution"] = {
                "intent": "claude",
                "data": "gpt-4", 
                "model": "fine-tuned"
            }
            workflow_results["execution_strategy"] = "sequential_provider_distribution"
            
            # Generate workflow summary
            workflow_results["summary"] = self._generate_workflow_summary(workflow_results)
            workflow_results["status"] = "completed"
            workflow_results["end_time"] = datetime.now().isoformat()
            
            logger.info("✅ Sequential workflow with provider distribution completed successfully!")
            return workflow_results
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            workflow_results["status"] = "failed"
            workflow_results["errors"].append(str(e))
            workflow_results["end_time"] = datetime.now().isoformat()
            return workflow_results
    
    async def _execute_intent_classification_step(
        self, 
        problem_description: str, 
        model_preference: str
    ) -> Dict[str, Any]:
        """Execute intent classification step with centralized prompt management"""
        try:
            # Format prompt using centralized manager
            prompt = self.prompt_manager.format_prompt(
                "intent_classification",
                problem_description=problem_description,
                problem_analysis=self.prompt_manager.reasoning_chain.get("problem_analysis", "Initial problem analysis pending..."),
                intent_reasoning=self.prompt_manager.reasoning_chain.get("intent_reasoning", "Intent classification reasoning pending..."),
                data_reasoning=self.prompt_manager.reasoning_chain.get("data_reasoning", "Data analysis reasoning pending..."),
                model_reasoning=self.prompt_manager.reasoning_chain.get("model_reasoning", "Model building reasoning pending..."),
                solver_reasoning=self.prompt_manager.reasoning_chain.get("solver_reasoning", "Solver selection reasoning pending..."),
                optimization_reasoning=self.prompt_manager.reasoning_chain.get("optimization_reasoning", "Optimization solving reasoning pending..."),
                simulation_reasoning=self.prompt_manager.reasoning_chain.get("simulation_reasoning", "Simulation analysis reasoning pending..."),
                previous_results="None"
            )
            
            # Call intent classifier with centralized prompt
            result = await self.intent_classifier.classify_intent_with_prompt(
                prompt, model_preference=model_preference
            )
            
            # Extract and store reasoning
            reasoning = self.prompt_manager.extract_reasoning_from_response(
                result.get("response", ""), "intent_classification"
            )
            if reasoning:
                self.prompt_manager.update_reasoning_chain("intent_reasoning", reasoning)
            
            # Validate response
            validation = self.prompt_manager.validate_response(
                result.get("response", ""), "intent_classification"
            )
            if not validation["is_valid"]:
                logger.warning(f"⚠️ Intent classification validation issues: {validation['issues']}")
            
            logger.info(f"✅ Intent classification completed with CoT reasoning")
            return result
            
        except Exception as e:
            logger.error(f"❌ Intent classification failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _execute_data_analysis_step(
        self, 
        problem_description: str,
        intent_result: Dict[str, Any],
        model_preference: str
    ) -> Dict[str, Any]:
        """Execute data analysis step with centralized prompt management"""
        try:
            # Extract intent data for prompt
            intent_data = intent_result.get("result", {})
            
            # Format prompt using centralized manager
            prompt = self.prompt_manager.format_prompt(
                "data_analysis",
                problem_description=problem_description,
                intent_result=intent_result,
                industry=intent_data.get("industry", "unknown"),
                optimization_type=intent_data.get("optimization_type", "linear"),
                intent=intent_data.get("intent", "unknown"),
                matched_use_case=intent_data.get("matched_use_case", "unknown"),
                problem_analysis=self.prompt_manager.reasoning_chain.get("problem_analysis", "Initial problem analysis pending..."),
                intent_reasoning=self.prompt_manager.reasoning_chain.get("intent_reasoning", "Intent classification reasoning pending..."),
                data_reasoning=self.prompt_manager.reasoning_chain.get("data_reasoning", "Data analysis reasoning pending..."),
                model_reasoning=self.prompt_manager.reasoning_chain.get("model_reasoning", "Model building reasoning pending..."),
                solver_reasoning=self.prompt_manager.reasoning_chain.get("solver_reasoning", "Solver selection reasoning pending..."),
                optimization_reasoning=self.prompt_manager.reasoning_chain.get("optimization_reasoning", "Optimization solving reasoning pending..."),
                simulation_reasoning=self.prompt_manager.reasoning_chain.get("simulation_reasoning", "Simulation analysis reasoning pending..."),
                previous_results={"intent": intent_result}
            )
            
            # Call data analyzer with centralized prompt
            result = await self.data_analyzer.analyze_data_with_prompt(
                prompt, intent_data=intent_result, model_preference=model_preference
            )
            
            # Extract and store reasoning
            reasoning = self.prompt_manager.extract_reasoning_from_response(
                result.get("response", ""), "data_analysis"
            )
            if reasoning:
                self.prompt_manager.update_reasoning_chain("data_reasoning", reasoning)
            
            # Validate response
            validation = self.prompt_manager.validate_response(
                result.get("response", ""), "data_analysis"
            )
            if not validation["is_valid"]:
                logger.warning(f"⚠️ Data analysis validation issues: {validation['issues']}")
            
            logger.info(f"✅ Data analysis completed with CoT reasoning")
            return result
            
        except Exception as e:
            logger.error(f"❌ Data analysis failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _execute_model_building_step(
        self, 
        problem_description: str,
        intent_result: Dict[str, Any],
        data_result: Dict[str, Any],
        model_preference: str
    ) -> Dict[str, Any]:
        """Execute model building step with centralized prompt management"""
        try:
            # Extract data for prompt
            intent_data = intent_result.get("result", {})
            simulated_data = data_result.get("result", {}).get("simulated_data", {})
            
            # Format prompt using centralized manager
            prompt = self.prompt_manager.format_prompt(
                "model_building",
                problem_description=problem_description,
                intent_result=intent_result,
                data_result=data_result,
                industry=intent_data.get("industry", "unknown"),
                optimization_type=intent_data.get("optimization_type", "linear"),
                selected_solver="OR-Tools",
                solver_capabilities=["linear", "integer", "mixed_integer"],
                data_variables=list(simulated_data.get("variables", {}).keys()),
                data_constraints=list(simulated_data.get("constraints", {}).keys()),
                data_objective=simulated_data.get("objective", {}),
                data_parameters=list(simulated_data.get("parameters", {}).keys()),
                problem_analysis=self.prompt_manager.reasoning_chain.get("problem_analysis", "Initial problem analysis pending..."),
                intent_reasoning=self.prompt_manager.reasoning_chain.get("intent_reasoning", "Intent classification reasoning pending..."),
                data_reasoning=self.prompt_manager.reasoning_chain.get("data_reasoning", "Data analysis reasoning pending..."),
                model_reasoning=self.prompt_manager.reasoning_chain.get("model_reasoning", "Model building reasoning pending..."),
                solver_reasoning=self.prompt_manager.reasoning_chain.get("solver_reasoning", "Solver selection reasoning pending..."),
                optimization_reasoning=self.prompt_manager.reasoning_chain.get("optimization_reasoning", "Optimization solving reasoning pending..."),
                simulation_reasoning=self.prompt_manager.reasoning_chain.get("simulation_reasoning", "Simulation analysis reasoning pending..."),
                previous_results={"intent": intent_result, "data": data_result}
            )
            
            # Call model builder with centralized prompt
            result = await self.model_builder.build_model_with_prompt(
                prompt, intent_data=intent_result, data_analysis=data_result, model_preference=model_preference
            )
            
            # Extract and store reasoning
            reasoning = self.prompt_manager.extract_reasoning_from_response(
                result.get("response", ""), "model_building"
            )
            if reasoning:
                self.prompt_manager.update_reasoning_chain("model_reasoning", reasoning)
            
            # Validate response
            validation = self.prompt_manager.validate_response(
                result.get("response", ""), "model_building"
            )
            if not validation["is_valid"]:
                logger.warning(f"⚠️ Model building validation issues: {validation['issues']}")
            
            logger.info(f"✅ Model building completed with CoT reasoning")
            return result
            
        except Exception as e:
            logger.error(f"❌ Model building failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def _generate_workflow_summary(self, workflow_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate workflow summary with Chain-of-Thought insights"""
        summary = {
            "workflow_id": workflow_results["workflow_id"],
            "status": workflow_results["status"],
            "steps_completed": len(workflow_results["steps"]),
            "reasoning_chain_length": len(self.prompt_manager.get_reasoning_chain()),
            "total_errors": len(workflow_results["errors"]),
            "chain_of_thought_enabled": True,
            "prompt_management": "centralized",
            "reasoning_quality": "high" if len(workflow_results["errors"]) == 0 else "medium"
        }
        
        # Add step-specific summaries
        for step_name, step_result in workflow_results["steps"].items():
            if step_result.get("status") == "success":
                summary[f"{step_name}_status"] = "success"
                summary[f"{step_name}_reasoning"] = "included"
            else:
                summary[f"{step_name}_status"] = "failed"
                summary[f"{step_name}_reasoning"] = "missing"
        
        return summary
    
    async def _execute_optimization_step(
        self,
        problem_description: str,
        intent_result: Dict[str, Any],
        data_result: Dict[str, Any],
        model_result: Dict[str, Any],
        model_preference: str = "fine-tuned"
    ) -> Dict[str, Any]:
        """Execute optimization/solving step"""
        try:
            if not self.optimization_solver:
                return {"status": "error", "error": "Optimization solver not initialized"}
            
            logger.info("⚡ Executing optimization step...")
            
            # Extract model data from model_result
            model_data = {
                'variables': model_result.get('variables', []),
                'constraints': model_result.get('constraints', []),
                'objective': model_result.get('objective', {}),
                'problem_config': model_result.get('problem_config', {}),
                'model_config': model_result.get('model_config', {}),
                'solver_config': model_result.get('solver_config', {})
            }
            
            # Call optimization solver with intent_data for smart routing
            result = await self.optimization_solver.solve_optimization(
                problem_description=problem_description,
                intent_data=intent_result,
                data_analysis=data_result,
                model_building=model_result  # Pass the full model_result, not just model_data
            )
            
            if result.get('status') in ['optimal', 'feasible', 'success']:
                logger.info("✅ Optimization completed successfully")
            else:
                logger.warning(f"⚠️ Optimization completed with status: {result.get('status')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Optimization step failed: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
