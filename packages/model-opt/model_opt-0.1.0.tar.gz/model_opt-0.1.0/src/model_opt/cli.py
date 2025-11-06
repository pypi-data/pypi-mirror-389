"""Main CLI entry point for model-opt."""
import argparse
import sys


def create_parser():
	"""Create argument parser for model-opt CLI."""
	parser = argparse.ArgumentParser(
		prog='model-opt',
		description='Model optimization toolkit'
	)
	
	# Add --log-file parameter to root parser only
	parser.add_argument(
		'--log-file',
		type=str,
		help='Path to log file for structured logging'
	)
	
	subparsers = parser.add_subparsers(dest='command', help='Commands')
	
	# Optimize command
	optimize_parser = subparsers.add_parser('optimize', help='Optimize a model')
	optimize_parser.add_argument('model_path', help='Path to model')
	optimize_parser.add_argument('--test-dataset', required=True, help='Path to test dataset')
	optimize_parser.add_argument('--test-script', required=True, help='Path to test/inference script')
	
	# Mode selection
	optimize_parser.add_argument('--agent', action='store_true', help='Enable agentic experimentation')
	optimize_parser.add_argument('--research', action='store_true', help='Enable research-driven mode (web search)')
	optimize_parser.add_argument('--interactive', action='store_true', help='Interactive prompts')
	optimize_parser.add_argument('--config', help='Load preset config')
	
	# Manual techniques
	optimize_parser.add_argument('--quantize', action='store_true', help='Apply quantization')
	optimize_parser.add_argument('--prune', action='store_true', help='Apply pruning')
	optimize_parser.add_argument('--distill', action='store_true', help='Apply distillation')
	optimize_parser.add_argument('--fuse', action='store_true', help='Auto-fuse layers')
	
	# Technique backends & knobs
	optimize_parser.add_argument('--quant-method', choices=['int8_weight_only', 'int8_dynamic'], default='int8_weight_only', help='Quantization method (TorchAO)')
	
	optimize_parser.add_argument('--prune-backend', choices=['torch-pruning', 'basic'], default='torch-pruning', help='Pruning backend')
	optimize_parser.add_argument('--prune-amount', type=float, default=0.5, help='Fraction to prune (0-1)')
	optimize_parser.add_argument('--prune-criterion', choices=['magnitude', 'taylor', 'group_norm', 'l1'], default='magnitude', help='Pruning criterion (magnitude/taylor/group_norm for torch-pruning, l1 for basic)')
	
	# Constraints
	optimize_parser.add_argument('--target-speed', help='Speed target (e.g., 3x)')
	optimize_parser.add_argument('--target-size', help='Size target')
	optimize_parser.add_argument('--max-accuracy-drop', help='Max accuracy drop (e.g., 5%)')
	
	# Hardware
	optimize_parser.add_argument('--device', help='Target device')
	optimize_parser.add_argument('--benchmark', action='store_true', help='Run performance benchmark')
	optimize_parser.add_argument('--validate', action='store_true', help='Accuracy validation')
	
	# Agent options
	optimize_parser.add_argument('--experiments', type=int, default=8, help='Number of variants (default: 8)')
	optimize_parser.add_argument('--auto-select', action='store_true', help='Skip user confirmation')
	optimize_parser.add_argument('--parallel-gpus', action='store_true', help='Parallel execution')
	optimize_parser.add_argument('--budget', help='Time budget')
	
	# Research options
	optimize_parser.add_argument('--search-sources', help='Search sources')
	optimize_parser.add_argument('--max-papers', type=int, default=50, help='Max papers to analyze (default: 50)')
	optimize_parser.add_argument('--min-citations', type=int, help='Min citation threshold')
	optimize_parser.add_argument('--year', help='Filter by publication year')
	optimize_parser.add_argument('--update-kb', action='store_true', help='Update knowledge base before optimizing')
	
	# Research command
	research_parser = subparsers.add_parser('research', help='Standalone knowledge base building')
	research_parser.add_argument('model_path', help='Path to model')
	research_parser.add_argument('--test-dataset', required=True, help='Path to test dataset')
	research_parser.add_argument('--test-script', required=True, help='Path to test/inference script')
	research_parser.add_argument('--analyze-only', action='store_true', help='Don\'t run optimization')
	research_parser.add_argument('--export-workflows', action='store_true', help='Export generated workflows as YAML')
	research_parser.add_argument('--cite', action='store_true', help='Generate bibliography')
	
	# LLM options for research
	research_parser.add_argument('--llm-provider', choices=['openai', 'google', 'together', 'vllm'], help='LLM provider to use')
	research_parser.add_argument('--llm-model', help='LLM model name')
	research_parser.add_argument('--llm-base-url', help='Custom API base (for local vLLM)')
	research_parser.add_argument('--llm-api-key', help='API key override')
	
	# KB command
	kb_parser = subparsers.add_parser('kb', help='Knowledge Base Management')
	kb_subparsers = kb_parser.add_subparsers(dest='kb_command', help='KB operations')
	
	kb_parser.add_argument('list', action='store_true', help='List cached papers')
	kb_parser.add_argument('search', help='Search knowledge base')
	kb_parser.add_argument('export', action='store_true', help='Export KB')
	kb_parser.add_argument('--format', help='Export format')
	kb_parser.add_argument('clear', action='store_true', help='Clear cache')
	kb_parser.add_argument('stats', action='store_true', help='Show KB statistics')
	
	kb_list_parser = kb_subparsers.add_parser('list', help='List cached papers')
	kb_search_parser = kb_subparsers.add_parser('search', help='Search knowledge base')
	kb_search_parser.add_argument('query', help='Search query')
	kb_export_parser = kb_subparsers.add_parser('export', help='Export KB')
	kb_export_parser.add_argument('--format', help='Export format')
	kb_subparsers.add_parser('clear', help='Clear cache')
	kb_subparsers.add_parser('stats', help='Show KB statistics')
	
	# Analyze command
	analyze_parser = subparsers.add_parser('analyze', help='Inspect without optimizing')
	analyze_parser.add_argument('model_path', help='Path to model')
	# LLM options for analyze-only
	analyze_parser.add_argument('--llm-provider', choices=['openai', 'google', 'together', 'vllm'], help='LLM provider to use')
	analyze_parser.add_argument('--llm-model', help='LLM model name')
	analyze_parser.add_argument('--llm-base-url', help='Custom API base (for local vLLM)')
	analyze_parser.add_argument('--llm-api-key', help='API key override')
	
	# Benchmark command
	benchmark_parser = subparsers.add_parser('benchmark', help='Performance only')
	benchmark_parser.add_argument('model_path', help='Path to model')
	benchmark_parser.add_argument('--device', default='cuda', help='Device (default: cuda)')
	
	# Compare command
	compare_parser = subparsers.add_parser('compare', help='A/B test two models')
	compare_parser.add_argument('model1_path', help='Path to first model')
	compare_parser.add_argument('model2_path', help='Path to second model')
	compare_parser.add_argument('--dataset', help='Dataset path')
	
	# Serve command
	serve_parser = subparsers.add_parser('serve', help='Deploy optimized model')
	serve_parser.add_argument('model_path', help='Path to model')
	serve_parser.add_argument('--port', type=int, default=8000, help='Port (default: 8000)')
	
	return parser


