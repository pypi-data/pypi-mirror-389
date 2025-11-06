"""Parallel research crawler integrating all components."""
import asyncio
from typing import List, Dict, Any, Optional

from .arxiv_crawler import ArXivCrawler
from .paper_filter import PaperFilter
from .semantic_scholar import SemanticScholarSearcher
from .huggingface import HuggingFaceSearcher


class ParallelResearchCrawler:
    """Parallel research crawler with integration to analyzer_agent for keywords."""
    
    def __init__(self, llm=None):
        """Initialize ParallelResearchCrawler.
        
        Args:
            llm: Optional LLM client for generating intelligent search keywords.
                 If provided, will use LLM to generate queries via analyzer_agent.
        """
        self.llm = llm
        self.arxiv_crawler = ArXivCrawler(llm=llm)
        self.paper_filter = PaperFilter()
        self.semantic_scholar = SemanticScholarSearcher()
        self.huggingface = HuggingFaceSearcher()
        
        # Keywords for filtering
        self.base_keywords = ['quantization', 'pruning', 'distillation', 'compression', 
                             'optimization', 'efficient', 'neural network']
    
    def _get_llm_keywords(self, model_info: Dict[str, Any]) -> Optional[List[str]]:
        """Get keywords from analyzer_agent if LLM is available.
        
        Args:
            model_info: Model architecture information
            
        Returns:
            List of keywords or None if LLM unavailable
        """
        if self.llm is None:
            return None
        
        try:
            from model_opt.agent.analyzer_agent import ResearchAgent
            agent = ResearchAgent(self.llm)
            keywords = agent.generate_keywords(model_info)
            return keywords if keywords else None
        except Exception as e:
            print(f"⚠️  Failed to get LLM keywords: {e}")
            return None
    
    async def search(
        self,
        model_info: Dict[str, Any],
        max_papers: int = 50,
        days: int = 120,
        min_keyword_matches: int = 2
    ) -> List[Dict[str, Any]]:
        """Parallel search across all sources with filtering.
        
        Args:
            model_info: Model architecture details (type, layers, params)
            max_papers: Maximum papers to retrieve per source
            days: Number of days to look back (default: 120)
            min_keyword_matches: Minimum keyword matches required (default: 2)
            
        Returns:
            List of paper metadata with relevance scores, filtered and ranked
        """
        # Get LLM-generated keywords if available
        llm_keywords = self._get_llm_keywords(model_info)
        
        # Combine base keywords with LLM keywords
        all_keywords = self.base_keywords.copy()
        if llm_keywords:
            # Add LLM keywords, avoiding duplicates
            for kw in llm_keywords:
                kw_lower = kw.lower().strip()
                if kw_lower and kw_lower not in all_keywords:
                    all_keywords.append(kw_lower)
        
        # Build search queries
        queries = self._build_queries(model_info, llm_keywords)
        
        # Search all sources in parallel
        tasks = []
        
        # ArXiv search (daily crawl or regular search)
        tasks.append(self._search_arxiv(llm_keywords, max_papers))
        
        # Semantic Scholar search
        for query in queries[:3]:  # Limit to 3 queries per source
            tasks.append(self._search_semantic_scholar(query, max_papers))
        
        # HuggingFace search
        for query in queries[:3]:
            tasks.append(self._search_huggingface(query, max_papers))
        
        # Wait for all searches to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        papers = []
        for result in results:
            if isinstance(result, Exception):
                continue
            if isinstance(result, list):
                papers.extend(result)
        
        # Deduplicate by title
        papers = self._deduplicate(papers)
        
        # Apply filters
        filtered_papers = self.paper_filter.apply_filters(
            papers,
            keywords=all_keywords,
            days=days,
            min_keyword_matches=min_keyword_matches
        )
        
        # Score relevance
        filtered_papers = self._score_relevance(filtered_papers, model_info)
        
        # Final ranking and limit
        filtered_papers.sort(
            key=lambda x: (
                x.get('venue_quality_score', 0.0),
                x.get('relevance_score', 0.0),
                x.get('keyword_matches', 0)
            ),
            reverse=True
        )
        
        return filtered_papers[:max_papers]
    
    def _build_queries(
        self,
        model_info: Dict[str, Any],
        llm_keywords: Optional[List[str]]
    ) -> List[str]:
        """Build search queries from model info and keywords.
        
        Args:
            model_info: Model architecture information
            llm_keywords: Optional LLM-generated keywords
            
        Returns:
            List of search query strings
        """
        arch_type = model_info.get('architecture_type', 'Unknown')
        family = model_info.get('model_family', '')
        
        queries = [
            f"{arch_type} optimization techniques 2024",
            f"{arch_type} quantization methods",
            f"{arch_type} pruning strategies",
            f"post-training optimization {arch_type}",
        ]
        
        if family:
            queries.append(f"{family} optimization")
        
        # Add LLM keywords as queries
        if llm_keywords:
            queries.extend(llm_keywords[:5])  # Limit to 5 additional queries
        
        return queries
    
    async def _search_arxiv(
        self,
        llm_keywords: Optional[List[str]],
        max_papers: int
    ) -> List[Dict[str, Any]]:
        """Search ArXiv with daily crawl or regular search.
        
        Args:
            llm_keywords: Optional LLM-generated keywords
            max_papers: Maximum papers to fetch
            
        Returns:
            List of paper metadata
        """
        try:
            # Try daily crawl first (only gets new papers)
            papers = await self.arxiv_crawler.crawl_daily(
                max_results=max_papers,
                llm_keywords=llm_keywords
            )
            
            # If no new papers, do regular search
            if not papers:
                query = self.arxiv_crawler._build_query(llm_keywords=llm_keywords)
                papers = await self.arxiv_crawler.search(query, max_results=max_papers)
            
            return papers
        except Exception as e:
            print(f"❌ ArXiv search failed: {e}")
            return []
    
    async def _search_semantic_scholar(
        self,
        query: str,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Search Semantic Scholar.
        
        Args:
            query: Search query
            max_results: Maximum results
            
        Returns:
            List of paper metadata
        """
        try:
            return await self.semantic_scholar.search(query, max_results=max_results)
        except Exception as e:
            print(f"❌ Semantic Scholar search failed: {e}")
            return []
    
    async def _search_huggingface(
        self,
        query: str,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Search HuggingFace.
        
        Args:
            query: Search query
            max_results: Maximum results
            
        Returns:
            List of model metadata
        """
        try:
            return await self.huggingface.search(query, max_results=max_results)
        except Exception as e:
            print(f"❌ HuggingFace search failed: {e}")
            return []
    
    def _deduplicate(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate papers by title.
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            Deduplicated list
        """
        seen_titles = set()
        deduplicated = []
        
        for paper in papers:
            title = paper.get('title', '').lower().strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                deduplicated.append(paper)
        
        return deduplicated
    
    def _score_relevance(
        self,
        papers: List[Dict[str, Any]],
        model_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Score papers based on relevance to model architecture.
        
        Args:
            papers: List of paper dictionaries
            model_info: Model architecture information
            
        Returns:
            Papers with relevance_score added
        """
        arch_type = model_info.get('architecture_type', '').lower()
        
        for paper in papers:
            score = 0.5  # Base score
            
            title = paper.get('title', '').lower()
            abstract = paper.get('abstract', '').lower() or paper.get('content', '').lower()
            text = f"{title} {abstract}"
            
            # Architecture match bonus
            if arch_type and arch_type in text:
                score += 0.3
            
            # Keywords
            keywords = ['optimization', 'quantization', 'pruning', 'compression', 'efficient']
            for keyword in keywords:
                if keyword in text:
                    score += 0.1
            
            # Citations
            citations = paper.get('citations', 0)
            if citations > 0:
                score += min(citations / 100, 0.2)  # Max 0.2 for citations
            
            # Combine with venue quality score
            venue_score = paper.get('venue_quality_score', 0.5)
            paper['relevance_score'] = min((score + venue_score) / 2, 1.0)  # Average and cap at 1.0
        
        return papers

