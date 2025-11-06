from __future__ import annotations

"""
LLM-powered research agent to assist optimization research.

Responsibilities:
1) Generate targeted keywords for searching papers/repos
2) Summarize top content
3) Rank results conditioned on current model info
4) Evaluate feasibility of ideas for the given model

Usage:
    from model_opt.agent.analyze import ResearchAgent
    from model_opt.utils.llm import LLMClient

    llm = LLMClient(provider="openai", model="gpt-4o")
    agent = ResearchAgent(llm)
    out = agent.run(model_info={
        'architecture_type': 'CNN',
        'model_family': 'ResNet',
        'layer_types': {'Conv2d': 49},
        'params': 25500000,
    }, max_papers=20)
    # out contains: queries, items (with summaries), ranking, evaluation
"""

from typing import Any, Dict, List, Tuple
import json

try:
    from pydantic import BaseModel, ValidationError, parse_raw_as, parse_obj_as
except Exception:  # pydantic optional; code falls back without strict validation
    BaseModel = object  # type: ignore
    ValidationError = Exception  # type: ignore
    def parse_raw_as(_type, raw):  # type: ignore
        return json.loads(raw)
    def parse_obj_as(_type, obj):  # type: ignore
        return obj


# ---------- Pydantic Models ----------
class RankingItem(BaseModel):
    index: int
    score: float
    reason: str


class EvaluationItem(BaseModel):
    index: int
    label: str
    justification: str


