"""
Test script to demonstrate scraper.py integration with model_loader.py
This shows how model analysis results feed into research search.

Usage: python tests/test_scraper_integration.py
"""
import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
	from model_opt.agent.tools.research import ParallelResearchCrawler as ParallelPaperSearch
except ImportError:
	try:
		from model_opt.agent.tools.scraper import ParallelPaperSearch
	except ImportError:
		print("Warning: Could not import research crawler (expected in development)")
		ParallelPaperSearch = None

from model_opt.agent.analyzer import analyze_papers


def create_sample_analysis_output():
	"""
	Simulate the analysis output that model_loader.py would produce.
	This represents PHASE 1: MODEL ANALYSIS results.
	"""
	return {
		'model_name': 'ResNet50',
		'params': 25500000,  # 25.5M params
		'model_size_mb': 98.0,
		'architecture_type': 'CNN',
		'model_family': 'ResNet',
		'layer_types': {
			'Conv2d': 49,
			'BatchNorm2d': 49,
			'ReLU': 48,
			'MaxPool2d': 1,
			'Linear': 1
		},
		'bottleneck_count': 16,
		'framework': 'PYTORCH',
		'hardware': 'NVIDIA RTX 3090 (24GB VRAM)',
		'inference_ms': 42.3,
		'accuracy': 76.1,
		'optimization_potential': 'HIGH',  # Based on bottleneck analysis
		'target_techniques': ['pruning', 'quantization', 'fusion']
	}


async def test_scraper_with_model_info():
	"""Test the scraper using model analysis results."""
	print("=" * 70)
	print("LIVE TEST: Model Analysis -> Research Search")
	print("=" * 70)
	
	# Step 1: Simulate model analysis
	print("\n[STEP 1] Model Analysis Output")
	print("-" * 70)
	print("This is what model_loader.py would produce:")
	print()
	
	model_info = create_sample_analysis_output()
	
	# Display analysis results
	print("PHASE 1: MODEL ANALYSIS")
	print("-" * 62)
	print(f"|- Framework: {model_info['framework']}")
	print(f"|- Model: {model_info['model_name']} ({model_info['params']/1e6:.1f}M params, {model_info['model_size_mb']:.1f}MB)")
	print(f"|- Architecture: {model_info['architecture_type']}")
	
	layer_types = model_info['layer_types']
	layer_str = ', '.join([f"{name} ({count})" for name, count in layer_types.items()])
	print(f"|- Layer Types: {layer_str}")
	print(f"|- Bottleneck Layers: {model_info['bottleneck_count']} (potential pruning targets)")
	print(f"|- Hardware: {model_info['hardware']}")
	print(f"+- Baseline Performance: {model_info['inference_ms']}ms inference, {model_info['accuracy']:.1f}% accuracy")
	print()
	
	if not ParallelPaperSearch:
		print("WARNING: Scraper not available (install dependencies)")
		return
	
	searcher = ParallelPaperSearch()
	
	# Convert model_info to format expected by scraper
	scraper_model_info = {
		'architecture_type': model_info['architecture_type'],
		'model_family': model_info.get('model_family', 'Unknown'),
		'layer_types': model_info['layer_types'],
		'params': model_info['params']
	}
	
	# Show generated queries (if method exists)
	print("[STEP 2] Generating Research Queries")
	print("-" * 70)
	# Build queries using internal method (for demo purposes)
	if hasattr(searcher, '_build_queries'):
		queries = searcher._build_queries(scraper_model_info, None)
	else:
		# Fallback: generate sample queries
		queries = [
			f"{scraper_model_info.get('architecture_type', 'CNN')} optimization techniques 2024",
			f"{scraper_model_info.get('architecture_type', 'CNN')} quantization methods",
			f"{scraper_model_info.get('architecture_type', 'CNN')} pruning strategies",
		]
	print(f"Generated {len(queries)} search queries:")
	for i, query in enumerate(queries[:5], 1):  # Show first 5
		print(f"  {i}. {query}")
	print()
	
	# Step 3: Actually run the search
	print("[STEP 3] Running LIVE Search Across Sources")
	print("-" * 70)
	print("Searching ArXiv, Semantic Scholar, GitHub, HuggingFace...")
	print("(Note: Rate limits apply - may take a moment)")
	print()
	
	try:
		# Run search with reduced max_papers for faster demo
		results = await searcher.search(scraper_model_info, max_papers=10)
		
		if not results:
			print("ERROR: No results returned. Possible reasons:")
			print("   - Rate limit exceeded")
			print("   - Network issues")
			print("   - API changes")
			print()
			print("Trying individual searchers to debug...")
			
			# Try individual searchers
			try:
				from model_opt.agent.tools.research import ArXivCrawler
				arxiv_searcher = ArXivCrawler()
			except ImportError:
				try:
					from model_opt.agent.tools.scraper import ArXivSearcher
					arxiv_searcher = ArXivSearcher()
				except ImportError:
					print("ArXiv searcher not available")
					return
			try:
				# ArXivCrawler uses different interface - try both
				if hasattr(arxiv_searcher, 'search'):
					arxiv_results = await arxiv_searcher.search(queries[0], max_results=3)
				elif hasattr(arxiv_searcher, 'search_with_keywords'):
					arxiv_results = await arxiv_searcher.search_with_keywords([queries[0]], max_results=3)
				else:
					# Try crawl_daily as fallback
					arxiv_results = await arxiv_searcher.crawl_daily(max_results=3)
				
				print(f"OK: ArXiv working: Found {len(arxiv_results)} papers")
				if arxiv_results:
					print(f"   Example: {arxiv_results[0].get('title', 'N/A')[:60]}...")
			except Exception as e:
				print(f"ERROR: ArXiv failed: {e}")
			
			return
		
		# Display results
		print(f"OK: Found {len(results)} relevant papers/repos")
		print()
		print("[STEP 4] Top Results")
		print("-" * 70)
		
		for i, paper in enumerate(results[:5], 1):  # Show top 5
			print(f"\n{i}. {paper.get('title', 'No title')[:70]}")
			print(f"   Source: {paper.get('source', 'unknown')}")
			print(f"   Relevance: {paper.get('relevance_score', 0):.2f}")
			
			if 'url' in paper and paper['url']:
				url = paper['url']
				if len(url) > 60:
					url = url[:60] + '...'
				print(f"   URL: {url}")
			
			if 'citations' in paper:
				print(f"   Citations: {paper.get('citations', 0)}")
			elif 'stars' in paper:
				print(f"   Stars: {paper.get('stars', 0)}")
			
			# Show content preview
			content = paper.get('content', '')
			if content:
				preview = content[:150].replace('\n', ' ')
				if len(content) > 150:
					preview += '...'
				print(f"   Content: {preview}")
		
		print(f"\n[COMPLETE] Retrieved {len(results)} total results")
		
		# PHASE 3: Analyze and extract techniques
		print("\n[STEP 5] PHASE 3: PAPER ANALYSIS & TECHNIQUE EXTRACTION")
		print("-" * 70)
		analyze_papers(results, scraper_model_info, top_n=15)
		
	except Exception as e:
		print(f"ERROR: Error during search: {e}")
		print("\nPossible issues:")
		print("  - Network connectivity")
		print("  - Rate limiting from APIs")
		print("  - Missing dependencies")
		import traceback
		traceback.print_exc()


def main():
	"""Run the demo."""
	asyncio.run(test_scraper_with_model_info())


if __name__ == '__main__':
	main()

