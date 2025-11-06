import json
import os
import re
from typing import List, Dict, Tuple, Optional, Any
import numpy as np

# Try to import faiss for HNSW indexing
try:
	import faiss
	_FAISS_AVAILABLE = True
except ImportError:
	_FAISS_AVAILABLE = False
	faiss = None


class LocalVecDB:
	"""A tiny local vector DB with HNSW indexing that persists to disk."""

	def __init__(
		self,
		db_dir: str = "rag_store",
		embedding_dim: int = 384,
		use_hnsw: bool = True,
		hnsw_m: int = 16,
		ef_construction: int = 200
	) -> None:
		"""Initialize LocalVecDB.
		
		Args:
			db_dir: Directory for storing database files
			embedding_dim: Dimension of embeddings
			use_hnsw: Whether to use HNSW indexing (requires faiss)
			hnsw_m: HNSW parameter M (number of connections)
			ef_construction: HNSW parameter ef_construction
		"""
		self.db_dir = db_dir
		self.embedding_dim = embedding_dim
		self.use_hnsw = use_hnsw and _FAISS_AVAILABLE
		self.hnsw_m = hnsw_m
		self.ef_construction = ef_construction
		os.makedirs(self.db_dir, exist_ok=True)
		self.index_path = os.path.join(self.db_dir, "embeddings.npz")
		self.hnsw_index_path = os.path.join(self.db_dir, "hnsw.index")
		self.meta_path = os.path.join(self.db_dir, "metadata.json")
		self._emb: np.ndarray | None = None
		self._meta: List[Dict] = []
		self._hnsw_index: Optional[Any] = None
		
		if self.use_hnsw and not _FAISS_AVAILABLE:
			print("⚠️  faiss not available, falling back to cosine similarity")
			self.use_hnsw = False

	def load(self) -> None:
		"""Load embeddings and metadata from disk."""
		if os.path.exists(self.index_path):
			self._emb = np.load(self.index_path)["embeddings"]
		else:
			self._emb = np.empty((0, self.embedding_dim), dtype=np.float32)
		if os.path.exists(self.meta_path):
			with open(self.meta_path, "r", encoding="utf-8") as f:
				self._meta = json.load(f)
		else:
			self._meta = []
		
		# Load HNSW index if available
		if self.use_hnsw and os.path.exists(self.hnsw_index_path):
			try:
				self._hnsw_index = faiss.read_index(self.hnsw_index_path)
			except Exception as e:
				print(f"⚠️  Failed to load HNSW index: {e}, will rebuild")
				self._hnsw_index = None

	def add(self, vectors: np.ndarray, metadatas: List[Dict]) -> None:
		"""Add vectors and metadata to the database.
		
		Args:
			vectors: Numpy array of embeddings
			metadatas: List of metadata dictionaries
		"""
		if self._emb is None:
			self.load()
		if vectors.ndim == 1:
			vectors = vectors[None, :]
		if self._emb.size == 0:
			self._emb = vectors.astype(np.float32)
		else:
			self._emb = np.vstack([self._emb, vectors.astype(np.float32)])
		self._meta.extend(metadatas)
		
		# Update HNSW index if enabled
		if self.use_hnsw:
			self._update_hnsw_index(vectors.astype(np.float32))

	def persist(self) -> None:
		"""Persist embeddings, metadata, and HNSW index to disk."""
		np.savez_compressed(self.index_path, embeddings=self._emb)
		with open(self.meta_path, "w", encoding="utf-8") as f:
			json.dump(self._meta, f, ensure_ascii=False, indent=2)
		
		# Save HNSW index if available
		if self.use_hnsw and self._hnsw_index is not None:
			try:
				faiss.write_index(self._hnsw_index, self.hnsw_index_path)
			except Exception as e:
				print(f"⚠️  Failed to save HNSW index: {e}")

	def _cosine_sim(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
		"""Compute cosine similarity between two arrays.
		
		Args:
			a: First array
			b: Second array
			
		Returns:
			Similarity matrix
		"""
		a = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-12)
		b = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-12)
		return a @ b.T
	
	def _extract_abstract_and_methodology(self, content: str) -> Tuple[str, str]:
		"""Extract abstract and methodology sections from paper content.
		
		Args:
			content: Full paper content or abstract
			
		Returns:
			Tuple of (abstract_text, methodology_text)
		"""
		# Try to extract abstract section
		abstract_patterns = [
			r'abstract[:\s]+(.*?)(?=\n\s*(?:introduction|1\.|keywords|index terms))',
			r'abstract\s*\n\s*(.*?)(?=\n\s*\n)',
		]
		
		abstract_text = ""
		for pattern in abstract_patterns:
			match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
			if match:
				abstract_text = match.group(1).strip()
				break
		
		# If no abstract section found, use first paragraph or provided abstract
		if not abstract_text:
			# Try to find first substantial paragraph
			paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 50]
			if paragraphs:
				abstract_text = paragraphs[0]
		
		# Try to extract methodology section
		methodology_patterns = [
			r'methodology[:\s]+(.*?)(?=\n\s*(?:results|experiments|evaluation|conclusion))',
			r'method[:\s]+(.*?)(?=\n\s*(?:results|experiments|evaluation|conclusion))',
			r'approach[:\s]+(.*?)(?=\n\s*(?:results|experiments|evaluation|conclusion))',
			r'3\.\s*(?:method|methodology|approach)[:\s]+(.*?)(?=\n\s*(?:4\.|results|experiments))',
		]
		
		methodology_text = ""
		for pattern in methodology_patterns:
			match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
			if match:
				methodology_text = match.group(1).strip()
				# Limit methodology length
				if len(methodology_text) > 2000:
					methodology_text = methodology_text[:2000]
				break
		
		# If no methodology found, try to extract relevant parts
		if not methodology_text:
			# Look for sections with keywords
			keywords = ['quantization', 'pruning', 'compression', 'optimization', 'technique', 'algorithm']
			content_lower = content.lower()
			for keyword in keywords:
				idx = content_lower.find(keyword)
				if idx > 0:
					# Extract context around keyword
					start = max(0, idx - 500)
					end = min(len(content), idx + 500)
					methodology_text = content[start:end].strip()
					break
		
		# Fallback: use abstract if methodology not found
		if not methodology_text and abstract_text:
			methodology_text = abstract_text
		
		return abstract_text or content[:500], methodology_text or content[:500]
	
	def _extract_implementation_status(self, paper: Dict[str, Any]) -> str:
		"""Extract implementation status from paper metadata.
		
		Args:
			paper: Paper metadata dictionary
			
		Returns:
			Implementation status string
		"""
		content = paper.get('content', '') or paper.get('abstract', '')
		url = paper.get('url', '')
		
		# Check for code availability
		if 'github.com' in url.lower():
			return 'Code Available'
		
		# Check content for implementation hints
		content_lower = content.lower()
		if any(kw in content_lower for kw in ['github', 'code available', 'implementation']):
			return 'Code Available'
		if any(kw in content_lower for kw in ['pseudocode', 'algorithm', 'proposed']):
			return 'Algorithm Described'
		if any(kw in content_lower for kw in ['theoretical', 'analysis', 'proof']):
			return 'Theoretical'
		
		return 'Unknown'
	
	def add_from_analyzer_agent(
		self,
		analyzer_results: Dict[str, Any],
		model_info: Dict[str, Any],
		embeddings_model: Any
	) -> None:
		"""Add papers from analyzer_agent.py results with filtering and enhanced encoding.
		
		Args:
			analyzer_results: Results from ResearchAgent.run() containing:
				- items: List of paper dictionaries
				- ranking: Ranking information
				- evaluation: Evaluation information
			model_info: Model architecture information
			embeddings_model: Embeddings model instance (from Embeddings class)
		"""
		if self._emb is None:
			self.load()
		
		# Get filtered papers from analyzer results
		items = analyzer_results.get('items', [])
		ranking = analyzer_results.get('ranking', [])
		evaluation = analyzer_results.get('evaluation', [])
		
		if not items:
			print("⚠️  No papers in analyzer results")
			return
		
		# Filter papers based on ranking (top papers)
		ranked_indices = set()
		for rank_item in ranking[:30]:  # Top 30 ranked papers
			idx = rank_item.get('index', 0) - 1  # Convert to 0-based
			if 0 <= idx < len(items):
				ranked_indices.add(idx)
		
		# Also include evaluated papers
		for eval_item in evaluation:
			idx = eval_item.get('index', 0) - 1
			if 0 <= idx < len(items):
				ranked_indices.add(idx)
		
		# If no ranking, use all items
		if not ranked_indices:
			ranked_indices = set(range(len(items)))
		
		filtered_papers = [items[i] for i in sorted(ranked_indices) if i < len(items)]
		
		print(f"📚 Processing {len(filtered_papers)} filtered papers from analyzer_agent...")
		
		# Extract techniques using analyzer.py functions
		try:
			from model_opt.agent.tools.analyzer import _guess_technique
		except ImportError:
			def _guess_technique(title, content):
				return "Unknown"
		
		# Process each paper
		vectors_list = []
		metadatas_list = []
		
		for paper in filtered_papers:
			title = paper.get('title', '')
			content = paper.get('content', '') or paper.get('abstract', '') or ''
			
			if not content:
				continue
			
			# Extract abstract and methodology
			abstract, methodology = self._extract_abstract_and_methodology(content)
			
			# Encode abstract and methodology separately
			abstract_vec = embeddings_model.encode([abstract])[0] if abstract else None
			methodology_vec = embeddings_model.encode([methodology])[0] if methodology else None
			
			# Average embeddings for combined representation
			if abstract_vec is not None and methodology_vec is not None:
				combined_vec = (abstract_vec + methodology_vec) / 2.0
			elif abstract_vec is not None:
				combined_vec = abstract_vec
			elif methodology_vec is not None:
				combined_vec = methodology_vec
			else:
				# Fallback: encode entire content
				combined_vec = embeddings_model.encode([content])[0]
			
			# Extract metadata
			technique = _guess_technique(title, content)
			architecture = model_info.get('architecture_type', 'Unknown')
			implementation_status = self._extract_implementation_status(paper)
			
			metadata = {
				'title': title,
				'url': paper.get('url', ''),
				'source': paper.get('source', ''),
				'citations': paper.get('citations', 0),
				'stars': paper.get('stars', 0),
				'techniques': technique,
				'architecture': architecture,
				'implementation_status': implementation_status,
				'abstract': abstract[:500] if abstract else '',  # Store truncated abstract
				'methodology_extracted': bool(methodology),
			}
			
			vectors_list.append(combined_vec)
			metadatas_list.append(metadata)
		
		if vectors_list:
			# Convert to numpy array
			vectors = np.array(vectors_list, dtype=np.float32)
			
			# Add to database
			self.add(vectors, metadatas_list)
			
			print(f"✓ Added {len(vectors_list)} papers with enhanced metadata")
		else:
			print("⚠️  No valid papers to add")

	def query(self, query_vec: np.ndarray, top_k: int = 5) -> List[Tuple[float, Dict]]:
		"""Query similar vectors.
		
		Args:
			query_vec: Query embedding vector
			top_k: Number of results to return
			
		Returns:
			List of (similarity_score, metadata) tuples
		"""
		if self._emb is None:
			self.load()
		if self._emb.size == 0:
			return []
		if query_vec.ndim == 1:
			query_vec = query_vec[None, :]
		
		query_vec = query_vec.astype(np.float32)
		
		# Use HNSW index if available, otherwise fall back to cosine similarity
		if self.use_hnsw and self._hnsw_index is not None:
			return self._query_hnsw(query_vec[0], top_k)
		else:
			sims = self._cosine_sim(query_vec, self._emb)[0]
			idx = np.argsort(-sims)[:top_k]
			return [(float(sims[i]), self._meta[i]) for i in idx]
	
	def _update_hnsw_index(self, new_vectors: np.ndarray):
		"""Update HNSW index with new vectors.
		
		Args:
			new_vectors: New embedding vectors to add
		"""
		if not self.use_hnsw:
			return
		
		try:
			# Normalize vectors for cosine similarity
			norms = np.linalg.norm(new_vectors, axis=1, keepdims=True)
			normalized = new_vectors / (norms + 1e-12)
			
			# Create or update index
			if self._hnsw_index is None:
				# Create new index
				index = faiss.IndexHNSWFlat(self.embedding_dim, self.hnsw_m)
				index.hnsw.efConstruction = self.ef_construction
				
				# Add existing embeddings if any
				if self._emb is not None and self._emb.size > 0:
					existing_norms = np.linalg.norm(self._emb, axis=1, keepdims=True)
					existing_normalized = self._emb / (existing_norms + 1e-12)
					index.add(existing_normalized.astype(np.float32))
				
				self._hnsw_index = index
			
			# Add new vectors
			self._hnsw_index.add(normalized.astype(np.float32))
		except Exception as e:
			print(f"⚠️  Failed to update HNSW index: {e}")
			self.use_hnsw = False
	
	def _query_hnsw(self, query_vec: np.ndarray, top_k: int) -> List[Tuple[float, Dict]]:
		"""Query using HNSW index.
		
		Args:
			query_vec: Query embedding vector
			top_k: Number of results
			
		Returns:
			List of (similarity_score, metadata) tuples
		"""
		if self._hnsw_index is None:
			# Fallback to cosine similarity
			sims = self._cosine_sim(query_vec[None, :], self._emb)[0]
			idx = np.argsort(-sims)[:top_k]
			return [(float(sims[i]), self._meta[i]) for i in idx]
		
		# Normalize query vector
		query_norm = np.linalg.norm(query_vec)
		normalized_query = (query_vec / (query_norm + 1e-12)).astype(np.float32)
		
		# Set ef_search for better recall
		self._hnsw_index.hnsw.efSearch = max(top_k * 2, 50)
		
		# Search
		distances, indices = self._hnsw_index.search(normalized_query[None, :], top_k)
		
		# Convert distances to similarities (HNSW returns squared L2 distances for normalized vectors)
		# For cosine similarity on normalized vectors: sim = 1 - dist^2 / 2
		results = []
		for dist, idx in zip(distances[0], indices[0]):
			if idx >= 0 and idx < len(self._meta):
				# Convert L2 distance to cosine similarity
				similarity = float(1.0 - (dist / 2.0))
				results.append((similarity, self._meta[idx]))
		
		return results
