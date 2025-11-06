"""HuggingFace model searcher with model card extraction."""
import aiohttp
from typing import List, Dict
import asyncio


class HuggingFaceSearcher:
    """HuggingFace model searcher with model card extraction."""
    
    async def search(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search HuggingFace models.
        
        Args:
            query: Search query string
            max_results: Maximum results to return
            
        Returns:
            List of model dictionaries with metadata
        """
        async with aiohttp.ClientSession() as session:
            url = "https://huggingface.co/api/models"
            params = {'search': query, 'limit': max_results}
            
            try:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        print(f"⚠️  HuggingFace API returned status {response.status}")
                        return []
                    
                    data = await response.json()
                    models = []
                    for model in data:
                        model_id = model.get('id', '')
                        model_info = {
                            'title': model_id,
                            'description': model.get('description', ''),
                            'url': f"https://huggingface.co/{model_id}",
                            'downloads': model.get('downloads', 0),
                            'source': 'huggingface',
                        }
                        
                        # Fetch model card content
                        model_info['content'] = await self._fetch_model_card(session, model_id)
                        
                        models.append(model_info)
                    return models
            except asyncio.TimeoutError:
                print("⚠️  HuggingFace API request timed out")
                return []
            except Exception as e:
                print(f"❌ Error searching HuggingFace: {e}")
                return []
    
    async def _fetch_model_card(self, session: aiohttp.ClientSession, model_id: str) -> str:
        """Fetch model card content from HuggingFace.
        
        Args:
            session: aiohttp ClientSession
            model_id: HuggingFace model ID
            
        Returns:
            Model card content as string
        """
        model_card_url = f"https://huggingface.co/{model_id}/raw/main/README.md"
        
        try:
            async with session.get(model_card_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    content = await response.text()
                    return content
        except Exception:
            pass
        
        return ""

