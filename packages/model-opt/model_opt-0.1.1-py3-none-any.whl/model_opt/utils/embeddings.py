from typing import List, Optional, Dict, Any
import numpy as np

try:
	from sentence_transformers import SentenceTransformer
	_SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
	_SENTENCE_TRANSFORMERS_AVAILABLE = False
	SentenceTransformer = None

try:
	import chromadb
	from chromadb.config import Settings
	_CHROMADB_AVAILABLE = True
except (ImportError, AttributeError):
	# ImportError: chromadb not installed
	# AttributeError: chromadb incompatible with numpy 2.0 (np.float_ removed)
	_CHROMADB_AVAILABLE = False
	chromadb = None
	Settings = None


class Embeddings:
	"""Wrapper for sentence-transformers embedding model with ChromaDB integration."""

	def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
		"""Initialize embeddings model.
		
		Args:
			model_name: Sentence transformer model name
		"""
		if not _SENTENCE_TRANSFORMERS_AVAILABLE:
			raise ImportError(
				"sentence-transformers>=2.2.0 is required. "
				"Install with: pip install sentence-transformers>=2.2.0"
			)
		self.model = SentenceTransformer(model_name)
		self.model_name = model_name

	def encode(self, texts: List[str]) -> np.ndarray:
		"""Encode texts to embeddings.
		
		Args:
			texts: List of text strings
			
		Returns:
			Numpy array of embeddings
		"""
		if not texts:
			return np.empty((0, self.get_dimension()), dtype=np.float32)
		vectors = self.model.encode(
			texts,
			convert_to_numpy=True,
			normalize_embeddings=True,
			show_progress_bar=False
		)
		return np.asarray(vectors, dtype=np.float32)
	
	def get_dimension(self) -> int:
		"""Get the embedding dimension.
		
		Returns:
			Embedding dimension
		"""
		try:
			return self.model.get_sentence_embedding_dimension()
		except AttributeError:
			# Fallback: encode a test text to get dimension
			test_vec = self.model.encode(['test'], convert_to_numpy=True)
			return test_vec.shape[1]


class ChromaDBEmbeddings:
	"""Embeddings with ChromaDB integration for vector storage."""
	
	def __init__(
		self,
		model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
		collection_name: str = "embeddings",
		persist_directory: Optional[str] = None
	):
		"""Initialize ChromaDB embeddings.
		
		Args:
			model_name: Sentence transformer model name
			collection_name: ChromaDB collection name
			persist_directory: Optional directory for persistence
		"""
		if not _SENTENCE_TRANSFORMERS_AVAILABLE:
			raise ImportError(
				"sentence-transformers>=2.2.0 is required. "
				"Install with: pip install sentence-transformers>=2.2.0"
			)
		
		self.embeddings = Embeddings(model_name)
		
		if _CHROMADB_AVAILABLE:
			if persist_directory:
				self.client = chromadb.PersistentClient(
					path=persist_directory,
					settings=Settings(anonymized_telemetry=False)
				)
			else:
				self.client = chromadb.Client(
					settings=Settings(anonymized_telemetry=False)
				)
			
			# Get or create collection
			self.collection = self.client.get_or_create_collection(
				name=collection_name,
				metadata={"hnsw:space": "cosine"}
			)
		else:
			self.client = None
			self.collection = None
	
	def encode(self, texts: List[str]) -> np.ndarray:
		"""Encode texts to embeddings.
		
		Args:
			texts: List of text strings
			
		Returns:
			Numpy array of embeddings
		"""
		return self.embeddings.encode(texts)
	
	def add(
		self,
		ids: List[str],
		texts: List[str],
		metadatas: Optional[List[Dict[str, Any]]] = None
	):
		"""Add embeddings to ChromaDB.
		
		Args:
			ids: List of document IDs
			texts: List of text strings
			metadatas: Optional list of metadata dictionaries
		"""
		if self.collection is None:
			raise ImportError("ChromaDB is not available")
		
		embeddings = self.encode(texts)
		
		# Convert to list of lists for ChromaDB
		embeddings_list = embeddings.tolist()
		
		self.collection.add(
			ids=ids,
			embeddings=embeddings_list,
			documents=texts,
			metadatas=metadatas or [{}] * len(texts)
		)
	
	def query(
		self,
		query_texts: List[str],
		n_results: int = 10,
		where: Optional[Dict] = None
	) -> Dict[str, Any]:
		"""Query similar embeddings from ChromaDB.
		
		Args:
			query_texts: List of query text strings
			n_results: Number of results to return
			where: Optional metadata filter
			
		Returns:
			Query results dictionary
		"""
		if self.collection is None:
			raise ImportError("ChromaDB is not available")
		
		query_embeddings = self.encode(query_texts).tolist()
		
		results = self.collection.query(
			query_embeddings=query_embeddings,
			n_results=n_results,
			where=where
		)
		
		return results
