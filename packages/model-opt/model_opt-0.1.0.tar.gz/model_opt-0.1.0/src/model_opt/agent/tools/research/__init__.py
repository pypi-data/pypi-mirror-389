"""Parallel research crawler for model optimization papers."""
from .arxiv_crawler import ArXivCrawler
from .paper_filter import PaperFilter
from .metadata_extractor import MetadataExtractor
from .scheduler import ResearchScheduler
from .semantic_scholar import SemanticScholarSearcher
from .huggingface import HuggingFaceSearcher
from .parallel_crawler import ParallelResearchCrawler

# Backward compatibility alias
ParallelPaperSearch = ParallelResearchCrawler

__all__ = [
    'ArXivCrawler',
    'PaperFilter',
    'MetadataExtractor',
    'ResearchScheduler',
    'SemanticScholarSearcher',
    'HuggingFaceSearcher',
    'ParallelResearchCrawler',
    'ParallelPaperSearch',  # Backward compatibility
]

