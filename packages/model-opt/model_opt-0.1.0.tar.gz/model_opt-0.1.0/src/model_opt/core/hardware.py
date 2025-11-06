"""Hardware abstraction layer for GPU/CPU resource management and optimization targets."""
from typing import Dict, List, Optional, Tuple, Any
from .exceptions import HardwareError
from .environment import get_environment_manager


class HardwareManager:
    """Manages GPU/CPU resources and optimization targets."""
    
    def __init__(self):
        """Initialize hardware manager."""
        self.env_manager = get_environment_manager()
        self._devices: List[Dict] = []
        self._current_device: Optional[str] = None
        self._scan_devices()
    
    def _scan_devices(self):
        """Scan available hardware devices."""
        self._devices = []
        
        # Scan CPU
        import platform
        cpu_info = {
            'type': 'cpu',
            'name': platform.processor() or 'Unknown',
            'available': True,
            'memory_total_gb': self._get_cpu_memory(),
        }
        self._devices.append(cpu_info)
        
        # Scan GPUs
        if self.env_manager.is_cuda_available():
            cuda_info = self.env_manager.get_cuda_info()
            for device_info in cuda_info.get('devices', []):
                gpu_info = {
                    'type': 'cuda',
                    'name': device_info['name'],
                    'index': device_info['index'],
                    'available': True,
                    'memory_total_gb': device_info['memory_total_gb'],
                    'compute_capability': device_info['compute_capability'],
                }
                self._devices.append(gpu_info)
    
    def _get_cpu_memory(self) -> float:
        """Get CPU memory in GB.
        
        Returns:
            Memory in GB
        """
        try:
            import psutil
            return psutil.virtual_memory().total / (1024**3)
        except (ImportError, Exception):
            # Fallback - approximate
            return 8.0  # Default assumption
    
    def get_devices(self) -> List[Dict]:
        """Get list of available devices.
        
        Returns:
            List of device information dictionaries
        """
        return self._devices.copy()
    
    def get_device(self, device_name: Optional[str] = None) -> Dict:
        """Get device information.
        
        Args:
            device_name: Device name (e.g., 'cuda:0', 'cpu'). If None, returns default.
            
        Returns:
            Device information dictionary
            
        Raises:
            HardwareError: If device is not available
        """
        if device_name is None:
            # Default to first available GPU or CPU
            for device in self._devices:
                if device['type'] == 'cuda' and device['available']:
                    return device
            return self._devices[0]  # CPU
        
        if device_name == 'cpu':
            for device in self._devices:
                if device['type'] == 'cpu':
                    return device
            raise HardwareError("CPU device not found")
        
        if device_name.startswith('cuda'):
            # Parse cuda:0 format
            if ':' in device_name:
                index = int(device_name.split(':')[1])
            else:
                index = 0
            
            for device in self._devices:
                if device['type'] == 'cuda' and device.get('index') == index:
                    return device
            
            raise HardwareError(f"CUDA device {index} not available")
        
        raise HardwareError(f"Unknown device: {device_name}")
    
    def set_device(self, device_name: str):
        """Set current device.
        
        Args:
            device_name: Device name
            
        Raises:
            HardwareError: If device is not available
        """
        device = self.get_device(device_name)
        if not device['available']:
            raise HardwareError(f"Device {device_name} is not available")
        self._current_device = device_name
    
    def get_current_device(self) -> str:
        """Get current device name.
        
        Returns:
            Current device name
        """
        if self._current_device is None:
            # Auto-select device
            if self.env_manager.is_cuda_available():
                self._current_device = 'cuda:0'
            else:
                self._current_device = 'cpu'
        return self._current_device
    
    def get_optimization_target(
        self,
        device_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get optimization target for device.
        
        Args:
            device_name: Device name. If None, uses current device.
            
        Returns:
            Optimization target dictionary with device-specific settings
        """
        device = self.get_device(device_name or self.get_current_device())
        
        target = {
            'device': device_name or self.get_current_device(),
            'device_type': device['type'],
            'memory_limit_gb': device.get('memory_total_gb', 0),
        }
        
        if device['type'] == 'cuda':
            target['compute_capability'] = device.get('compute_capability')
            target['supports_mixed_precision'] = True
            target['supports_tensor_cores'] = self._supports_tensor_cores(
                device.get('compute_capability', '0.0')
            )
        else:
            target['supports_mixed_precision'] = False
            target['supports_tensor_cores'] = False
        
        return target
    
    def _supports_tensor_cores(self, compute_capability: str) -> bool:
        """Check if device supports Tensor Cores.
        
        Args:
            compute_capability: Compute capability string (e.g., '7.0')
            
        Returns:
            True if Tensor Cores are supported
        """
        try:
            major = float(compute_capability.split('.')[0])
            return major >= 7.0  # Tensor Cores available from compute capability 7.0+
        except:
            return False
    
    def monitor_resources(self, device_name: Optional[str] = None) -> Dict[str, Any]:
        """Monitor current resource usage.
        
        Args:
            device_name: Device name. If None, monitors current device.
            
        Returns:
            Resource usage dictionary
        """
        device = self.get_device(device_name or self.get_current_device())
        
        if device['type'] == 'cuda':
            return self._monitor_cuda(device.get('index', 0))
        else:
            return self._monitor_cpu()
    
    def _monitor_cuda(self, device_index: int) -> Dict[str, Any]:
        """Monitor CUDA device resources.
        
        Args:
            device_index: CUDA device index
            
        Returns:
            Resource usage dictionary
        """
        try:
            import torch
            if not torch.cuda.is_available():
                return {'error': 'CUDA not available'}
            
            torch.cuda.set_device(device_index)
            memory_allocated = torch.cuda.memory_allocated(device_index) / (1024**3)
            memory_reserved = torch.cuda.memory_reserved(device_index) / (1024**3)
            memory_total = torch.cuda.get_device_properties(device_index).total_memory / (1024**3)
            
            return {
                'device_index': device_index,
                'memory_allocated_gb': memory_allocated,
                'memory_reserved_gb': memory_reserved,
                'memory_total_gb': memory_total,
                'memory_free_gb': memory_total - memory_reserved,
                'utilization_percent': (memory_reserved / memory_total) * 100 if memory_total > 0 else 0,
            }
        except ImportError:
            return {'error': 'PyTorch not available'}
        except Exception as e:
            return {'error': str(e)}
    
    def _monitor_cpu(self) -> Dict[str, Any]:
        """Monitor CPU resources.
        
        Returns:
            Resource usage dictionary
        """
        try:
            import psutil
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            return {
                'memory_used_gb': memory.used / (1024**3),
                'memory_total_gb': memory.total / (1024**3),
                'memory_percent': memory.percent,
                'cpu_percent': cpu_percent,
            }
        except (ImportError, Exception) as e:
            return {'error': f'psutil not available: {str(e)}'}
    
    def set_memory_limit(
        self,
        device_name: Optional[str] = None,
        limit_gb: Optional[float] = None
    ):
        """Set memory limit for device.
        
        Args:
            device_name: Device name. If None, uses current device.
            limit_gb: Memory limit in GB. If None, removes limit.
            
        Raises:
            HardwareError: If operation fails
        """
        device = self.get_device(device_name or self.get_current_device())
        
        if device['type'] == 'cuda':
            try:
                import torch
                if limit_gb is None:
                    # Clear memory limit
                    torch.cuda.empty_cache()
                else:
                    # Set memory fraction
                    memory_limit = limit_gb * (1024**3)
                    total_memory = device.get('memory_total_gb', 0) * (1024**3)
                    fraction = min(1.0, memory_limit / total_memory) if total_memory > 0 else 1.0
                    torch.cuda.set_per_process_memory_fraction(fraction, device.get('index', 0))
            except ImportError:
                raise HardwareError("PyTorch not available for memory management")
            except Exception as e:
                raise HardwareError(f"Failed to set memory limit: {e}")


def get_hardware_manager() -> HardwareManager:
    """Get or create global hardware manager instance.
    
    Returns:
        HardwareManager instance
    """
    if '_hardware_manager' not in globals():
        globals()['_hardware_manager'] = HardwareManager()
    return globals()['_hardware_manager']

