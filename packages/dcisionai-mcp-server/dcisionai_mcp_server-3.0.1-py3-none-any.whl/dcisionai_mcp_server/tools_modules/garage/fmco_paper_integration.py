"""
FMCO Paper Integration System
Automatically integrate latest FMCO research papers into Pinecone KB
"""

import logging
import json
import asyncio
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import os
import re

logger = logging.getLogger(__name__)

@dataclass
class FMCOPaper:
    """FMCO research paper structure"""
    title: str
    authors: List[str]
    abstract: str
    url: str
    arxiv_id: Optional[str]
    published_date: str
    categories: List[str]
    key_findings: List[str]
    methodologies: List[str]
    datasets: List[str]
    architectures: List[str]
    applications: List[str]

class FMCOPaperIntegrator:
    """Automated FMCO paper integration system"""
    
    def __init__(self):
        self.arxiv_api_url = "http://export.arxiv.org/api/query"
        self.pinecone_client = None  # Will be initialized when needed
        self.fmco_keywords = [
            "foundation models combinatorial optimization",
            "large language models optimization",
            "neural combinatorial optimization",
            "transformer optimization",
            "graph neural network optimization",
            "reinforcement learning optimization",
            "meta-learning optimization",
            "few-shot optimization",
            "in-context learning optimization",
            "prompting optimization",
            "chain-of-thought optimization",
            "program synthesis optimization",
            "code generation optimization",
            "automated optimization",
            "neural architecture search optimization",
            "multi-task optimization",
            "transfer learning optimization",
            "self-supervised optimization",
            "contrastive learning optimization",
            "attention mechanism optimization"
        ]
        
        # Initialize Pinecone client
        self._initialize_pinecone()
    
    def _initialize_pinecone(self):
        """Initialize Pinecone client for paper storage"""
        try:
            from ..core.pinecone_client import PineconeKnowledgeBase
            self.pinecone_client = PineconeKnowledgeBase()
            logger.info("✅ Pinecone client initialized for FMCO paper integration")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Pinecone client: {e}")
            self.pinecone_client = None
    
    async def fetch_latest_papers(self, days_back: int = 30, max_papers: int = 50) -> List[FMCOPaper]:
        """Fetch latest FMCO papers from arXiv"""
        
        logger.info(f"🔍 Fetching FMCO papers from last {days_back} days...")
        
        papers = []
        start_date = datetime.now() - timedelta(days=days_back)
        
        for keyword in self.fmco_keywords[:5]:  # Limit to avoid rate limiting
            try:
                # Search arXiv for papers
                query_params = {
                    "search_query": f"all:{keyword}",
                    "start": 0,
                    "max_results": 10,
                    "sortBy": "submittedDate",
                    "sortOrder": "descending"
                }
                
                response = requests.get(self.arxiv_api_url, params=query_params, timeout=30)
                response.raise_for_status()
                
                # Parse XML response
                papers_batch = self._parse_arxiv_response(response.text, start_date)
                papers.extend(papers_batch)
                
                logger.info(f"📄 Found {len(papers_batch)} papers for keyword: {keyword}")
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Failed to fetch papers for keyword '{keyword}': {e}")
                continue
        
        # Remove duplicates and sort by date
        unique_papers = self._deduplicate_papers(papers)
        unique_papers.sort(key=lambda x: x.published_date, reverse=True)
        
        # Limit results
        papers = unique_papers[:max_papers]
        
        logger.info(f"✅ Fetched {len(papers)} unique FMCO papers")
        return papers
    
    def _parse_arxiv_response(self, xml_content: str, min_date: datetime) -> List[FMCOPaper]:
        """Parse arXiv XML response"""
        import xml.etree.ElementTree as ET
        
        papers = []
        
        try:
            root = ET.fromstring(xml_content)
            
            for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                try:
                    # Extract paper information
                    title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip()
                    abstract = entry.find("{http://www.w3.org/2005/Atom}summary").text.strip()
                    published = entry.find("{http://www.w3.org/2005/Atom}published").text
                    
                    # Parse published date
                    pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    if pub_date < min_date:
                        continue
                    
                    # Extract authors
                    authors = []
                    for author in entry.findall("{http://www.w3.org/2005/Atom}author"):
                        name = author.find("{http://www.w3.org/2005/Atom}name").text
                        authors.append(name)
                    
                    # Extract arXiv ID
                    arxiv_id = entry.find("{http://www.w3.org/2005/Atom}id").text.split('/')[-1]
                    
                    # Extract categories
                    categories = []
                    for category in entry.findall("{http://www.w3.org/2005/Atom}category"):
                        cat_term = category.get("term")
                        if cat_term:
                            categories.append(cat_term)
                    
                    # Generate URL
                    url = f"https://arxiv.org/abs/{arxiv_id}"
                    
                    # Analyze paper content
                    key_findings = self._extract_key_findings(abstract, title)
                    methodologies = self._extract_methodologies(abstract, title)
                    datasets = self._extract_datasets(abstract)
                    architectures = self._extract_architectures(abstract, title)
                    applications = self._extract_applications(abstract, title)
                    
                    paper = FMCOPaper(
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        url=url,
                        arxiv_id=arxiv_id,
                        published_date=published,
                        categories=categories,
                        key_findings=key_findings,
                        methodologies=methodologies,
                        datasets=datasets,
                        architectures=architectures,
                        applications=applications
                    )
                    
                    papers.append(paper)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse paper entry: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"❌ Failed to parse arXiv XML: {e}")
        
        return papers
    
    def _extract_key_findings(self, abstract: str, title: str) -> List[str]:
        """Extract key findings from paper"""
        findings = []
        
        # Look for common finding patterns
        patterns = [
            r"achieves?\s+([^.]*?improvement[^.]*)",
            r"outperforms?\s+([^.]*)",
            r"demonstrates?\s+([^.]*)",
            r"proposes?\s+([^.]*)",
            r"introduces?\s+([^.]*)",
            r"novel\s+([^.]*)",
            r"state-of-the-art\s+([^.]*)",
            r"significant\s+([^.]*)"
        ]
        
        text = f"{title} {abstract}".lower()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            findings.extend(matches[:2])  # Limit to 2 per pattern
        
        return findings[:5]  # Limit total findings
    
    def _extract_methodologies(self, abstract: str, title: str) -> List[str]:
        """Extract methodologies from paper"""
        methodologies = []
        
        method_keywords = [
            "transformer", "attention", "graph neural network", "gnn", "reinforcement learning",
            "rl", "meta-learning", "few-shot", "in-context learning", "prompting",
            "chain-of-thought", "program synthesis", "code generation", "neural architecture search",
            "multi-task learning", "transfer learning", "self-supervised", "contrastive learning",
            "variational", "generative", "discriminative", "supervised", "unsupervised",
            "semi-supervised", "active learning", "curriculum learning", "progressive training"
        ]
        
        text = f"{title} {abstract}".lower()
        
        for keyword in method_keywords:
            if keyword in text:
                methodologies.append(keyword)
        
        return methodologies[:8]  # Limit methodologies
    
    def _extract_datasets(self, abstract: str) -> List[str]:
        """Extract datasets mentioned in paper"""
        datasets = []
        
        dataset_keywords = [
            "tsp", "cvrp", "vrp", "or-tools", "miplib", "qaplib", "tsplib", "cvrplib",
            "sat", "maxsat", "csp", "knapsack", "bin packing", "job shop", "flow shop",
            "scheduling", "routing", "assignment", "matching", "clustering", "partitioning"
        ]
        
        text = abstract.lower()
        
        for keyword in dataset_keywords:
            if keyword in text:
                datasets.append(keyword)
        
        return datasets[:5]  # Limit datasets
    
    def _extract_architectures(self, abstract: str, title: str) -> List[str]:
        """Extract architectures from paper"""
        architectures = []
        
        arch_keywords = [
            "transformer", "bert", "gpt", "t5", "encoder-decoder", "attention",
            "graph neural network", "gnn", "gat", "gcn", "graphsage", "gin",
            "lstm", "gru", "rnn", "cnn", "resnet", "densenet", "efficientnet",
            "vit", "swin", "perceiver", "retrieval", "memory", "pointer network"
        ]
        
        text = f"{title} {abstract}".lower()
        
        for keyword in arch_keywords:
            if keyword in text:
                architectures.append(keyword)
        
        return architectures[:6]  # Limit architectures
    
    def _extract_applications(self, abstract: str, title: str) -> List[str]:
        """Extract applications from paper"""
        applications = []
        
        app_keywords = [
            "manufacturing", "retail", "finance", "healthcare", "logistics", "energy",
            "supply chain", "transportation", "telecommunications", "agriculture",
            "environmental", "urban planning", "resource allocation", "portfolio",
            "scheduling", "routing", "inventory", "production", "distribution",
            "warehousing", "procurement", "pricing", "revenue management"
        ]
        
        text = f"{title} {abstract}".lower()
        
        for keyword in app_keywords:
            if keyword in text:
                applications.append(keyword)
        
        return applications[:5]  # Limit applications
    
    def _deduplicate_papers(self, papers: List[FMCOPaper]) -> List[FMCOPaper]:
        """Remove duplicate papers"""
        seen_titles = set()
        unique_papers = []
        
        for paper in papers:
            # Normalize title for comparison
            normalized_title = re.sub(r'[^\w\s]', '', paper.title.lower())
            
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_papers.append(paper)
        
        return unique_papers
    
    async def integrate_papers_to_kb(self, papers: List[FMCOPaper]) -> Dict[str, Any]:
        """Integrate papers into Pinecone knowledge base"""
        
        if not self.pinecone_client:
            logger.error("❌ Pinecone client not initialized")
            return {"status": "error", "message": "Pinecone client not available"}
        
        logger.info(f"📚 Integrating {len(papers)} papers into knowledge base...")
        
        integration_results = {
            "total_papers": len(papers),
            "successful_integrations": 0,
            "failed_integrations": 0,
            "integrated_papers": [],
            "errors": []
        }
        
        for paper in papers:
            try:
                # Create knowledge base entry
                kb_entry = self._create_kb_entry(paper)
                
                # Store in Pinecone
                success = await self._store_paper_in_pinecone(kb_entry)
                
                if success:
                    integration_results["successful_integrations"] += 1
                    integration_results["integrated_papers"].append({
                        "title": paper.title,
                        "arxiv_id": paper.arxiv_id,
                        "url": paper.url
                    })
                else:
                    integration_results["failed_integrations"] += 1
                    integration_results["errors"].append(f"Failed to store: {paper.title}")
                
            except Exception as e:
                logger.error(f"❌ Failed to integrate paper '{paper.title}': {e}")
                integration_results["failed_integrations"] += 1
                integration_results["errors"].append(f"Error with '{paper.title}': {str(e)}")
        
        logger.info(f"✅ Paper integration completed: {integration_results['successful_integrations']}/{integration_results['total_papers']} successful")
        
        return integration_results
    
    def _create_kb_entry(self, paper: FMCOPaper) -> Dict[str, Any]:
        """Create knowledge base entry from paper"""
        
        # Create comprehensive text for embedding
        kb_text = f"""
        Title: {paper.title}
        
        Authors: {', '.join(paper.authors)}
        
        Abstract: {paper.abstract}
        
        Categories: {', '.join(paper.categories)}
        
        Key Findings: {'; '.join(paper.key_findings)}
        
        Methodologies: {', '.join(paper.methodologies)}
        
        Datasets: {', '.join(paper.datasets)}
        
        Architectures: {', '.join(paper.architectures)}
        
        Applications: {', '.join(paper.applications)}
        
        URL: {paper.url}
        ArXiv ID: {paper.arxiv_id}
        Published: {paper.published_date}
        """
        
        # Create metadata
        metadata = {
            "title": paper.title,
            "authors": paper.authors,
            "abstract": paper.abstract,
            "url": paper.url,
            "arxiv_id": paper.arxiv_id,
            "published_date": paper.published_date,
            "categories": paper.categories,
            "key_findings": paper.key_findings,
            "methodologies": paper.methodologies,
            "datasets": paper.datasets,
            "architectures": paper.architectures,
            "applications": paper.applications,
            "paper_type": "fmco_research",
            "integration_date": datetime.now().isoformat(),
            "source": "arxiv"
        }
        
        return {
            "id": f"fmco_paper_{paper.arxiv_id}",
            "text": kb_text.strip(),
            "metadata": metadata
        }
    
    async def _store_paper_in_pinecone(self, kb_entry: Dict[str, Any]) -> bool:
        """Store paper in Pinecone knowledge base"""
        
        try:
            # Use the existing Pinecone client to store the paper
            # This would integrate with the existing knowledge base system
            success = await self.pinecone_client.add_document(
                document_id=kb_entry["id"],
                text=kb_entry["text"],
                metadata=kb_entry["metadata"]
            )
            
            if success:
                logger.info(f"✅ Stored paper: {kb_entry['metadata']['title']}")
            else:
                logger.warning(f"⚠️ Failed to store paper: {kb_entry['metadata']['title']}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error storing paper in Pinecone: {e}")
            return False
    
    async def run_automated_integration(self, days_back: int = 30, max_papers: int = 50) -> Dict[str, Any]:
        """Run complete automated integration process"""
        
        logger.info("🚀 Starting automated FMCO paper integration...")
        
        try:
            # Step 1: Fetch latest papers
            papers = await self.fetch_latest_papers(days_back, max_papers)
            
            if not papers:
                logger.warning("⚠️ No papers found for integration")
                return {
                    "status": "warning",
                    "message": "No papers found for integration",
                    "papers_found": 0
                }
            
            # Step 2: Integrate papers into KB
            integration_results = await self.integrate_papers_to_kb(papers)
            
            # Step 3: Generate summary
            summary = {
                "status": "success",
                "integration_date": datetime.now().isoformat(),
                "papers_found": len(papers),
                "successful_integrations": integration_results["successful_integrations"],
                "failed_integrations": integration_results["failed_integrations"],
                "success_rate": integration_results["successful_integrations"] / len(papers) if papers else 0,
                "latest_papers": [
                    {
                        "title": paper.title,
                        "authors": paper.authors[:3],  # First 3 authors
                        "published_date": paper.published_date,
                        "key_findings": paper.key_findings[:2],  # First 2 findings
                        "methodologies": paper.methodologies[:3],  # First 3 methodologies
                        "url": paper.url
                    }
                    for paper in papers[:5]  # Latest 5 papers
                ]
            }
            
            logger.info(f"✅ Automated integration completed: {summary['successful_integrations']}/{summary['papers_found']} papers integrated")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Automated integration failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "integration_date": datetime.now().isoformat()
            }
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get current integration status"""
        
        return {
            "status": "active",
            "keywords_monitored": len(self.fmco_keywords),
            "pinecone_available": self.pinecone_client is not None,
            "last_integration": datetime.now().isoformat(),
            "monitored_categories": [
                "foundation models", "combinatorial optimization", "neural optimization",
                "transformer optimization", "graph neural networks", "reinforcement learning",
                "meta-learning", "few-shot learning", "prompting", "program synthesis"
            ]
        }
