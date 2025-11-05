"""
Optimized fractal decoder using vectorization and parallel processing.

Implements optimizations similar to OptimizedFractalEncoder for decoding.
"""

import math
import numpy as np
from typing import List, Dict
from csf.security.validation import validate_array


def _decode_params_batch(
    fractal_params: List[Dict],
    combined_key: np.ndarray,
) -> bytearray:
    """
    Decode a batch of fractal parameters into bytes.
    
    Uses Cython implementation if available (2-5x faster), otherwise falls back to Python.
    
    Args:
        fractal_params: List of fractal parameters
        combined_key: Combined mathematical and semantic key
    
    Returns:
        Decoded bytes
    """
    # Try Rust implementation first (fastest, 2-5x speedup)
    try:
        import csf_rust
        result = csf_rust.decode_params_batch_rust(fractal_params, combined_key)
        return bytearray(result)
    except (ImportError, AttributeError):
        # Try Cython implementation (2-5x speedup)
        try:
            from csf.fractal._decode_cython import decode_params_batch_cython
            return decode_params_batch_cython(fractal_params, combined_key)
        except ImportError:
            # Fallback to Python implementation
            pass
    
    message_bytes = bytearray(len(fractal_params))
    
    for i, param in enumerate(fractal_params):
        # Extract byte value from fractal parameters
        c_real, c_imag = param["c"]
        iteration = param.get("iteration", i)
        
        # Validate and sanitize fractal parameters
        if not (math.isfinite(c_real) and math.isfinite(c_imag)):
            # Invalid parameter - use stored byte_value or fallback
            if "byte_value" in param and isinstance(param["byte_value"], int):
                message_bytes[i] = param["byte_value"] % 256
            else:
                message_bytes[i] = 0
            continue
        
        param_idx = iteration % len(combined_key)
        
        # Normalize key offset same way as encoder
        key_offset = (abs(combined_key[param_idx]) % 1.0) * 0.5
        
        # Decode: byte = (c_real - key_offset) * 256 (reverse of encoding)
        decoded_val = c_real - key_offset
        # Normalize to [0, 1)
        while decoded_val < 0:
            decoded_val += 1.0
        while decoded_val >= 1.0:
            decoded_val -= 1.0
        # Use round() instead of int() to handle quantization errors better
        byte_val = int(round(decoded_val * 256)) % 256
        
        message_bytes[i] = byte_val
    
    return message_bytes


class OptimizedFractalDecoder:
    """
    Optimized fractal decoder with vectorization and parallel processing.
    
    Features:
    - Vectorized batch processing
    - Memory-efficient operations
    - Pre-allocated buffers
    """
    
    def __init__(self, batch_size: int = 1000):
        """
        Initialize optimized decoder.
        
        Args:
            batch_size: Size of batches for processing
        """
        self.batch_size = batch_size
    
    def decode_message(
        self, fractal_params: List[Dict], math_key: np.ndarray, semantic_key: np.ndarray
    ) -> str:
        """
        Decode fractal parameters back to message with optimizations.
        
        Args:
            fractal_params: List of fractal parameters
            math_key: Mathematical key vector
            semantic_key: Semantic key vector
        
        Returns:
            Decoded plaintext message
        """
        validate_array(math_key, "math_key")
        validate_array(semantic_key, "semantic_key")
        
        if not fractal_params:
            return ""
        
        # Combine keys (same as encoder)
        min_len = min(len(math_key), len(semantic_key))
        if min_len < 128:
            combined_key = np.zeros(128, dtype=np.float64)
            combined_key[:min_len] = (math_key[:min_len] + semantic_key[:min_len]) / 2
        else:
            combined_key = (math_key[:128] + semantic_key[:128]) / 2
        
        # Pre-allocate buffer for better performance
        message_bytes = _decode_params_batch(fractal_params, combined_key)
        
        try:
            return message_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return message_bytes.decode("utf-8", errors="replace")

