#!/usr/bin/env python
"""Quick verification script to check if package can be imported correctly."""

import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 70)
print("Package Verification")
print("=" * 70)

try:
    import model_opt
    print(f"✓ Package imported successfully")
    print(f"  Version: {model_opt.__version__}")
except ImportError as e:
    print(f"✗ Failed to import package: {e}")
    sys.exit(1)

# Test core imports
print("\nCore Modules:")
try:
    from model_opt import Optimizer, analyze_model
    print("  ✓ Optimizer")
    print("  ✓ analyze_model")
except ImportError as e:
    print(f"  ✗ Core imports failed: {e}")

# Test optional imports
print("\nOptional Modules:")
optional_modules = {
    'IntelligentOptimizer': 'autotuner',
    'ResearchAgent': 'agent',
    'Quantizer': 'techniques',
    'Pruner': 'techniques',
    'LayerFuser': 'techniques',
    'Decomposer': 'techniques',
}

for module_name, category in optional_modules.items():
    try:
        module = getattr(model_opt, module_name, None)
        if module is not None:
            print(f"  ✓ {module_name} ({category})")
        else:
            print(f"  ⚠ {module_name} ({category}) - Not available (dependencies may be missing)")
    except Exception as e:
        print(f"  ⚠ {module_name} ({category}) - Error: {e}")

print("\n" + "=" * 70)
print("Verification complete!")
print("=" * 70)

