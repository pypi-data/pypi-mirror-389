"""Environment manager for CUDA detection, dependency validation, and compatibility checks."""
from typing import Dict, List, Tuple, Optional
from .exceptions import EnvironmentError, HardwareError


class EnvironmentManager:
    """Manages environment detection, validation, and compatibility checks."""
    
    def __init__(self):
        """Initialize environment manager."""
        self._cuda_info: Optional[Dict] = None
        self._dependencies: Dict[str, bool] = {}
        self._validate()
    
    def _validate(self):
        """Validate environment on initialization."""
        self._check_cuda()
        self._check_dependencies()
    
    def _check_cuda(self) -> bool:
        """Check CUDA availability and version.
        
        Returns:
            True if CUDA is available
        """
        try:
            import torch
            if torch.cuda.is_available():
                cuda_version = torch.version.cuda
                # Check for CUDA 12.1 specifically
                cuda_12_1_available = cuda_version.startswith('12.1')
                
                self._cuda_info = {
                    'available': True,
                    'version': cuda_version,
                    'cuda_12_1': cuda_12_1_available,
                    'device_count': torch.cuda.device_count(),
                    'devices': []
                }
                for i in range(torch.cuda.device_count()):
                    props = torch.cuda.get_device_properties(i)
                    self._cuda_info['devices'].append({
                        'index': i,
                        'name': props.name,
                        'memory_total_gb': props.total_memory / (1024**3),
                        'compute_capability': f"{props.major}.{props.minor}"
                    })
                return True
            else:
                self._cuda_info = {'available': False}
                return False
        except ImportError:
            self._cuda_info = {'available': False, 'error': 'PyTorch not installed'}
            return False
    
    def _check_dependencies(self):
        """Check availability of optional dependencies."""
        dependencies = {
            'pytorch': self._check_pytorch(),
            'tensorflow': self._check_tensorflow(),
            'jax': self._check_jax(),
            'torchao': self._check_torchao(),
            'torch_pruning': self._check_torch_pruning(),
            'timm': self._check_timm(),
            # New optimization frameworks
            'nncf': self._check_nncf(),
            'neural_compressor': self._check_neural_compressor(),
            'ultralytics': self._check_ultralytics(),
            # Database backends
            'mongodb': self._check_mongodb(),
            'redis': self._check_redis(),
            'neo4j': self._check_neo4j(),
            'chromadb': self._check_chromadb(),
            # Evaluation
            'pycocotools': self._check_pycocotools(),
        }
        self._dependencies = dependencies
    
    def _check_pytorch(self) -> bool:
        """Check if PyTorch is installed."""
        try:
            import torch
            return True
        except ImportError:
            return False
    
    def _check_tensorflow(self) -> bool:
        """Check if TensorFlow is installed."""
        try:
            import tensorflow
            return True
        except ImportError:
            return False
    
    def _check_jax(self) -> bool:
        """Check if JAX is installed."""
        try:
            import jax
            return True
        except ImportError:
            return False
    
    def _check_torchao(self) -> bool:
        """Check if TorchAO is installed."""
        try:
            import torchao
            return True
        except ImportError:
            return False
    
    def _check_torch_pruning(self) -> bool:
        """Check if torch-pruning is installed."""
        try:
            import torch_pruning
            return True
        except ImportError:
            return False
    
    def _check_timm(self) -> bool:
        """Check if timm is installed."""
        try:
            import timm
            return True
        except ImportError:
            return False
    
    def _check_nncf(self) -> bool:
        """Check if NNCF is installed."""
        try:
            import nncf
            return True
        except ImportError:
            return False
    
    def _check_neural_compressor(self) -> bool:
        """Check if Intel Neural Compressor is installed."""
        try:
            import neural_compressor
            return True
        except ImportError:
            return False
    
    def _check_ultralytics(self) -> bool:
        """Check if ultralytics is installed."""
        try:
            import ultralytics
            return True
        except ImportError:
            return False
    
    def _check_mongodb(self) -> bool:
        """Check if pymongo is installed."""
        try:
            import pymongo
            return True
        except ImportError:
            return False
    
    def _check_redis(self) -> bool:
        """Check if redis is installed."""
        try:
            import redis
            return True
        except ImportError:
            return False
    
    def _check_neo4j(self) -> bool:
        """Check if neo4j driver is installed."""
        try:
            from neo4j import GraphDatabase
            return True
        except ImportError:
            return False
    
    def _check_chromadb(self) -> bool:
        """Check if chromadb is installed."""
        try:
            import chromadb
            return True
        except ImportError:
            return False
    
    def _check_pycocotools(self) -> bool:
        """Check if pycocotools is installed."""
        try:
            import pycocotools
            return True
        except ImportError:
            return False
    
    def get_cuda_info(self) -> Dict:
        """Get CUDA information.
        
        Returns:
            Dictionary with CUDA availability and device info
        """
        if self._cuda_info is None:
            self._check_cuda()
        return self._cuda_info.copy() if self._cuda_info else {}
    
    def is_cuda_available(self) -> bool:
        """Check if CUDA is available.
        
        Returns:
            True if CUDA is available
        """
        info = self.get_cuda_info()
        return info.get('available', False)
    
    def get_dependencies(self) -> Dict[str, bool]:
        """Get dependency availability status.
        
        Returns:
            Dictionary mapping dependency names to availability
        """
        return self._dependencies.copy()
    
    def check_dependency(self, name: str) -> bool:
        """Check if a specific dependency is available.
        
        Args:
            name: Dependency name
            
        Returns:
            True if dependency is available
            
        Raises:
            EnvironmentError: If dependency is required but not available
        """
        return self._dependencies.get(name, False)
    
    def require_dependency(self, name: str):
        """Require a dependency to be available.
        
        Args:
            name: Dependency name
            
        Raises:
            EnvironmentError: If dependency is not available
        """
        if not self.check_dependency(name):
            raise EnvironmentError(
                f"Required dependency '{name}' is not installed. "
                f"Install with: pip install {name}"
            )
    
    def check_compatibility(
        self,
        framework: str,
        device: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Check compatibility between framework and device.
        
        Args:
            framework: Framework name (pytorch, tensorflow, jax)
            device: Device name (cuda, cpu, etc.)
            
        Returns:
            Tuple of (is_compatible, error_message)
        """
        if device and device.startswith('cuda'):
            if not self.is_cuda_available():
                return False, "CUDA is not available"
            
            if framework not in ['pytorch', 'tensorflow']:
                if framework == 'jax':
                    # JAX can use CUDA but needs separate check
                    if not self.check_dependency('jax'):
                        return False, "JAX is not installed"
                else:
                    return False, f"Framework '{framework}' does not support CUDA"
        
        if framework == 'pytorch' and not self.check_dependency('pytorch'):
            return False, "PyTorch is not installed"
        elif framework == 'tensorflow' and not self.check_dependency('tensorflow'):
            return False, "TensorFlow is not installed"
        elif framework == 'jax' and not self.check_dependency('jax'):
            return False, "JAX is not installed"
        
        return True, None
    
    def get_environment_info(self) -> Dict:
        """Get comprehensive environment information.
        
        Returns:
            Dictionary with environment information
        """
        import sys
        import platform
        
        info = {
            'python_version': sys.version,
            'platform': platform.platform(),
            'cuda': self.get_cuda_info(),
            'dependencies': self.get_dependencies(),
        }
        
        # Add framework versions if available
        if self.check_dependency('pytorch'):
            try:
                import torch
                info['pytorch_version'] = torch.__version__
            except:
                pass
        
        if self.check_dependency('tensorflow'):
            try:
                import tensorflow as tf
                info['tensorflow_version'] = tf.__version__
            except:
                pass
        
        if self.check_dependency('jax'):
            try:
                import jax
                info['jax_version'] = jax.__version__
            except:
                pass
        
        return info


def get_environment_manager() -> EnvironmentManager:
    """Get or create global environment manager instance.
    
    Returns:
        EnvironmentManager instance
    """
    if '_env_manager' not in globals():
        globals()['_env_manager'] = EnvironmentManager()
    return globals()['_env_manager']