class ResearchAgent:
    def __init__(self, llm) -> None:
        self.llm = llm

    # ---------- Prompts ----------
    def build_system_prompt(self, model_info: Dict[str, Any]) -> str:
        arch = model_info.get('architecture_type', 'Unknown')
        family = model_info.get('model_family', '')
        params = model_info.get('params', 0)
        return (
            "You are a senior ML systems research assistant. "
            "Goal: help optimize a model via research.\n"
            f"Model: arch={arch}, family={family}, params={params}.\n"
            "Produce: (1) targeted search keywords, (2) concise summaries, "
            "(3) ranking by expected speed/size gains under accuracy constraints, "
            "(4) feasibility assessment with risks." 
        )

    def _prompt_keywords(self, model_info: Dict[str, Any]) -> str:
        arch = model_info.get('architecture_type', 'Unknown')
        family = model_info.get('model_family', '')
        return (
            "Generate 8-12 focused search queries for recent (2022-2025) "
            f"optimization techniques for {arch} {family}.\n"
            "Cover quantization (PTQ/QAT), pruning (structured/unstructured), kernel fusion, efficient layers.\n"
            "Return as a JSON array of strings only."
        )

    def _prompt_summarize(self) -> str:
        return (
            "Summarize each item in 3-5 bullets: core idea, claimed gains, dataset/model scope, "
            "requirements (data/training), code availability. Return compact text."
        )

    def _prompt_rank(self, model_info: Dict[str, Any]) -> str:
        arch = model_info.get('architecture_type', 'Unknown')
        return (
            "Rank the items by expected impact for the target model. Criteria: "
            f"1) applicability to {arch}, 2) expected speed/size gains, 3) effort/risk. "
            "Return JSON list of objects: {index, score (0-1), reason}."
        )

    def _prompt_evaluate(self, model_info: Dict[str, Any]) -> str:
        return (
            "Label each top idea as Strong/Promising/Weak for this model. Include 1-2 sentence justification "
            "and key risks. Return JSON list: {index, label, justification}."
        )

    # ---------- Orchestration ----------
    def generate_keywords(self, model_info: Dict[str, Any]) -> List[str]:
        sys_prompt = self.build_system_prompt(model_info)
        user_prompt = self._prompt_keywords(model_info)
        try:
            text = self.llm.complete(system=sys_prompt, prompt=user_prompt)
            queries = parse_raw_as(List[str], text)
            queries = [q.strip() for q in queries if isinstance(q, str) and q.strip()]
            if queries:
                return queries[:12]
        except (ValidationError, Exception):
            pass

        # Fallback heuristic
        arch = model_info.get('architecture_type', 'CNN')
        family = model_info.get('model_family', 'ResNet')
        base = [
            f"{arch} optimization techniques 2024",
            f"{arch} quantization methods",
            f"{arch} pruning strategies",
            f"post-training optimization {arch}",
        ]
        if arch.upper() == 'CNN':
            base += [
                "convolutional layer fusion",
                "filter pruning CNN",
                "depthwise separable convolution",
                f"{family} optimization",
            ]
        return base

    async def search_papers(self, model_info: Dict[str, Any], max_papers: int) -> List[Dict[str, Any]]:
        try:
            from .tools.research import ParallelResearchCrawler
        except Exception:
            try:
                from model_opt.agent.tools.research import ParallelResearchCrawler
            except Exception:
                # Fallback to old scraper if research module not available
                try:
                    from .tools.scraper import ParallelPaperSearch as ParallelResearchCrawler
                except Exception:
                    from model_opt.agent.tools.scraper import ParallelPaperSearch as ParallelResearchCrawler

        # Pass LLM to crawler so it can generate intelligent keywords directly
        # This allows the crawler to use LLM if available, or fall back to rule-based
        searcher = ParallelResearchCrawler(llm=self.llm)

        # The crawler will automatically use LLM for keyword generation if available
        # Otherwise it falls back to rule-based generation
        results = await searcher.search(model_info, max_papers=max_papers)
        return results

    def summarize_contents(self, items: List[Dict[str, Any]]) -> List[str]:
        sys_prompt = "You write terse, information-dense summaries for ML papers/repos."
        tpl = self._prompt_summarize()
        summaries: List[str] = []
        for it in items:
            title = it.get('title', '')
            url = it.get('url', '')
            content = it.get('content') or it.get('abstract') or ''
            snippet = content[:4000]
            user_prompt = (
                f"Title: {title}\nURL: {url}\nContent:\n{snippet}\n\n{tpl}"
            )
            try:
                summaries.append(self.llm.complete(system=sys_prompt, prompt=user_prompt).strip())
            except Exception:
                summaries.append("")
        return summaries

    def rank_by_model(self, items: List[Dict[str, Any]], model_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        sys_prompt = self.build_system_prompt(model_info)
        instr = self._prompt_rank(model_info)
        # Build a compact list for the model
        lines: List[str] = []
        for i, it in enumerate(items, 1):
            t = it.get('title', '')
            src = it.get('source', '')
            lines.append(f"{i}. {t} ({src})")
        user_prompt = "Items:\n" + "\n".join(lines) + "\n\n" + instr
        try:
            text = self.llm.complete(system=sys_prompt, prompt=user_prompt)
            parsed_items = parse_raw_as(List[RankingItem], text)
            return [item.dict() for item in parsed_items]
        except (ValidationError, Exception):
            pass
        # Fallback naive ranking
        return [{"index": i + 1, "score": 0.5, "reason": "heuristic"} for i in range(len(items))]

    def evaluate_ideas(self, items: List[Dict[str, Any]], model_info: Dict[str, Any], indices: List[int]) -> List[Dict[str, Any]]:
        sys_prompt = self.build_system_prompt(model_info)
        instr = self._prompt_evaluate(model_info)
        subset = []
        for i in indices:
            if 1 <= i <= len(items):
                it = items[i - 1]
                subset.append({"index": i, "title": it.get('title', ''), "source": it.get('source', '')})
        try:
            text = self.llm.complete(system=sys_prompt, prompt=f"Items: {subset}\n\n{instr}")
            parsed_items = parse_raw_as(List[EvaluationItem], text)
            return [item.dict() for item in parsed_items]
        except (ValidationError, Exception):
            pass
        return [{"index": i, "label": "Promising", "justification": "heuristic"} for i in indices]

    def run(self, model_info: Dict[str, Any], max_papers: int = 30) -> Dict[str, Any]:
        import asyncio

        # Phase 1.5: keyword generation (based on given model_info)
        queries = self.generate_keywords(model_info)

        # Phase 2: search
        results: List[Dict[str, Any]] = asyncio.run(self.search_papers(model_info, max_papers=max_papers))

        # Phase 3a: summarize
        summaries = self.summarize_contents(results)
        for it, s in zip(results, summaries):
            it['summary'] = s

        # Phase 3b: rank
        ranking = self.rank_by_model(results, model_info)

        # Phase 3c: evaluate
        top_indices = [int(r.get('index', 0)) for r in ranking[: min(10, len(ranking))] if isinstance(r.get('index', 0), int)]
        evaluation = self.evaluate_ideas(results, model_info, indices=top_indices)

        return {
            'queries': queries,
            'items': results,
            'ranking': ranking,
            'evaluation': evaluation,
        }


