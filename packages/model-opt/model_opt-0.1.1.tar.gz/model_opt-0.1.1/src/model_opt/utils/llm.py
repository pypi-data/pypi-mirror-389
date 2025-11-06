import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import requests


def _load_dotenv():
	"""Load .env file from project root if present"""
	env_path = Path(__file__).parent.parent.parent.parent / '.env'
	if env_path.exists():
		try:
			with open(env_path, 'r', encoding='utf-8') as f:
				for line in f:
					line = line.strip()
					if not line or line.startswith('#'):
						continue
					if '=' in line:
						k, v = line.split('=', 1)
						os.environ[k.strip()] = v.strip().strip('"').strip("'")
		except Exception:
			pass


# Load .env on import
_load_dotenv()


class LLMClient:
	"""Unified LLM client for OpenAI, Together, Google, or local vLLM (OpenAI-compatible)."""

	def __init__(self, provider: str, model: str, base_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
		self.provider = provider.lower()
		self.model = model
		self.base_url = base_url
		self.api_key = api_key or self._get_default_key()

	def _get_default_key(self) -> Optional[str]:
		if self.provider == 'openai':
			return os.environ.get('OPENAI_API_KEY')
		if self.provider == 'together':
			return os.environ.get('TOGETHER_API_KEY')
		if self.provider == 'google':
			return os.environ.get('GOOGLE_API_KEY')
		# vLLM local may not require a key
		return None

	def test_api_key(self) -> Tuple[bool, str]:
		"""Test API key with a simple request. Returns (success, message)."""
		if self.provider == 'vllm':
			# vLLM might not require auth; just check if server is reachable
			if self.base_url:
				try:
					resp = requests.get(self.base_url.rstrip('/v1') + '/health', timeout=5)
					if resp.status_code == 200:
						return True, "Local vLLM server reachable"
					return False, f"Server returned {resp.status_code}"
				except:
					return False, "Cannot reach local vLLM server"
			return True, "vLLM (no key check)"
		if not self.api_key:
			key_name = {
				'openai': 'OPENAI_API_KEY',
				'together': 'TOGETHER_API_KEY',
				'google': 'GOOGLE_API_KEY',
			}.get(self.provider, 'API_KEY')
			return False, f"Missing {key_name}. Set in .env or use --llm-api-key"
		# Test with a tiny generation (reuse generate code)
		try:
			self.generate("Hi", max_tokens=3, temperature=0.1)
			return True, "API key valid"
		except requests.HTTPError as e:
			if e.response and e.response.status_code == 401:
				return False, "API key invalid (401 Unauthorized)"
			return False, f"API error: {e}"
		except Exception as e:
			return False, f"Connection error: {e}"

	def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.2) -> str:
		if self.provider in ('openai', 'together') or (self.provider == 'vllm'):
			return self._generate_openai_compatible(prompt, max_tokens, temperature)
		elif self.provider == 'google':
			return self._generate_google(prompt, max_tokens, temperature)
		else:
			raise ValueError(f"Unsupported provider: {self.provider}")

	def complete(self, system: str = "", prompt: str = "", max_tokens: int = 512, temperature: float = 0.2) -> str:
		"""Complete method compatible with analyzer_agent interface.
		
		Args:
			system: System prompt/instructions.
			prompt: User prompt.
			max_tokens: Maximum tokens to generate.
			temperature: Sampling temperature.
		
		Returns:
			Generated text.
		"""
		if self.provider in ('openai', 'together') or (self.provider == 'vllm'):
			return self._generate_openai_compatible_with_system(system, prompt, max_tokens, temperature)
		elif self.provider == 'google':
			# Google doesn't separate system/user, combine them
			combined = f"{system}\n\n{prompt}" if system else prompt
			return self._generate_google(combined, max_tokens, temperature)
		else:
			# Fallback to generate with combined prompt
			combined = f"{system}\n\n{prompt}" if system else prompt
			return self.generate(combined, max_tokens, temperature)

	def _generate_openai_compatible(self, prompt: str, max_tokens: int, temperature: float) -> str:
		"""Generate with default system message."""
		return self._generate_openai_compatible_with_system(
			'You are a helpful AI assistant for model optimization.',
			prompt,
			max_tokens,
			temperature
		)

	def _generate_openai_compatible_with_system(self, system: str, prompt: str, max_tokens: int, temperature: float) -> str:
		"""Generate with custom system message."""
		url = (self.base_url or 'https://api.openai.com/v1') + '/chat/completions'
		headers = {
			'Content-Type': 'application/json'
		}
		if self.api_key:
			headers['Authorization'] = f"Bearer {self.api_key}"
		messages = []
		if system:
			messages.append({'role': 'system', 'content': system})
		messages.append({'role': 'user', 'content': prompt})
		payload: Dict[str, Any] = {
			'model': self.model,
			'messages': messages,
			'max_tokens': max_tokens,
			'temperature': temperature
		}
		resp = requests.post(url, json=payload, headers=headers, timeout=60)
		resp.raise_for_status()
		data = resp.json()
		return data['choices'][0]['message']['content']

	def _generate_google(self, prompt: str, max_tokens: int, temperature: float) -> str:
		# Gemini 1.5 REST (text-only simple endpoint)
		api_key = self.api_key
		if not api_key:
			raise ValueError('GOOGLE_API_KEY not set')
		model = self.model or 'gemini-1.5-flash'
		url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
		payload = {
			"contents": [
				{"parts": [{"text": prompt}]}
			],
			"generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}
		}
		resp = requests.post(url, json=payload, timeout=60)
		resp.raise_for_status()
		data = resp.json()
		return data['candidates'][0]['content']['parts'][0]['text']
