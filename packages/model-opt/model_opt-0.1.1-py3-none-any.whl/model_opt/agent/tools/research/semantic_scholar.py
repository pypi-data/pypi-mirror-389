"""Semantic Scholar API searcher with content extraction."""
import aiohttp
from typing import List, Dict
import asyncio


class SemanticScholarSearcher:
    """Semantic Scholar API searcher with content extraction."""
    
    async def search(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search Semantic Scholar API.
        
        Args:
            query: Search query string
            max_results: Maximum results to return
            
        Returns:
            List of paper dictionaries with metadata
        """
        async with aiohttp.ClientSession() as session:
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                'query': query,
                'limit': max_results,
                'fields': 'title,authors,abstract,year,citationCount,url,venue'
            }
            
            try:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        print(f"⚠️  Semantic Scholar API returned status {response.status}")
                        return []
                    
                    data = await response.json()
                    
                    papers = []
                    for paper in data.get('data', []):
                        papers.append({
                            'title': paper.get('title', ''),
                            'authors': [a.get('name', '') for a in paper.get('authors', [])],
                            'abstract': paper.get('abstract', ''),
                            'url': paper.get('url', ''),
                            'citations': paper.get('citationCount', 0),
                            'year': paper.get('year'),
                            'venue': paper.get('venue', ''),
                            'content': paper.get('abstract', ''),  # Abstract as content
                            'source': 'semantic_scholar',
                        })
                    
                    return papers
            except asyncio.TimeoutError:
                print("⚠️  Semantic Scholar API request timed out")
                return []
            except Exception as e:
                print(f"❌ Error searching Semantic Scholar: {e}")
                return []

