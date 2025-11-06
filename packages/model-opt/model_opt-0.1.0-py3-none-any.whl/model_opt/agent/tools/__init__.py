"""Research tools for model optimization."""
# Try to import from new research module, fallback to old scraper
try:
	from .research import (
		ParallelResearchCrawler,
		ParallelPaperSearch,  # Backward compatibility alias
		SemanticScholarSearcher,
		HuggingFaceSearcher,
		ArXivCrawler,
	)
	_ARXIV_SEARCHER = ArXivCrawler
except ImportError:
	# Fallback to old scraper if research module not available
	try:
		from .scraper import (
			ParallelPaperSearch,
			ArXivSearcher,
			GitHubSearcher,
			SemanticScholarSearcher,
			GoogleScholarSearcher,
			HuggingFaceSearcher,
		)
		ParallelResearchCrawler = ParallelPaperSearch  # Alias for compatibility
		_ARXIV_SEARCHER = ArXivSearcher
	except ImportError:
		# If neither available, create dummy classes
		ParallelPaperSearch = None
		ParallelResearchCrawler = None
		SemanticScholarSearcher = None
		HuggingFaceSearcher = None
		_ARXIV_SEARCHER = None

__all__ = [
	"ParallelPaperSearch",
	"ParallelResearchCrawler",
	"SemanticScholarSearcher",
	"HuggingFaceSearcher",
]
