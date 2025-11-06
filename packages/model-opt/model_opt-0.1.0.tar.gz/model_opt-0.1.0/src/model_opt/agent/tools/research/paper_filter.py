"""Paper filtering by date range, venue quality, and keyword relevance."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re


class PaperFilter:
    """Filter papers by date range, venue quality, and keyword relevance."""
    
    # High-quality venues (case-insensitive)
    HIGH_QUALITY_VENUES = {
        'cvpr', 'iccv', 'eccv', 'neurips', 'nips', 'icml', 'aaai',
        'ijcv', 'tpami', 'iclr', 'acl', 'emnlp', 'naacl'
    }
    
    # Venue keywords that appear in titles/abstracts
    VENUE_KEYWORDS = {
        'cvpr': ['cvpr', 'computer vision and pattern recognition'],
        'iccv': ['iccv', 'international conference on computer vision'],
        'eccv': ['eccv', 'european conference on computer vision'],
        'neurips': ['neurips', 'nips', 'neural information processing systems'],
        'icml': ['icml', 'international conference on machine learning'],
        'aaai': ['aaai', 'association for the advancement of artificial intelligence'],
    }
    
    def filter_by_date(
        self,
        papers: List[Dict[str, Any]],
        days: int = 120
    ) -> List[Dict[str, Any]]:
        """Filter papers by submission date (last N days).
        
        Args:
            papers: List of paper metadata dictionaries
            days: Number of days to look back (default: 120)
            
        Returns:
            Filtered list of papers within date range
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        filtered = []
        for paper in papers:
            submission_date = paper.get('submission_date') or paper.get('published')
            
            if submission_date is None:
                # If no date, include it (better than excluding)
                filtered.append(paper)
                continue
            
            if isinstance(submission_date, str):
                # Try to parse string date
                try:
                    # Handle ISO format with or without timezone
                    if submission_date.endswith('Z'):
                        submission_date = datetime.fromisoformat(submission_date.replace('Z', '+00:00'))
                    else:
                        submission_date = datetime.fromisoformat(submission_date)
                except Exception:
                    # If parsing fails, include the paper
                    filtered.append(paper)
                    continue
            
            if isinstance(submission_date, datetime):
                # Normalize both datetimes to be timezone-aware or both naive
                # Make cutoff_date timezone-aware if submission_date is aware
                if submission_date.tzinfo is not None:
                    # submission_date is timezone-aware
                    if cutoff_date.tzinfo is None:
                        # cutoff_date is naive, make it timezone-aware (UTC)
                        from datetime import timezone
                        cutoff_date = cutoff_date.replace(tzinfo=timezone.utc)
                else:
                    # submission_date is naive
                    if cutoff_date.tzinfo is not None:
                        # cutoff_date is aware, make it naive
                        cutoff_date = cutoff_date.replace(tzinfo=None)
                
                if submission_date >= cutoff_date:
                    filtered.append(paper)
            else:
                # Unknown date format, include it
                filtered.append(paper)
        
        return filtered
    
    def filter_by_keywords(
        self,
        papers: List[Dict[str, Any]],
        keywords: List[str],
        min_matches: int = 2
    ) -> List[Dict[str, Any]]:
        """Filter papers by keyword matches in title/abstract.
        
        Args:
            papers: List of paper metadata dictionaries
            keywords: List of keywords to search for
            min_matches: Minimum number of keyword matches required
            
        Returns:
            Filtered list of papers with sufficient keyword matches
        """
        if not keywords:
            return papers
        
        # Normalize keywords to lowercase
        keywords_lower = [kw.lower() for kw in keywords if kw]
        
        filtered = []
        for paper in papers:
            title = paper.get('title', '').lower()
            abstract = paper.get('abstract', '').lower() or paper.get('content', '').lower()
            text = f"{title} {abstract}"
            
            # Count keyword matches
            matches = sum(1 for kw in keywords_lower if kw in text)
            
            if matches >= min_matches:
                paper['keyword_matches'] = matches
                filtered.append(paper)
        
        return filtered
    
    def score_venue_quality(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score papers based on venue quality.
        
        Args:
            papers: List of paper metadata dictionaries
            
        Returns:
            Papers with venue_quality_score added
        """
        for paper in papers:
            score = 0.5  # Base score
            
            title = paper.get('title', '').lower()
            abstract = paper.get('abstract', '').lower() or paper.get('content', '').lower()
            text = f"{title} {abstract}"
            
            # Check for high-quality venue mentions
            for venue, keywords in self.VENUE_KEYWORDS.items():
                if any(kw in text for kw in keywords):
                    score += 0.3  # Boost for top-tier venues
                    paper['detected_venue'] = venue.upper()
                    break
            
            # Check categories for arXiv
            categories = paper.get('categories', [])
            if any('cs.CV' in cat or 'cs.LG' in cat for cat in categories):
                score += 0.1
            
            paper['venue_quality_score'] = min(score, 1.0)  # Cap at 1.0
        
        return papers
    
    def apply_filters(
        self,
        papers: List[Dict[str, Any]],
        keywords: Optional[List[str]] = None,
        days: int = 120,
        min_keyword_matches: int = 2,
        require_venue: bool = False
    ) -> List[Dict[str, Any]]:
        """Apply all filters to papers.
        
        Args:
            papers: List of paper metadata dictionaries
            keywords: Optional list of keywords for filtering
            days: Number of days to look back (default: 120)
            min_keyword_matches: Minimum keyword matches required
            require_venue: If True, only include papers with detected venues
            
        Returns:
            Filtered and scored list of papers
        """
        # Step 1: Filter by date
        filtered = self.filter_by_date(papers, days=days)
        
        # Step 2: Filter by keywords if provided
        if keywords:
            filtered = self.filter_by_keywords(filtered, keywords, min_matches=min_keyword_matches)
        
        # Step 3: Score venue quality
        filtered = self.score_venue_quality(filtered)
        
        # Step 4: Optional venue requirement
        if require_venue:
            filtered = [p for p in filtered if p.get('detected_venue')]
        
        # Step 5: Sort by venue quality score (prefer high-quality venues)
        filtered.sort(key=lambda x: x.get('venue_quality_score', 0.0), reverse=True)
        
        return filtered