def main():
	"""Main CLI entry point."""
	parser = create_parser()
	args = parser.parse_args()
	
	# Initialize logging if --log-file is provided
	if hasattr(args, 'log_file') and args.log_file:
		try:
			from .core.logger import set_log_file
		except ImportError:
			from model_opt.core.logger import set_log_file
		set_log_file(args.log_file)
	
	if not args.command:
		parser.print_help()
		sys.exit(1)
	
	# Handle optimize and research commands with model analysis
	analysis_info = None
	if args.command in ['optimize', 'research']:
		try:
			from .core.model_loader import analyze_model
		except ImportError:
			from model_opt.core.model_loader import analyze_model
		analysis_info = analyze_model(args.model_path, args.test_dataset, args.test_script)
	
	# Apply optimization techniques if requested
	if args.command == 'optimize':
		techniques = []
		if getattr(args, 'prune', False):
			techniques.append('prune')
		if getattr(args, 'quantize', False):
			techniques.append('quantize')
		
		if techniques:
			try:
				from .core.optimizer import Optimizer
			except ImportError:
				from model_opt.core.optimizer import Optimizer
			
			optimizer = Optimizer(args.model_path, args.test_dataset, args.test_script)
			output_path = f"{args.model_path}_optimized.pth"
			options = {
				'quant_method': getattr(args, 'quant_method', 'int8_weight_only'),
				'prune_backend': getattr(args, 'prune_backend', 'torch-pruning'),
				'prune_amount': getattr(args, 'prune_amount', 0.5),
				'prune_criterion': getattr(args, 'prune_criterion', 'magnitude'),
			}
			optimized_model = optimizer.optimize(techniques, output_path=output_path, **options)
			print(f"\nOptimized model saved to: {output_path}")

	# Research mode: Phase 2 (web search) + Phase 3 (embed & persist)
	run_research = (
		(args.command == 'research') or
		(args.command == 'optimize' and getattr(args, 'research', False))
	)

	if run_research and analysis_info:
		print("\nPHASE 2: RESEARCH SEARCH")
		print("━" * 62)
		try:
			# Local imports to keep optional deps isolated
			import asyncio
			try:
				from .agent.tools.research import ParallelResearchCrawler as ParallelPaperSearch
			except ImportError:
				try:
					from model_opt.agent.tools.research import ParallelResearchCrawler as ParallelPaperSearch
				except ImportError:
					# Fallback to old scraper if research module not available
					try:
						from .agent.tools.scraper import ParallelPaperSearch
					except ImportError:
						from model_opt.agent.tools.scraper import ParallelPaperSearch

			scraper_model_info = {
				'architecture_type': analysis_info.get('architecture_type', ''),
				'model_family': analysis_info.get('model_family', ''),
				'layer_types': analysis_info.get('layer_types', {}),
				'params': analysis_info.get('params', 0),
			}

			max_papers = getattr(args, 'max_papers', 50)
			results = asyncio.run(ParallelPaperSearch().search(scraper_model_info, max_papers=max_papers))

			if not results:
				print("No research results found.")
			else:
				print(f"Found {len(results)} relevant items.")

			# Phase 3: embed & persist
			print("\nPHASE 3: BUILD KNOWLEDGE BASE")
			print("━" * 62)
			texts, metas = [], []
			for r in results:
				content = r.get('content') or r.get('abstract') or ''
				if not content:
					continue
				texts.append(content)
				metas.append({
					'title': r.get('title', ''),
					'url': r.get('url', ''),
					'source': r.get('source', ''),
					'citations': r.get('citations', 0),
					'stars': r.get('stars', 0)
				})

			if not results:
				print("No content available to index.")
			else:
				try:
					try:
						from .utils.embeddings import Embeddings
					except ImportError:
						from model_opt.utils.embeddings import Embeddings
					try:
						from .utils.vecdb import LocalVecDB
					except ImportError:
						from model_opt.utils.vecdb import LocalVecDB
					try:
						from .agent.analyzer_agent import ResearchAgent
					except ImportError:
						from model_opt.agent.analyzer_agent import ResearchAgent

					emb = Embeddings()
					
					# Try to use analyzer_agent for filtering and enhanced processing
					try:
						# Check if we have analyzer results (from --analyze-only or agent mode)
						analyzer_results = None
						if getattr(args, 'analyze_only', False) or getattr(args, 'agent', False):
							# If analyzer_agent was used, try to get its results
							# For now, create a simple structure from raw results
							analyzer_results = {
								'items': results,
								'ranking': [{'index': i+1, 'score': 0.5} for i in range(min(30, len(results)))],
								'evaluation': []
							}
						
						# Use enhanced method if we have analyzer structure
						if analyzer_results:
							db = LocalVecDB(
								db_dir="rag_store",
								embedding_dim=emb.get_dimension(),
								use_hnsw=True,
								hnsw_m=16,
								ef_construction=200
							)
							db.load()
							db.add_from_analyzer_agent(analyzer_results, scraper_model_info, emb)
							db.persist()
							print(f"✓ Indexed papers with HNSW indexing and enhanced metadata")
						else:
							# Fallback to simple method
							texts, metas = [], []
							for r in results:
								content = r.get('content') or r.get('abstract') or ''
								if not content:
									continue
								texts.append(content)
								metas.append({
									'title': r.get('title', ''),
									'url': r.get('url', ''),
									'source': r.get('source', ''),
									'citations': r.get('citations', 0),
									'stars': r.get('stars', 0)
								})
							
							if texts:
								vectors = emb.encode(texts)
								db = LocalVecDB(db_dir="rag_store", embedding_dim=vectors.shape[1])
								db.load()
								db.add(vectors, metas)
								db.persist()
								print(f"Indexed {len(texts)} documents into rag_store/")
					except Exception as e:
						# Fallback to simple indexing
						texts, metas = [], []
						for r in results:
							content = r.get('content') or r.get('abstract') or ''
							if not content:
								continue
							texts.append(content)
							metas.append({
								'title': r.get('title', ''),
								'url': r.get('url', ''),
								'source': r.get('source', ''),
								'citations': r.get('citations', 0),
								'stars': r.get('stars', 0)
							})
						
						if texts:
							vectors = emb.encode(texts)
							db = LocalVecDB(db_dir="rag_store", embedding_dim=vectors.shape[1])
							db.load()
							db.add(vectors, metas)
							db.persist()
							print(f"Indexed {len(texts)} documents into rag_store/ (fallback mode)")
				except ImportError as e:
					# Friendly message for missing optional deps
					print(f"ERROR: {e}")
					print("\nTo enable embeddings, install sentence-transformers:")
					print("  pip install sentence-transformers")
					print("For HNSW indexing, install faiss-cpu:")
					print("  pip install faiss-cpu")
				except Exception as e:
					print(f"ERROR during embedding/indexing: {e}")
					import traceback
					traceback.print_exc()
		except Exception as e:
			print(f"ERROR during research phase: {e}")
	
	# Initialize LLM client when agent/research/analyze-only is requested
	need_llm = False
	if args.command == 'analyze':
		need_llm = True
	if args.command == 'research' and getattr(args, 'analyze_only', False):
		need_llm = True
	if args.command == 'optimize' and (getattr(args, 'agent', False) or getattr(args, 'research', False)):
		need_llm = True
	
	if need_llm and getattr(args, 'llm_provider', None):
		try:
			from .utils.llm import LLMClient
		except ImportError:
			from model_opt.utils.llm import LLMClient
		llm = LLMClient(
			provider=args.llm_provider,
			model=args.llm_model or ('gpt-4o' if args.llm_provider=='openai' else 'gemini-1.5-flash'),
			base_url=getattr(args, 'llm_base_url', None),
			api_key=getattr(args, 'llm_api_key', None),
		)
		# Test API key before proceeding
		print(f"\nVerifying LLM API connection ({args.llm_provider})...")
		ok, msg = llm.test_api_key()
		if not ok:
			print(f"ERROR: {msg}")
			print("\nPlease set the API key in one of these ways:")
			print("  1. Create a .env file in the project root with:")
			key_env = {
				'openai': 'OPENAI_API_KEY=sk-...',
				'together': 'TOGETHER_API_KEY=...',
				'google': 'GOOGLE_API_KEY=...',
			}.get(args.llm_provider, 'API_KEY=...')
			print(f"     {key_env}")
			print("  2. Use --llm-api-key flag to pass it directly")
			sys.exit(1)
		print(f"✓ {msg}")
	
	print(f"Command: {args.command}")
	print(f"Arguments: {args}")


if __name__ == '__main__':
	main()

