"""ArXiv crawler with daily paper discovery and exponential backoff."""
import asyncio
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

try:
    import arxiv
    _ARXIV_AVAILABLE = True
except ImportError:
    _ARXIV_AVAILABLE = False
    arxiv = None

from .metadata_extractor import MetadataExtractor


class ArXivCrawler:
    """ArXiv crawler with exponential backoff and daily discovery."""
    
    # Base query for optimization papers
    BASE_QUERY = "cat:cs.CV OR cat:cs.LG AND (quantization OR pruning OR distillation OR compression)"
    
    def __init__(
        self,
        llm=None,
        last_crawl_date: Optional[datetime] = None,
        state_file: Optional[str] = None
    ):
        """Initialize ArXiv crawler.
        
        Args:
            llm: Optional LLM client for generating keywords
            last_crawl_date: Last crawl date (for daily discovery)
            state_file: Path to file storing last crawl date
        """
        if not _ARXIV_AVAILABLE:
            raise ImportError("arxiv library is required. Install with: pip install arxiv")
        
        self.llm = llm
        self.last_crawl_date = last_crawl_date
        self.state_file = state_file or ".arxiv_crawler_state.json"
        self.extractor = MetadataExtractor()
        
        # Load last crawl date if available
        if self.last_crawl_date is None:
            self.last_crawl_date = self._load_last_crawl_date()
    
    def _load_last_crawl_date(self) -> Optional[datetime]:
        """Load last crawl date from state file."""
        try:
            state_path = Path(self.state_file)
            if state_path.exists():
                with open(state_path, 'r') as f:
                    state = json.load(f)
                    date_str = state.get('last_crawl_date')
                    if date_str:
                        return datetime.fromisoformat(date_str)
        except Exception:
            pass
        return None
    
    def _save_last_crawl_date(self, date: datetime):
        """Save last crawl date to state file."""
        try:
            state_path = Path(self.state_file)
            state = {
                'last_crawl_date': date.isoformat()
            }
            with open(state_path, 'w') as f:
                json.dump(state, f)
        except Exception:
            pass
    
    def _build_query(
        self,
        base_keywords: Optional[List[str]] = None,
        llm_keywords: Optional[List[str]] = None
    ) -> str:
        """Build arXiv query from base and LLM-generated keywords.
        
        Args:
            base_keywords: Base keywords (from BASE_QUERY)
            llm_keywords: LLM-generated keywords from analyzer_agent
            
        Returns:
            Combined arXiv query string
        """
        # Start with base query
        query_parts = [self.BASE_QUERY]
        
        # Add LLM keywords if available
        if llm_keywords:
            # Filter and format keywords for arXiv query
            formatted_keywords = []
            for kw in llm_keywords[:10]:  # Limit to 10 keywords
                kw_clean = kw.strip().lower()
                # Remove common stopwords and format
                if kw_clean and len(kw_clean) > 3:
                    formatted_keywords.append(kw_clean)
            
            if formatted_keywords:
                # Combine keywords with OR
                kw_query = " OR ".join(formatted_keywords[:5])  # Limit query length
                query_parts.append(f"AND ({kw_query})")
        
        return " ".join(query_parts)
    
    async def _fetch_with_backoff(
        self,
        query: str,
        max_results: int = 100,
        max_retries: int = 5
    ) -> List[Any]:
        """Fetch papers with exponential backoff retry logic.
        
        Args:
            query: arXiv search query
            max_results: Maximum results to fetch
            max_retries: Maximum number of retries
            
        Returns:
            List of arxiv.Result objects
        """
        delay = 1.0  # Start with 1 second delay
        
        for attempt in range(max_retries):
            try:
                # Run arxiv search in thread pool (it's synchronous)
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(
                    None,
                    self._sync_search,
                    query,
                    max_results
                )
                return results
                
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"⚠️  ArXiv search failed after {max_retries} attempts: {e}")
                    return []
                
                # Exponential backoff: 1s, 2s, 4s, 8s, 16s (capped at 60s)
                delay = min(delay * 2, 60.0)
                print(f"⚠️  ArXiv search failed (attempt {attempt + 1}/{max_retries}), retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
        
        return []
    
    def _sync_search(self, query: str, max_results: int) -> List[Any]:
        """Synchronous arXiv search (runs in thread pool).
        
        Args:
            query: arXiv search query
            max_results: Maximum results
            
        Returns:
            List of arxiv.Result objects
        """
        if not _ARXIV_AVAILABLE or arxiv is None:
            raise ImportError("arxiv library is required. Install with: pip install arxiv")
        
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        return list(search.results())
    
    async def crawl_daily(
        self,
        max_results: int = 100,
        llm_keywords: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Daily crawl for new papers since last crawl.
        
        Args:
            max_results: Maximum results to fetch
            llm_keywords: Optional LLM-generated keywords from analyzer_agent
            
        Returns:
            List of new paper metadata dictionaries
        """
        # Build query
        query = self._build_query(llm_keywords=llm_keywords)
        
        # Fetch papers
        print(f"🔍 Crawling arXiv with query: {query[:100]}...")
        arxiv_results = await self._fetch_with_backoff(query, max_results=max_results)
        
        if not arxiv_results:
            print("⚠️  No papers found")
            return []
        
        # Extract metadata
        papers = self.extractor.extract_batch(arxiv_results)
        
        # Filter to only new papers (since last crawl)
        if self.last_crawl_date:
            new_papers = []
            for paper in papers:
                paper_date = paper.get('submission_date') or paper.get('published')
                if paper_date and isinstance(paper_date, datetime):
                    if paper_date > self.last_crawl_date:
                        new_papers.append(paper)
                else:
                    # Include papers without dates (better than excluding)
                    new_papers.append(paper)
            papers = new_papers
        
        # Update last crawl date
        if papers:
            latest_date = max(
                (p.get('submission_date') or p.get('published') or datetime.now())
                for p in papers
                if isinstance(p.get('submission_date') or p.get('published'), datetime)
            )
            if isinstance(latest_date, datetime):
                self._save_last_crawl_date(latest_date)
                self.last_crawl_date = latest_date
        
        print(f"✓ Found {len(papers)} new papers")
        return papers
    
    async def search(
        self,
        query: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """General search (not daily-specific).
        
        Args:
            query: arXiv search query
            max_results: Maximum results to fetch
            
        Returns:
            List of paper metadata dictionaries
        """
        arxiv_results = await self._fetch_with_backoff(query, max_results=max_results)
        
        if not arxiv_results:
            return []
        
        return self.extractor.extract_batch(arxiv_results)
    
    async def search_with_keywords(
        self,
        keywords: List[str],
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Search using keywords (builds query automatically).
        
        Args:
            keywords: List of search keywords
            max_results: Maximum results to fetch
            
        Returns:
            List of paper metadata dictionaries
        """
        query = self._build_query(llm_keywords=keywords)
        return await self.search(query, max_results=max_results)

