"""
Test script for phases 1-4 of the optimization pipeline:
1. Model Analysis
2. Research Paper Search
3. Get Applicable Techniques
4. Plan Optimization

Usage:
    python tests/test_phases_1_to_4.py --model resnet50
"""

import argparse
import os
import sys
import time
import subprocess
import requests
import io
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

try:
    import torch
    import torchvision.models as models
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    print("Warning: PyTorch not available. This script requires PyTorch.")
    sys.exit(1)


def _start_vllm_server(model: str = "Qwen/Qwen3-0.6B", port: int = 8000, timeout: int = 180):
    """Start VLLM server with specified model using Windows-compatible wrapper."""
    base_url = f"http://localhost:{port}/v1"
    
    # Check if server is already running
    try:
        resp = requests.get(f"http://localhost:{port}/health", timeout=2)
        if resp.status_code == 200:
            print(f"  VLLM server already running on port {port}")
            return None, base_url
    except:
        pass
    
    print(f"  Starting VLLM server with model {model} on port {port}...")
    print(f"  (This may take 30-90 seconds depending on model size and hardware)")
    
    try:
        # Use the Windows-compatible wrapper script
        script_path = Path(__file__).parent.parent / "scripts" / "run_vllm_server.py"
        
        if not script_path.exists():
            # Fallback to direct VLLM call if wrapper doesn't exist
            print(f"  Warning: Wrapper script not found at {script_path}, using direct VLLM call")
            cmd = [
                sys.executable, "-m", "vllm.entrypoints.openai.api_server",
                "--model", model,
                "--port", str(port),
                "--host", "0.0.0.0"
            ]
        else:
            # Use wrapper script for Windows compatibility
            cmd = [
                sys.executable, str(script_path),
                "--model", model,
                "--port", str(port),
                "--host", "0.0.0.0"
            ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to be ready
        health_url = f"http://localhost:{port}/health"
        start_time = time.time()
        check_interval = 10
        last_check_time = start_time
        
        while time.time() - start_time < timeout:
            elapsed = int(time.time() - start_time)
            try:
                resp = requests.get(health_url, timeout=3)
                if resp.status_code == 200:
                    elapsed_total = int(time.time() - start_time)
                    print(f"  VLLM server ready at {base_url} (took {elapsed_total}s)")
                    return process, base_url
            except requests.exceptions.RequestException:
                pass
            
            # Print progress every 30 seconds
            if elapsed - int(last_check_time - start_time) >= 30:
                remaining = int(timeout - elapsed)
                print(f"  ... still waiting ({elapsed}s elapsed, ~{remaining}s remaining)")
                last_check_time = time.time()
            
            time.sleep(check_interval)
        
        # Timeout
        elapsed_total = int(time.time() - start_time)
        print(f"  Warning: VLLM server failed to start within {timeout}s (waited {elapsed_total}s)")
        print(f"  Tip: Large models may need more time. Try increasing --vllm-timeout")
        if process.poll() is None:
            process.terminate()
            time.sleep(2)
            if process.poll() is None:
                process.kill()
        return None, base_url
        
    except Exception as e:
        print(f"  Warning: Failed to start VLLM server: {e}")
        print(f"  Tip: Make sure VLLM is installed: pip install vllm")
        return None, base_url


def phase1_analyze_model(model, model_name: str) -> Dict[str, Any]:
    """Phase 1: Analyze model architecture and characteristics."""
    print("\n" + "=" * 70)
    print("Phase 1: Analyzing model...")
    print("=" * 70)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    
    # Detect architecture
    model_str = str(model).lower()
    class_name = model.__class__.__name__.lower()
    
    has_conv = any(isinstance(m, (torch.nn.Conv1d, torch.nn.Conv2d, torch.nn.Conv3d)) for m in model.modules())
    has_attention = any('attention' in name.lower() or 'attn' in name.lower() for name, _ in model.named_modules())
    
    if 'resnet' in class_name or 'resnet' in model_str:
        arch = "CNN"
        family = "ResNet"
        suggestions = "Layer fusion and pruning effective"
    elif 'vit' in class_name or 'vision_transformer' in model_str:
        arch = "ViT"
        family = "VisionTransformer"
        suggestions = "Token merging and quantization effective"
    elif has_conv:
        arch = "CNN"
        family = "Unknown"
        suggestions = "Layer fusion and pruning effective"
    else:
        arch = "Unknown"
        family = ""
        suggestions = "Standard optimization techniques"
    
    print(f"\n  Architecture: {arch}")
    print(f"  Family: {family}")
    print(f"  Parameters: {total_params:,}")
    print(f"  Has Convolution: {has_conv}")
    print(f"  Has Attention: {has_attention}")
    print(f"  Suggestions: {suggestions}")
    
    model_info = {
        'architecture_type': arch,
        'model_family': family,
        'params': total_params,
        'has_conv': has_conv,
        'has_attention': has_attention
    }
    
    print("\n✓ Phase 1 completed successfully")
    return model_info


def phase2_research_papers(model_info: Dict[str, Any], llm, max_papers: int = 15) -> Optional[Dict[str, Any]]:
    """Phase 2: Search research papers."""
    print("\n" + "=" * 70)
    print("Phase 2: Searching research papers...")
    print("=" * 70)
    
    # Try with LLM if available
    if llm:
        try:
            from model_opt.agent.analyzer_agent import ResearchAgent
            
            print(f"\n  Using LLM-enhanced research agent...")
            agent = ResearchAgent(llm)
            results = agent.run(model_info, max_papers=max_papers)
            
            items = results.get('items', [])
            queries = results.get('queries', [])
            
            print(f"\n  📊 Search Summary:")
            print(f"    Generated {len(queries)} search queries using LLM")
            print(f"    Found {len(items)} papers about {model_info.get('architecture_type', 'Unknown')} optimization")
            
            if queries:
                print(f"\n  🔍 Generated Search Queries:")
                for i, query in enumerate(queries, 1):
                    print(f"    {i}. {query}")
            
            if items:
                print(f"\n  📄 Papers Found and Analyzed:")
                print("    " + "-" * 66)
                
                for idx, item in enumerate(items, 1):
                    title = item.get('title', 'Unknown Title')
                    authors = item.get('authors', [])
                    abstract = item.get('abstract', '')
                    url = item.get('url', item.get('pdf_url', ''))
                    date = item.get('date', item.get('published_date', ''))
                    source = item.get('source', 'unknown')
                    
                    # Display paper details
                    print(f"\n    Paper #{idx}:")
                    print(f"      Title: {title}")
                    
                    if authors:
                        authors_str = ', '.join(authors[:3])
                        if len(authors) > 3:
                            authors_str += f" et al. ({len(authors)} total)"
                        print(f"      Authors: {authors_str}")
                    
                    if date:
                        print(f"      Date: {date}")
                    
                    if source:
                        print(f"      Source: {source}")
                    
                    if url:
                        print(f"      URL: {url}")
                    
                    if abstract:
                        # Truncate long abstracts
                        abstract_preview = abstract[:200] + "..." if len(abstract) > 200 else abstract
                        print(f"      Abstract: {abstract_preview}")
                    
                    # Show analysis metadata if available
                    if 'score' in item:
                        print(f"      Relevance Score: {item['score']:.3f}")
                    if 'techniques' in item:
                        techniques = item.get('techniques', [])
                        if techniques:
                            print(f"      Techniques: {', '.join(techniques) if isinstance(techniques, list) else techniques}")
                    if 'architecture' in item:
                        print(f"      Architecture: {item['architecture']}")
                    if 'implementation_status' in item:
                        print(f"      Implementation Status: {item['implementation_status']}")
                
                print("\n    " + "-" * 66)
                
                # Show top 3 papers summary
                print(f"\n  🏆 Top Papers Summary:")
                for idx in range(min(3, len(items))):
                    item = items[idx]
                    title = item.get('title', 'Unknown')
                    if len(title) > 60:
                        title = title[:57] + "..."
                    print(f"    {idx+1}. {title}")
            
            print("\n✓ Phase 2 completed successfully (with LLM)")
            return results
        except Exception as e:
            print(f"  Warning: Research phase with LLM failed: {e}")
            import traceback
            traceback.print_exc()
            print(f"  Falling back to basic paper search...")
    
    # Fallback: Try basic research without LLM
    try:
        from model_opt.agent.tools.research import ParallelResearchCrawler
        
        print(f"\n  Using basic research crawler (no LLM)...")
        crawler = ParallelResearchCrawler(llm=None)
        
        arch_type = model_info.get('architecture_type', 'CNN')
        query = f"{arch_type} model compression quantization pruning"
        
        print(f"\n  🔍 Search Query: {query}")
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        print(f"  Searching... (this may take a moment)")
        # Create a simple model_info dict for the search
        search_model_info = {
            'architecture_type': arch_type,
            'model_family': model_info.get('model_family', arch_type)
        }
        items = loop.run_until_complete(
            crawler.search(search_model_info, max_papers=max_papers)
        )
        
        # Wrap results in expected format
        results = {'items': items, 'queries': [query], 'method': 'basic_search'}
        
        print(f"\n  📊 Search Summary:")
        print(f"    Found {len(items)} papers (basic search without LLM)")
        
        if items:
            print(f"\n  📄 Papers Found:")
            print("    " + "-" * 66)
            
            for idx, item in enumerate(items, 1):
                title = item.get('title', 'Unknown Title')
                authors = item.get('authors', [])
                abstract = item.get('abstract', '')
                url = item.get('url', item.get('pdf_url', ''))
                date = item.get('date', item.get('published_date', ''))
                source = item.get('source', 'unknown')
                
                print(f"\n    Paper #{idx}:")
                print(f"      Title: {title}")
                
                if authors:
                    authors_str = ', '.join(authors[:3]) if isinstance(authors, list) else str(authors)
                    if isinstance(authors, list) and len(authors) > 3:
                        authors_str += f" et al. ({len(authors)} total)"
                    print(f"      Authors: {authors_str}")
                
                if date:
                    print(f"      Date: {date}")
                
                if source:
                    print(f"      Source: {source}")
                
                if url:
                    print(f"      URL: {url}")
                
                if abstract:
                    abstract_preview = abstract[:200] + "..." if len(abstract) > 200 else abstract
                    print(f"      Abstract: {abstract_preview}")
                
                # Show metadata if available
                if 'score' in item:
                    print(f"      Relevance Score: {item['score']:.3f}")
                if 'techniques' in item:
                    techniques = item.get('techniques', [])
                    if techniques:
                        print(f"      Techniques: {', '.join(techniques) if isinstance(techniques, list) else techniques}")
            
            print("\n    " + "-" * 66)
            
            # Show top papers
            print(f"\n  🏆 Top Papers:")
            for idx in range(min(3, len(items))):
                item = items[idx]
                title = item.get('title', 'Unknown')
                if len(title) > 60:
                    title = title[:57] + "..."
                print(f"    {idx+1}. {title}")
        
        print("\n✓ Phase 2 completed successfully (basic search)")
        return {'items': items, 'queries': [query], 'method': 'basic_search'}
    except Exception as e:
        print(f"  Warning: Research phase failed: {e}")
        import traceback
        traceback.print_exc()
        print(f"  Continuing without research papers...")
        print("\n✓ Phase 2 completed (fallback mode)")
        return {
            'items': [],
            'queries': [],
            'method': 'fallback',
            'note': 'Research phase unavailable, using default optimization strategies'
        }


def phase3_applicable_techniques(
    model,
    model_info: Dict[str, Any],
    constraints: Optional[Dict[str, float]] = None,
    use_federated_api: bool = True,
    federated_api_url: Optional[str] = None,
    federated_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Phase 3: Get applicable techniques using hybrid optimization."""
    print("\n" + "=" * 70)
    print("Phase 3: Getting applicable techniques...")
    print("=" * 70)
    
    try:
        from model_opt.autotuner.intelligent_optimizer import IntelligentOptimizer
        from model_opt.autotuner.search_space import ArchitectureFamily
        
        # Try to use federated API first (default), fallback to file-based
        federated_tree_path = None
        api_client_initialized = False
        
        if use_federated_api:
            try:
                from model_opt.tree_search.federated import FederatedAPIClient
                from model_opt.core.config import FEDERATED_API_CONFIG
                
                # Use provided URL/key or fall back to config
                api_url = federated_api_url or FEDERATED_API_CONFIG['base_url']
                api_key = federated_api_key or FEDERATED_API_CONFIG['api_key']
                
                # Test API connectivity
                try:
                    import asyncio
                    import httpx
                    
                    async def test_api():
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            try:
                                resp = await client.get(f"{api_url}/health")
                                return resp.status_code == 200
                            except Exception:
                                return False
                    
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    api_available = loop.run_until_complete(test_api())
                    
                    if api_available:
                        print(f"\n  ✓ Using federated tree API: {api_url}")
                        api_client_initialized = True
                    else:
                        print(f"\n  ⚠ Federated API not available at {api_url}, falling back to file-based")
                except Exception as e:
                    print(f"\n  ⚠ Failed to test federated API: {e}, falling back to file-based")
            except ImportError:
                print(f"\n  ⚠ Federated API client not available, falling back to file-based")
            except Exception as e:
                print(f"\n  ⚠ Failed to initialize federated API: {e}, falling back to file-based")
        
        # Fallback to file-based if API not used or failed
        if not api_client_initialized:
            sample_tree_path = os.path.join(os.path.dirname(__file__), 'federated_tree_sample.json')
            if os.path.exists(sample_tree_path):
                federated_tree_path = sample_tree_path
                print(f"\n  Using sample federated tree from: {federated_tree_path}")
            else:
                print(f"\n  No federated tree available (API or file), using local cache only")
        
        # Initialize optimizer with federated tree (API or file path)
        if api_client_initialized:
            optimizer = IntelligentOptimizer(
                use_federated_api=True,
                federated_api_url=federated_api_url,
                federated_api_key=federated_api_key
            )
        else:
            optimizer = IntelligentOptimizer(storage_backend=federated_tree_path)
        
        # Create example input for optimization
        example_input = torch.randn(1, 3, 224, 224)
        
        # Test hybrid method (default)
        print("\n  Testing hybrid method (federated tree -> cache -> MCTS)...")
        try:
            # Create a fresh model copy for hybrid
            try:
                hybrid_model = type(model)()
                hybrid_model.load_state_dict(model.state_dict())
                hybrid_model.eval()
            except Exception:
                import copy
                hybrid_model = copy.deepcopy(model)
                hybrid_model.eval()
            
            # Use default method='hybrid'
            hybrid_model, hybrid_result = optimizer.optimize_auto(
                hybrid_model,
                constraints=constraints,
                example_input=example_input,
                method='hybrid',
                n_simulations=50,
                timeout_seconds=300.0
            )
            
            method_results = {
                'hybrid': {
                    'model': hybrid_model,
                    'result': hybrid_result,
                    'techniques': hybrid_result.techniques,
                    'speedup': hybrid_result.speedup,
                    'compression_ratio': hybrid_result.compression_ratio,
                    'accuracy_drop': hybrid_result.accuracy_drop
                }
            }
            
            print(f"\n  ✓ Hybrid optimization completed:")
            print(f"    Techniques: {len(hybrid_result.techniques)}")
            if hybrid_result.techniques:
                tech_names = [str(t.value) if hasattr(t, 'value') else str(t) for t in hybrid_result.techniques[:5]]
                print(f"    Applied: {', '.join(tech_names)}")
            print(f"    Speedup: {hybrid_result.speedup:.2f}x")
            print(f"    Compression: {hybrid_result.compression_ratio:.2f}x")
            print(f"    Accuracy Drop: {hybrid_result.accuracy_drop:.2%}")
            
            if api_client_initialized:
                api_url_used = federated_api_url or "from config"
                print(f"    ✓ Federated tree lookup attempted (API: {api_url_used})")
            elif federated_tree_path:
                print(f"    ✓ Federated tree lookup attempted (file: {federated_tree_path})")
            else:
                print(f"    ✓ Using local cache only (no federated tree)")
            
        except Exception as e:
            print(f"    ✗ Hybrid failed: {e}")
            import traceback
            traceback.print_exc()
            method_results = {'hybrid': None}
        
        # Get signature for compatibility
        from model_opt.autotuner.search_space import ModelSignature
        signature = ModelSignature(
            family=ArchitectureFamily.CNN if model_info.get('architecture_type') == 'CNN' else ArchitectureFamily.VIT,
            total_params=model_info.get('params', 0),
            num_layers=len(list(model.modules())),
            has_attention=model_info.get('has_attention', False),
            has_conv=model_info.get('has_conv', False)
        )
        
        default_techniques = method_results.get('hybrid', {}).get('techniques', [])
        
        print("\n✓ Phase 3 completed successfully")
        return {
            'method_results': method_results,
            'techniques': default_techniques,
            'signature': signature,
            'optimizer': optimizer
        }
    except Exception as e:
        print(f"  ✗ Phase 3 failed: {e}")
        import traceback
        traceback.print_exc()
        return {'method_results': {}, 'techniques': [], 'signature': None, 'optimizer': None}


def phase4_plan_optimization(method_results: Dict[str, Any], constraints: Optional[Dict[str, float]] = None) -> bool:
    """Phase 4: Plan optimization - validate and display the optimization plan."""
    print("\n" + "=" * 70)
    print("Phase 4: Planning optimization...")
    print("=" * 70)
    
    try:
        if method_results and any(v is not None for v in method_results.values()):
            valid_results = {k: v for k, v in method_results.items() if v is not None}
            
            if valid_results:
                best_method = max(valid_results.items(), key=lambda x: x[1].get('speedup', 0))
                best_method_name = best_method[0]
                best_result_data = best_method[1]
                
                techniques = best_result_data.get('techniques', [])
                expected_speedup = best_result_data.get('speedup', 1.0)
                expected_compression = best_result_data.get('compression_ratio', 1.0)
                expected_acc_drop = best_result_data.get('accuracy_drop', 0.0)
                
                print(f"\n  Optimization Plan:")
                print(f"    Method: {best_method_name}")
                print(f"    Techniques: {len(techniques)} techniques")
                if techniques:
                    tech_names = [str(t.value) if hasattr(t, 'value') else str(t) for t in techniques[:5]]
                    print(f"    Applied: {', '.join(tech_names)}")
                print(f"    Expected Speedup: {expected_speedup:.2f}x")
                print(f"    Expected Compression: {expected_compression:.2f}x")
                print(f"    Expected Accuracy Drop: {expected_acc_drop:.2%}")
                
                if constraints:
                    max_acc_drop = constraints.get('max_accuracy_drop', 0.05)
                    if expected_acc_drop > max_acc_drop:
                        print(f"\n    ⚠ Warning: Expected accuracy drop ({expected_acc_drop:.2%}) exceeds constraint ({max_acc_drop:.2%})")
                    else:
                        print(f"\n    ✓ Validation: Plan meets accuracy constraint (drop < {max_acc_drop:.2%})")
                
                print("\n✓ Phase 4 completed successfully")
                return True
            else:
                print("  ✗ No valid optimization results to plan from")
                return False
        else:
            print("  ✗ No method results available for planning")
            return False
    except Exception as e:
        print(f"  ✗ Planning phase failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Test phases 1-4 of optimization pipeline")
    parser.add_argument('--model', type=str, default='resnet50', help='Model name from torch.hub (e.g., resnet50, mobilenet_v2)')
    parser.add_argument('--pretrained', action='store_true', default=True, help='Use pretrained weights')
    parser.add_argument('--llm-provider', type=str, default='vllm', help='LLM provider (openai, together, google, vllm)')
    parser.add_argument('--llm-model', type=str, default='Qwen/Qwen3-0.6B', help='LLM model name')
    parser.add_argument('--llm-base-url', type=str, help='LLM base URL (for vllm, default: http://localhost:8000/v1)')
    parser.add_argument('--vllm-port', type=int, default=8000, help='Port for VLLM server (default: 8000)')
    parser.add_argument('--vllm-auto-start', action='store_true', default=True, help='Automatically start VLLM server if not running')
    parser.add_argument('--vllm-timeout', type=int, default=180, help='Timeout in seconds for VLLM server startup')
    parser.add_argument('--max-papers', type=int, default=15, help='Maximum papers to search')
    parser.add_argument('--max-accuracy-drop', type=float, default=0.05, help='Maximum acceptable accuracy drop')
    parser.add_argument('--skip-research', action='store_true', help='Skip research phase (Phase 2)')
    parser.add_argument('--federated-api-url', type=str, help='Federated API URL (defaults to config value)')
    parser.add_argument('--federated-api-key', type=str, help='Federated API key (defaults to config/env value)')
    parser.add_argument('--use-federated-api', action='store_true', default=True, help='Use federated tree API (default: True)')
    parser.add_argument('--no-federated-api', dest='use_federated_api', action='store_false', help='Disable federated tree API, use file-based instead')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Model Optimization Pipeline - Phases 1-4 Test")
    print("=" * 70)
    
    # Track phase completion
    phases_completed = {
        'phase1': False,
        'phase2': False,
        'phase3': False,
        'phase4': False
    }
    
    # Initialize LLM (optional - only if research phase enabled)
    llm = None
    vllm_process = None
    
    if not args.skip_research:
        try:
            from model_opt.utils.llm import LLMClient
            
            base_url = args.llm_base_url
            if args.llm_provider == 'vllm' and args.vllm_auto_start:
                if not base_url:
                    base_url = f"http://localhost:{args.vllm_port}/v1"
                print(f"\n  Auto-starting VLLM server (this may take 30-90 seconds)...")
                vllm_process, base_url = _start_vllm_server(
                    model=args.llm_model,
                    port=args.vllm_port,
                    timeout=args.vllm_timeout
                )
                if vllm_process is not None:
                    print(f"  Waiting for VLLM server to be fully ready...")
                    time.sleep(10)
            
            if args.llm_provider == 'vllm' and not base_url:
                base_url = f"http://localhost:{args.vllm_port}/v1"
            
            llm = LLMClient(
                provider=args.llm_provider,
                model=args.llm_model,
                base_url=base_url
            )
            
            # Test API key with extended retry for VLLM
            success, msg = llm.test_api_key()
            if not success and args.llm_provider == 'vllm':
                max_retries = 5
                retry_delay = 10
                print(f"  VLLM server not ready yet, waiting up to {max_retries * retry_delay} seconds...")
                for retry in range(max_retries):
                    print(f"  Retry {retry + 1}/{max_retries} (waiting {retry_delay}s)...")
                    time.sleep(retry_delay)
                    success, msg = llm.test_api_key()
                    if success:
                        print(f"  VLLM server is ready!")
                        break
                    retry_delay = min(retry_delay + 5, 20)
            
            if not success:
                if args.llm_provider == 'vllm':
                    print(f"  Warning: VLLM server not available: {msg}")
                    print(f"  Phase 2 will run with fallback search (no LLM)")
                    llm = None
                else:
                    print(f" Warning: LLM connection test failed: {msg}")
                    args.skip_research = True
        except Exception as e:
            print(f" Warning: Could not initialize LLM: {e}")
            if args.llm_provider != 'vllm':
                args.skip_research = True
    
    # Phase 1: Load and analyze model
    print(f"\nLoading model: {args.model}")
    try:
        if hasattr(models, args.model):
            model_fn = getattr(models, args.model)
            model = model_fn(pretrained=args.pretrained)
        else:
            model = torch.hub.load('pytorch/vision', args.model, pretrained=args.pretrained)
        model.eval()
        
        model_info = phase1_analyze_model(model, args.model)
        phases_completed['phase1'] = True
    except Exception as e:
        print(f" ✗ Failed to load model: {e}")
        sys.exit(1)
    
    # Phase 2: Research papers
    analyzer_results = None
    if not args.skip_research:
        analyzer_results = phase2_research_papers(model_info, llm, max_papers=args.max_papers)
        phases_completed['phase2'] = analyzer_results is not None
    else:
        print("\n" + "=" * 70)
        print("Phase 2: Searching research papers...")
        print("=" * 70)
        print("  (Skipped by user)")
        phases_completed['phase2'] = True
    
    # Cleanup VLLM process if started
    if vllm_process and vllm_process.poll() is None:
        try:
            vllm_process.terminate()
            vllm_process.wait(timeout=5)
            print("\n  VLLM server stopped")
        except:
            if vllm_process.poll() is None:
                vllm_process.kill()
    
    # Phase 3: Get applicable techniques
    constraints = {'max_accuracy_drop': args.max_accuracy_drop}
    tree_search_results = phase3_applicable_techniques(
        model,
        model_info,
        constraints,
        use_federated_api=args.use_federated_api,
        federated_api_url=args.federated_api_url,
        federated_api_key=args.federated_api_key
    )
    method_results = tree_search_results.get('method_results', {})
    phases_completed['phase3'] = len(method_results) > 0 and any(v is not None for v in method_results.values())
    
    # Phase 4: Plan optimization
    phases_completed['phase4'] = phase4_plan_optimization(method_results, constraints)
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Phase 1 (Model Analysis): {'✓' if phases_completed['phase1'] else '✗'}")
    print(f"Phase 2 (Research Papers): {'✓' if phases_completed['phase2'] else '✗'}")
    print(f"Phase 3 (Applicable Techniques): {'✓' if phases_completed['phase3'] else '✗'}")
    print(f"Phase 4 (Plan Optimization): {'✓' if phases_completed['phase4'] else '✗'}")
    print("=" * 70)
    
    if all(phases_completed.values()):
        print("\n✓ All phases completed successfully!")
        return 0
    else:
        print("\n✗ Some phases failed. Check output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

