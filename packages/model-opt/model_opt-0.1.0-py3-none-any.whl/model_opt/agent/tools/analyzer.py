import re
from typing import Dict, List, Tuple, Any


_QUANT_KWS = [
	"int8", "int4", "quantization", "per-channel", "calibration", "qat",
	"post-training quantization", "ptq", "histogram"
]
_PRUNE_KWS = [
	"pruning", "filter", "structured", "unstructured", "sparsity", "magnitude"
]
_DISTILL_KWS = [
	"distillation", "teacher", "student", "knowledge distillation"
]
_FUSE_KWS = [
	"fuse", "fusion", "conv-bn", "bn folding", "layer fusion"
]
_THROUGHPUT_KWS = [
	"speed", "speedup", "x", "latency", "ms", "flops", "throughput"
]

_METRIC_RE = re.compile(r"((?:\d+\.?\d*)x)|((?:\d+\.?\d*)%)|(FLOPs|latency|ms|speedup)", re.IGNORECASE)


def _contains_any(text: str, keywords: List[str]) -> bool:
	low = text.lower()
	return any(kw in low for kw in keywords)


def _extract_metrics(text: str) -> str:
	matches = _METRIC_RE.findall(text or "")
	if not matches:
		return ""
	flat: List[str] = []
	for g1, g2, g3 in matches:
		if g1:
			flat.append(g1)
		if g2:
			flat.append(g2)
		if g3:
			flat.append(g3)
	return ", ".join(dict.fromkeys(flat))[:120]


def _guess_technique(title: str, content: str) -> str:
	text = f"{title} {content}".lower()
	techs: List[str] = []
	if _contains_any(text, _QUANT_KWS):
		techs.append("Quantization")
	if _contains_any(text, _PRUNE_KWS):
		techs.append("Structured/Unstructured Pruning")
	if _contains_any(text, _DISTILL_KWS):
		techs.append("Knowledge Distillation")
	if _contains_any(text, _FUSE_KWS):
		techs.append("Layer Fusion")
	return ", ".join(techs) if techs else "Unknown"


def _applicable(technique: str, model_info: Dict[str, Any]) -> Tuple[bool, str]:
	arch = (model_info.get('architecture_type') or '').lower()
	tech = (technique or '').lower()
	if not technique:
		return False, "Unknown"
	if 'prun' in tech or 'fuse' in tech or 'quant' in tech:
		# Broadly applicable to CNNs; quant applies widely
		if arch in ['cnn', '']:  # default to True if unknown
			return True, 'YES (CNN compatible)'
		return True, 'Likely (generic)'
	if 'distill' in tech:
		return True, 'YES (teacher-student)'
	return False, 'Unknown'


def _normalize(value: float, cap: float) -> float:
	if value <= 0:
		return 0.0
	return min(value / cap, 1.0)


def _score_paper(paper: Dict[str, Any], technique: str, model_info: Dict[str, Any]) -> float:
	title = paper.get('title', '')
	content = paper.get('content') or paper.get('abstract') or ''
	score = 0.0
	# Relevance keywords
	text = f"{title} {content}".lower()
	for group, weight in [
		(_QUANT_KWS, 0.25), (_PRUNE_KWS, 0.25), (_DISTILL_KWS, 0.2), (_FUSE_KWS, 0.15), (_THROUGHPUT_KWS, 0.1)
	]:
		if _contains_any(text, group):
			score += weight
	# Citations and stars
	score += 0.2 * _normalize(float(paper.get('citations', 0)), 500.0)
	score += 0.2 * _normalize(float(paper.get('stars', 0)), 5000.0)
	# Architecture match bonus
	arch = (model_info.get('architecture_type') or '').lower()
	if arch and arch in text:
		score += 0.15
	# Code availability bonus
	url = paper.get('url', '')
	if 'github.com' in url:
		score += 0.1
	return min(score, 1.0)


def _first_code_url(paper: Dict[str, Any]) -> str:
	url = paper.get('url') or ''
	if 'github.com' in url:
		return url
	# Try to find GitHub URL inside content
	content = paper.get('content') or ''
	m = re.search(r"https?://github\.com/\S+", content)
	return m.group(0) if m else ''


def _format_paper(idx: int, paper: Dict[str, Any], technique: str, applicable_note: str, metrics: str, code_url: str) -> List[str]:
	lines: List[str] = []
	title = paper.get('title', 'Unknown')
	source = paper.get('source', 'unknown')
	arxiv_id = ''
	if source == 'arxiv':
		arxiv_id = paper.get('arxiv_id', '')
	paper_header = f"Paper #{idx}: \"{title}\"" + (f" (arXiv:{arxiv_id})" if arxiv_id else "")
	lines.append(paper_header)
	lines.append(f"  |- Citations: {paper.get('citations', 0)}")
	lines.append(f"  |- Technique: {technique}")
	if metrics:
		lines.append(f"  |- Results: {metrics}")
	lines.append(f"  |- Applicable: {'\u2713 YES' if applicable_note.startswith('YES') else applicable_note}")
	if code_url:
		stars = paper.get('stars', 0)
		lines.append(f"  |- Code: {code_url} {'\u2b50 ' + str(stars) if stars else ''}")
	return lines


def analyze_papers(papers: List[Dict[str, Any]], model_info: Dict[str, Any], top_n: int = 15) -> Dict[str, Any]:
	"""Analyze papers, extract techniques, rank and print a PHASE 3 report."""
	# Score and collect
	entries: List[Tuple[float, Dict[str, Any], str, str, str, str]] = []  # (score, paper, technique, applicable_note, metrics, code_url)
	for paper in papers:
		title = paper.get('title', '')
		content = paper.get('content') or paper.get('abstract') or ''
		technique = _guess_technique(title, content)
		applicable, note = _applicable(technique, model_info)
		metrics = _extract_metrics(content)
		code_url = _first_code_url(paper)
		score = _score_paper(paper, technique, model_info)
		entries.append((score, paper, technique, ('YES' if applicable else note), metrics, code_url))

	# Rank
	entries.sort(key=lambda x: x[0], reverse=True)
	top = entries[:max(1, top_n)]

	# Print header
	print("PHASE 3: PAPER ANALYSIS & TECHNIQUE EXTRACTION")
	print("-" * 62)
	print(f"Analyzing top {len(top)} papers...\n")

	for i, (score, paper, technique, note, metrics, code_url) in enumerate(top, 1):
		for line in _format_paper(i, paper, technique, note, metrics, code_url):
			print(line)
		print()

	# Aggregate techniques
	tech_rank: List[Tuple[float, str, int]] = []  # (score, technique, paper_idx)
	for i, (score, _, technique, _, _, _) in enumerate(top, 1):
		if not technique or technique == 'Unknown':
			continue
		tech_rank.append((score, technique, i))
	tech_rank.sort(key=lambda x: x[0], reverse=True)

	print("Extracted Techniques (Ranked by Relevance):")
	for j, (score, tech, idx) in enumerate(tech_rank[:10], 1):
		print(f"   {j}. [{score:.2f}] {tech} (Paper #{idx})")
	print()

	return {
		'top_entries': top,
		'techniques': tech_rank
	}
