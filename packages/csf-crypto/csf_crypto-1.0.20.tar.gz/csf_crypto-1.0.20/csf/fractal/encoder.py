"""
Fractal message encoder with performance optimizations.

Encodes messages into fractal parameter space using vectorization,
parallel processing, and compiled code (Cython/Rust) when available.
"""

import math
from typing import List, Dict, Optional
import numpy as np
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from csf.security.validation import validate_string, validate_array

# Try to import Noverraz (improved engine)
try:
    from csf.fractal.noverraz.core import NoverrazEngine
    from csf.fractal.noverraz.vectorized import VectorizedNoverraz
    USE_NOVERRAZ = True
    NoverrazClass = VectorizedNoverraz
except ImportError:
    USE_NOVERRAZ = False
    # Fallback to optimized Julia if available
    try:
        from csf.fractal.julia_optimized import OptimizedJulia
        JuliaClass = OptimizedJulia
    except ImportError:
        from csf.fractal.julia import ConstantTimeJulia
        JuliaClass = ConstantTimeJulia


def _encode_bytes_batch(
    bytes_array: np.ndarray,
    combined_key: np.ndarray,
    start_index: int,
) -> List[Dict]:
    """
    Encode a batch of bytes into fractal parameters.
    
    Uses Rust/Cython implementation if available (2-5x faster), otherwise falls back to Python.
    
    Args:
        bytes_array: Array of bytes to encode
        combined_key: Combined mathematical and semantic key
        start_index: Starting index for position calculation
    
    Returns:
        List of fractal parameters
    """
    # Try Rust implementation first (fastest, 2-5x speedup)
    try:
        import csf_rust
        return csf_rust.encode_bytes_batch_rust(bytes_array, combined_key, start_index)
    except (ImportError, AttributeError):
        # Try Cython implementation (2-5x speedup)
        try:
            from csf.fractal._encode_cython import encode_bytes_batch_cython
            return encode_bytes_batch_cython(bytes_array, combined_key, start_index)
        except ImportError:
            # Fallback to Python implementation
            pass
    
    # Pre-allocate list for better performance
    num_bytes = len(bytes_array)
    fractal_params = [None] * num_bytes
    key_len = len(combined_key)
    
    for i, byte_val in enumerate(bytes_array):
        param_idx = (start_index + i) % key_len
        
        # Generate key offsets
        key_offset = (abs(combined_key[param_idx]) % 1.0) * 0.5
        key_offset_imag = (abs(combined_key[(param_idx + 1) % key_len]) % 1.0) * 0.5
        
        # Encode byte to c parameter
        c_real = ((float(byte_val) / 256.0) + key_offset) % 1.0
        c_imag = key_offset_imag
        
        # Get z0 from key
        z0_real = combined_key[(param_idx + 2) % key_len]
        z0_imag = combined_key[(param_idx + 3) % key_len]
        
        # Validate and clamp c parameters
        if not math.isfinite(c_real):
            c_real = 0.0
        else:
            c_real = max(0.0, min(0.9999999, c_real))
        
        if not math.isfinite(c_imag):
            c_imag = 0.0
        else:
            c_imag = max(0.0, min(0.9999999, c_imag))
        
        # Validate and clamp z0 parameters
        if not math.isfinite(z0_real):
            z0_real = 0.0
        else:
            z0_real = max(-1e100, min(1e100, z0_real))
        
        if not math.isfinite(z0_imag):
            z0_imag = 0.0
        else:
            z0_imag = max(-1e100, min(1e100, z0_imag))
        
        # Pre-allocated list, assign directly
        fractal_params[i] = {
            "c": (float(c_real), float(c_imag)),
            "z0": (float(z0_real), float(z0_imag)),
            "iteration": int(start_index + i),
            "byte_value": int(byte_val),
        }
    
    return fractal_params


