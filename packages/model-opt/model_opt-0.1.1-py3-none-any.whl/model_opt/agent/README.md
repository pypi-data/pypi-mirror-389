# Research Agent

Research paper search and analysis agent for finding optimization techniques based on model architecture.

## Overview

The research agent searches multiple sources (ArXiv, Semantic Scholar, HuggingFace) to find relevant optimization papers and techniques for your model architecture.

## Basic Usage

```python
from model_opt.agent import ResearchAgent
from model_opt.utils.llm import LLMClient

# Initialize LLM (optional, for enhanced keyword generation)
llm = LLMClient(provider="openai", model="gpt-4o-mini")

# Create research agent
agent = ResearchAgent(llm)

# Run research
model_info = {
    'architecture_type': 'CNN',
    'model_family': 'ResNet',
    'params': 25000000
}

results = agent.run(model_info, max_papers=50)

# Results contain:
# - items: List of research papers/models
# - ranking: Ranking scores for each item
# - evaluation: Evaluation labels (Strong, Promising, Weak)
# - queries: Search queries used
```

## CLI Usage

```bash
# Research optimization papers
model-opt research model.pth \
    --test-dataset data/val/ \
    --test-script evaluate.py \
    --max-papers 50

# Analyze only (no optimization)
model-opt research model.pth \
    --test-dataset data/val/ \
    --test-script evaluate.py \
    --analyze-only \
    --max-papers 30
```

## LLM-Enhanced Search

When an LLM provider is specified, the agent automatically uses LLM for generating better search keywords:

```python
# OpenAI
llm = LLMClient(provider="openai", model="gpt-4o-mini")

# Google
llm = LLMClient(provider="google", model="gemini-pro")

# Together AI
llm = LLMClient(provider="together", model="meta-llama/Llama-3-8b-chat-hf")

# Local vLLM
llm = LLMClient(
    provider="vllm",
    model="meta-llama/Meta-Llama-3-8B",
    base_url="http://localhost:8000/v1"
)

agent = ResearchAgent(llm)
results = agent.run(model_info, max_papers=50)
```

## Research Sources

The agent searches multiple sources in parallel:

### ArXiv

```python
from model_opt.agent.tools.research import ArXivCrawler

crawler = ArXivCrawler()
papers = crawler.crawl_daily(
    query="cat:cs.CV OR cat:cs.LG AND (quantization OR pruning)",
    max_results=50,
    days_back=120
)
```

### Semantic Scholar

```python
from model_opt.agent.tools.research import SemanticScholarSearcher

searcher = SemanticScholarSearcher()
papers = searcher.search(
    query="ResNet quantization compression",
    max_results=50
)
```

### HuggingFace

```python
from model_opt.agent.tools.research import HuggingFaceSearcher

searcher = HuggingFaceSearcher()
models = searcher.search(
    query="ResNet quantized",
    max_results=50
)
```

## Parallel Research Crawler

The `ParallelResearchCrawler` searches all sources in parallel:

```python
from model_opt.agent.tools.research import ParallelResearchCrawler

crawler = ParallelResearchCrawler()
results = await crawler.search(
    model_info={
        'architecture_type': 'CNN',
        'model_family': 'ResNet'
    },
    max_papers=50
)
```

## Paper Filtering

Papers are automatically filtered by:
- **Date**: Last 120 days (configurable)
- **Venue**: Prefer CVPR/ICCV/ECCV (configurable)
- **Keywords**: Require 2+ keyword matches (configurable)

```python
from model_opt.agent.tools.research import PaperFilter

filter = PaperFilter(
    days_back=120,
    preferred_venues=['CVPR', 'ICCV', 'ECCV'],
    min_keyword_matches=2
)

filtered_papers = filter.filter(papers, keywords=['quantization', 'pruning'])
```

## Metadata Extraction

Extracts structured metadata from research results:

```python
from model_opt.agent.tools.research import MetadataExtractor

extractor = MetadataExtractor()
metadata = extractor.extract(paper_result)

# Returns:
# - arxiv_id: arXiv ID
# - title: Paper title
# - authors: List of authors
# - abstract: Abstract text
# - submission_date: Submission date
# - pdf_url: PDF URL
# - citations: Citation count
# - venue: Publication venue
```

## Integration with Vector Database

Research results can be indexed into a vector database for semantic search:

```python
from model_opt.utils.vecdb import LocalVecDB
from model_opt.utils.embeddings import Embeddings

# Get research results
results = agent.run(model_info, max_papers=50)

# Index into vector DB
emb = Embeddings()
db = LocalVecDB(
    db_dir="rag_store",
    embedding_dim=emb.get_dimension(),
    use_hnsw=True,
    hnsw_m=16,
    ef_construction=200
)

db.load()
db.add_from_analyzer_agent(results, model_info, emb)
db.persist()

# Query later
similar_papers = db.query(
    query_text="ResNet quantization techniques",
    top_k=10
)
```

## Components

### ResearchAgent

Main research agent that orchestrates search, ranking, and evaluation:

```python
from model_opt.agent import ResearchAgent

agent = ResearchAgent(llm=llm)
results = agent.run(model_info, max_papers=50)
```

### ParallelResearchCrawler

Parallel search across multiple sources:

```python
from model_opt.agent.tools.research import ParallelResearchCrawler

crawler = ParallelResearchCrawler()
results = await crawler.search(model_info, max_papers=50)
```

### PaperFilter

Filter and score papers based on criteria:

```python
from model_opt.agent.tools.research import PaperFilter

filter = PaperFilter(
    days_back=120,
    preferred_venues=['CVPR', 'ICCV', 'ECCV'],
    min_keyword_matches=2
)
```

### MetadataExtractor

Extract and normalize metadata from research results:

```python
from model_opt.agent.tools.research import MetadataExtractor

extractor = MetadataExtractor()
metadata = extractor.extract(paper_result)
```

## Scheduled Research

Daily scheduled research crawls:

```python
from model_opt.agent.tools.research import ResearchScheduler

scheduler = ResearchScheduler()
scheduler.schedule_daily(
    model_info=model_info,
    callback=lambda results: process_results(results)
)
```

## See Also

- [Optimization Techniques](../techniques/README.md) - Available optimization techniques
- [Autotuner Documentation](../autotuner/README.md) - Using research results with autotuner

