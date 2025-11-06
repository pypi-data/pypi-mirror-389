"""Agents and research tools."""

try:
    from .tools.research import ParallelResearchCrawler as ParallelPaperSearch
except ImportError:
    try:
        from .tools.scraper import ParallelPaperSearch
    except ImportError:
        ParallelPaperSearch = None

try:
	from .analyzer_agent import ResearchAgent
	_AGENTS_AVAILABLE = True
except ImportError:
	_AGENTS_AVAILABLE = False
	ResearchAgent = None

__all__ = [
	"ParallelPaperSearch",
	"ResearchAgent",
]


