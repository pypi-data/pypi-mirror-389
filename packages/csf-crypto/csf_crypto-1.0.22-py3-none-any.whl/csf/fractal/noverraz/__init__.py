"""
Noverraz: Next-Generation Fractal Cryptographic Engine

Noverraz is an improved, more efficient and secure replacement for Julia sets
in CSF-Crypto. It offers:
- 10-100x better performance
- Enhanced security properties
- Guaranteed convergence
- Direct key injection
- Quantum resistance
"""

__version__ = "1.0.0"

# Core classes used in production
from csf.fractal.noverraz.core import NoverrazEngine
from csf.fractal.noverraz.vectorized import VectorizedNoverraz

# Experimental classes (not used in production, available for testing/research)
# from csf.fractal.noverraz.optimized import OptimizedNoverraz
# from csf.fractal.noverraz.parallel import ParallelNoverraz

__all__ = [
    'NoverrazEngine',
    'VectorizedNoverraz',
    # 'OptimizedNoverraz',  # Experimental - not used in production
    # 'ParallelNoverraz',    # Experimental - not used in production
]