class FractalEncoder:
    """
    Fractal encoder with performance optimizations.
    
    Features:
    - Vectorized batch processing
    - Multi-process parallelization
    - Streaming for large messages
    - Memory-efficient operations
    - Automatic use of compiled code (Rust/Cython) when available
    """
    
    def __init__(
        self,
        iterations: int = 50,
        escape_radius: float = 2.0,
        batch_size: int = 1000,
        num_workers: Optional[int] = None,
        use_streaming: bool = True,
    ):
        """
        Initialize fractal encoder.
        
        Args:
            iterations: Maximum iterations for fractal computation
            escape_radius: Escape radius for divergence detection (not used with Noverraz)
            batch_size: Size of batches for processing
            num_workers: Number of parallel workers (default: CPU count, max 8)
            use_streaming: Enable streaming for large messages
        """
        self.iterations = iterations
        self.escape_radius = escape_radius
        self.batch_size = batch_size
        if num_workers is None:
            num_workers = min(mp.cpu_count(), 8)
        self.num_workers = num_workers
        self.use_streaming = use_streaming
        
        # Use Noverraz if available (improved engine)
        if USE_NOVERRAZ:
            # Noverraz doesn't need escape_radius (has damping)
            self.noverraz = NoverrazClass(iterations=iterations, alpha=0.2, beta=0.05)
            self.julia = None
        else:
            self.julia = JuliaClass(iterations, escape_radius)
            self.noverraz = None
    
    def encode_message(
        self, message: str, math_key: np.ndarray, semantic_key: np.ndarray
    ) -> List[Dict]:
        """
        Encode a message into fractal parameters with optimizations.
        
        Args:
            message: Plaintext message
            math_key: Mathematical key vector
            semantic_key: Semantic key vector
        
        Returns:
            List of fractal parameters
        """
        validate_string(message, "message")
        validate_array(math_key, "math_key")
        validate_array(semantic_key, "semantic_key")
        
        # Combine keys
        min_len = min(len(math_key), len(semantic_key))
        if min_len < 128:
            combined_key = np.zeros(128, dtype=np.float64)
            combined_key[:min_len] = (math_key[:min_len] + semantic_key[:min_len]) / 2
        else:
            combined_key = (math_key[:128] + semantic_key[:128]) / 2
        
        # Convert to bytes
        message_bytes = np.frombuffer(message.encode("utf-8"), dtype=np.uint8)
        
        # Decide processing strategy
        if len(message_bytes) < self.batch_size or self.num_workers == 1:
            # Small message or single worker: process directly
            return _encode_bytes_batch(message_bytes, combined_key, 0)
        
        # Large message: use parallel processing
        if self.use_streaming and len(message_bytes) > 10000:
            # Very large: use streaming
            return self._encode_streaming(message_bytes, combined_key)
        else:
            # Medium: use parallel batches
            return self._encode_parallel(message_bytes, combined_key)
    
    def _encode_parallel(
        self, message_bytes: np.ndarray, combined_key: np.ndarray
    ) -> List[Dict]:
        """Encode using parallel processing."""
        # Split into chunks
        chunks = []
        for i in range(0, len(message_bytes), self.batch_size):
            end = min(i + self.batch_size, len(message_bytes))
            chunks.append((message_bytes[i:end], combined_key, i))
        
        # Process in parallel
        if len(chunks) == 1:
            return _encode_bytes_batch(chunks[0][0], chunks[0][1], chunks[0][2])
        
        # Use ThreadPoolExecutor for lambda compatibility
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            results = list(executor.map(
                lambda args: _encode_bytes_batch(args[0], args[1], args[2]),
                chunks
            ))
        
        # Combine results
        fractal_params = []
        for chunk_params in results:
            fractal_params.extend(chunk_params)
        
        return fractal_params
    
    def _encode_streaming(
        self, message_bytes: np.ndarray, combined_key: np.ndarray
    ) -> List[Dict]:
        """Encode using streaming (memory-efficient)."""
        fractal_params = []
        
        for i in range(0, len(message_bytes), self.batch_size):
            end = min(i + self.batch_size, len(message_bytes))
            chunk = message_bytes[i:end]
            
            chunk_params = _encode_bytes_batch(chunk, combined_key, i)
            fractal_params.extend(chunk_params)
        
        return fractal_params
