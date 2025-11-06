"""Metadata extraction from arXiv API responses."""
from typing import Dict, List, Any, Optional
from datetime import datetime
import re


class MetadataExtractor:
    """Extract and normalize metadata from arXiv API responses."""
    
    def extract_arxiv_metadata(self, result: Any) -> Dict[str, Any]:
        """Extract metadata from a single arXiv result.
        
        Args:
            result: arxiv.Result object from arxiv library
            
        Returns:
            Dictionary with extracted metadata:
            - arxiv_id: arXiv paper ID
            - title: Paper title
            - authors: List of author names
            - abstract: Abstract text
            - submission_date: Submission date (datetime)
            - pdf_url: URL to PDF
            - published: Published date (datetime)
            - categories: List of arXiv categories
        """
        try:
            # Extract arXiv ID from entry_id
            entry_id = result.entry_id
            arxiv_id = entry_id.split('/')[-1] if '/' in entry_id else entry_id
            
            # Normalize dates
            submission_date = self.normalize_date(result.published)
            published_date = self.normalize_date(result.published) if hasattr(result, 'published') else None
            
            metadata = {
                'arxiv_id': arxiv_id,
                'title': result.title,
                'authors': [author.name for author in result.authors],
                'abstract': result.summary,
                'submission_date': submission_date,
                'published': published_date or submission_date,
                'pdf_url': result.pdf_url if hasattr(result, 'pdf_url') else f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                'url': entry_id,
                'categories': result.categories if hasattr(result, 'categories') else [],
                'content': result.summary,  # For compatibility
                'source': 'arxiv',
            }
            
            return metadata
        except Exception as e:
            # Return minimal metadata on error
            return {
                'arxiv_id': '',
                'title': str(result.title) if hasattr(result, 'title') else 'Unknown',
                'authors': [],
                'abstract': '',
                'submission_date': None,
                'published': None,
                'pdf_url': '',
                'url': '',
                'categories': [],
                'content': '',
                'source': 'arxiv',
                'error': str(e)
            }
    
    def extract_batch(self, arxiv_results: List[Any]) -> List[Dict[str, Any]]:
        """Extract metadata from multiple arXiv results.
        
        Args:
            arxiv_results: List of arxiv.Result objects
            
        Returns:
            List of metadata dictionaries
        """
        return [self.extract_arxiv_metadata(result) for result in arxiv_results]
    
    def normalize_date(self, date_obj: Any) -> Optional[datetime]:
        """Normalize date to datetime object.
        
        Args:
            date_obj: Date object (datetime, string, or None)
            
        Returns:
            datetime object or None
        """
        if date_obj is None:
            return None
        
        if isinstance(date_obj, datetime):
            return date_obj
        
        if isinstance(date_obj, str):
            try:
                # Try common formats
                formats = [
                    '%Y-%m-%d',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%d %H:%M:%S',
                ]
                for fmt in formats:
                    try:
                        return datetime.strptime(date_obj, fmt)
                    except ValueError:
                        continue
            except Exception:
                pass
        
        return None
    
    def extract_venue_from_arxiv(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Try to extract venue information from arXiv metadata.
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            Venue name if found, None otherwise
        """
        # arXiv doesn't directly provide venue, but we can check comments/journal_ref
        # This is a placeholder - actual venue extraction would need additional API calls
        title = metadata.get('title', '').lower()
        abstract = metadata.get('abstract', '').lower()
        
        # Check for common venue mentions in title/abstract
        venues = {
            'cvpr': 'CVPR',
            'iccv': 'ICCV',
            'eccv': 'ECCV',
            'neurips': 'NeurIPS',
            'icml': 'ICML',
            'aaai': 'AAAI',
            'ijcv': 'IJCV',
            'tpami': 'TPAMI',
        }
        
        text = f"{title} {abstract}"
        for venue_key, venue_name in venues.items():
            if venue_key in text:
                return venue_name
        
        return None

