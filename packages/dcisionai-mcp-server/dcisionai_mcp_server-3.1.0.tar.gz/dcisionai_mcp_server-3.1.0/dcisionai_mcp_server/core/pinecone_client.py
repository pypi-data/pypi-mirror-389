#!/usr/bin/env python3
"""
Pinecone Knowledge Base Client
Replaces AWS Bedrock Knowledge Base with Pinecone vector database
"""

import os
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

# Pinecone import disabled for now
PINECONE_AVAILABLE = False
Pinecone = None

logger = logging.getLogger(__name__)


class PineconeKnowledgeBase:
    """Pinecone-based knowledge base for intent classification"""
    
    def __init__(self):
        """Initialize Pinecone client and OpenAI client"""
        if not PINECONE_AVAILABLE:
            raise ImportError("Pinecone package is not available. Please install pinecone-client or make Pinecone optional.")
        
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        self.index_name = "dcisionai-model-kb"
        self.index_host = "dcisionai-model-kb-xbm58wf.svc.aped-4627-b74a.pinecone.io"
        
        try:
            self.index = self.pc.Index(self.index_name, host=self.index_host)
            logger.info(f"✅ Connected to Pinecone index: {self.index_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Pinecone index: {e}")
            raise
        
        # Initialize OpenAI for embeddings
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.embedding_model = "text-embedding-3-large"
        
        logger.info("✅ Pinecone Knowledge Base client initialized")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            return None
    
    def query_knowledge_base(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Query the Pinecone knowledge base for relevant use cases"""
        try:
            logger.info(f"🔍 Querying Pinecone KB: '{query[:50]}...'")
            
            # Generate embedding for the query
            embedding = self.generate_embedding(query)
            if not embedding:
                logger.error("Failed to generate embedding for query")
                return {"error": "Failed to generate embedding"}
            
            # Query Pinecone
            results = self.index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            if not results.matches:
                logger.warning("No results found in Pinecone KB")
                return {"error": "No results found"}
            
            logger.info(f"📊 Found {len(results.matches)} results from Pinecone KB")
            
            # Process results
            matches = []
            for match in results.matches:
                matches.append({
                    "score": match.score,
                    "industry": match.metadata.get("industry", "unknown"),
                    "use_case": match.metadata.get("use_case", "unknown"),
                    "text": match.metadata.get("text", ""),
                    "metadata": match.metadata
                })
            
            return {
                "matches": matches,
                "total_matches": len(matches),
                "query": query
            }
            
        except Exception as e:
            logger.error(f"❌ Error querying Pinecone KB: {e}")
            return {"error": str(e)}
    
    def extract_intent_from_results(self, query: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract intent classification from Pinecone results"""
        try:
            if "error" in results:
                return {"error": results["error"]}
            
            matches = results.get("matches", [])
            if not matches:
                return {"error": "No matches found"}
            
            # Get the best match
            best_match = matches[0]
            best_score = best_match["score"]
            
            # Determine confidence based on score
            if best_score >= 0.6:
                confidence = 0.9
            elif best_score >= 0.4:
                confidence = 0.7
            elif best_score >= 0.2:
                confidence = 0.5
            else:
                confidence = 0.3
            
            # Extract information from best match
            industry = best_match["industry"]
            use_case = best_match["use_case"]
            text_preview = best_match["text"][:200] + "..." if len(best_match["text"]) > 200 else best_match["text"]
            
            # Check if this is a supported industry
            supported_industries = ["MANUFACTURING", "RETAIL", "FINANCE"]
            is_supported = industry in supported_industries
            
            # Additional check: If query contains logistics/warehouse keywords but matches retail,
            # this should be treated as roadmap case
            logistics_keywords = ["warehouse", "3pl", "logistics", "fulfillment", "picking", "shipping", "delivery", "distribution"]
            query_lower = query.lower()
            has_logistics_keywords = any(keyword in query_lower for keyword in logistics_keywords)
            
            if has_logistics_keywords and industry == "RETAIL":
                logger.info(f"⚠️ Logistics keywords detected in query but matched to retail - treating as roadmap")
                is_supported = False
                industry = "LOGISTICS"  # Override industry for roadmap response
            
            # Generate reasoning
            reasoning = f"Based on the query '{query}', the knowledge base identified this as a {industry.lower()} optimization problem. "
            reasoning += f"The best match is {use_case.replace('_', ' ').title()} with a similarity score of {best_score:.3f}. "
            reasoning += f"This use case involves: {text_preview}"
            
            return {
                "intent": f"{industry.lower()}_{use_case}",
                "industry": industry,
                "matched_use_case": use_case,
                "confidence": confidence,
                "reasoning": reasoning,
                "best_match_score": best_score,
                "is_supported": is_supported,
                "text_preview": text_preview,
                "all_matches": matches[:3]  # Include top 3 matches for context
            }
            
        except Exception as e:
            logger.error(f"❌ Error extracting intent from results: {e}")
            return {"error": str(e)}
    
    def classify_intent(self, problem_description: str) -> Dict[str, Any]:
        """Main method to classify intent using Pinecone knowledge base"""
        try:
            logger.info(f"🧠 Classifying intent for: '{problem_description[:50]}...'")
            
            # Query the knowledge base
            kb_results = self.query_knowledge_base(problem_description)
            
            if "error" in kb_results:
                logger.warning(f"KB query failed: {kb_results['error']}")
                return {
                    "status": "kb_failed",
                    "error": kb_results["error"],
                    "intent": "unmatched",
                    "confidence": 0.0
                }
            
            # Extract intent from results
            intent_result = self.extract_intent_from_results(problem_description, kb_results)
            
            if "error" in intent_result:
                logger.warning(f"Intent extraction failed: {intent_result['error']}")
                return {
                    "status": "extraction_failed",
                    "error": intent_result["error"],
                    "intent": "unmatched",
                    "confidence": 0.0
                }
            
            # Check if this is a roadmap case (unsupported industry)
            if not intent_result.get("is_supported", False):
                logger.info(f"⚠️ Unsupported industry detected: {intent_result.get('industry')}")
                return {
                    "status": "roadmap",
                    "intent": intent_result["intent"],
                    "industry": intent_result["industry"],
                    "matched_use_case": intent_result["matched_use_case"],
                    "confidence": intent_result["confidence"],
                    "reasoning": intent_result["reasoning"],
                    "roadmap_response": True
                }
            
            # Successful classification
            logger.info(f"✅ Intent classified: {intent_result['intent']} (confidence: {intent_result['confidence']})")
            return {
                "status": "success",
                "intent": intent_result["intent"],
                "industry": intent_result["industry"],
                "matched_use_case": intent_result["matched_use_case"],
                "confidence": intent_result["confidence"],
                "reasoning": intent_result["reasoning"],
                "best_match_score": intent_result["best_match_score"],
                "text_preview": intent_result["text_preview"],
                "all_matches": intent_result["all_matches"]
            }
            
        except Exception as e:
            logger.error(f"❌ Intent classification error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "intent": "unmatched",
                "confidence": 0.0
            }
