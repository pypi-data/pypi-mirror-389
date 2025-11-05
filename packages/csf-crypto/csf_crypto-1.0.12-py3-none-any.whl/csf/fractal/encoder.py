"""
Fractal message encoder.

Encodes messages into fractal parameter space.
"""

import math
from typing import List, Dict
import numpy as np
from csf.fractal.julia import ConstantTimeJulia
from csf.security.validation import validate_string, validate_array
from csf.security.constant_time import select_int


class FractalEncoder:
    """
    Encodes messages into fractal parameters using constant-time operations.
    """

    def __init__(self, iterations: int = 50, escape_radius: float = 2.0):
        """
        Initialize fractal encoder.

        Args:
            iterations: Maximum iterations for fractal computation (reduced from 100 to 50 for performance)
            escape_radius: Escape radius for divergence detection
        """
        self.iterations = iterations
        self.escape_radius = escape_radius
        self.julia = ConstantTimeJulia(iterations, escape_radius)

    def encode_message(
        self, message: str, math_key: np.ndarray, semantic_key: np.ndarray
    ) -> List[Dict]:
        """
        Encode a message into fractal parameters.

        Args:
            message: Plaintext message
            math_key: Mathematical key vector
            semantic_key: Semantic key vector

        Returns:
            List of fractal parameters for each byte
        """
        validate_string(message, "message")
        validate_array(math_key, "math_key")
        validate_array(semantic_key, "semantic_key")

        # Combine keys (constant-time combination)
        min_len = min(len(math_key), len(semantic_key))
        if min_len < 128:
            # Pad if needed
            combined_key = np.zeros(128, dtype=np.float64)
            combined_key[:min_len] = (math_key[:min_len] + semantic_key[:min_len]) / 2
        else:
            combined_key = (math_key[:128] + semantic_key[:128]) / 2

        # Convert message to bytes
        message_bytes = message.encode("utf-8")
        fractal_params = []

        for i, byte_val in enumerate(message_bytes):
            # Create unique parameter set for each byte (constant-time indexing)
            param_idx = i % len(combined_key)

            # Normalize combined_key values to [0, 1) range for reversible encoding
            # Use modulo 1.0 to ensure values stay in [0, 1)
            key_offset = (abs(combined_key[param_idx]) % 1.0) * 0.5
            key_offset_imag = (abs(combined_key[(param_idx + 1) % len(combined_key)]) % 1.0) * 0.5

            # Generate fractal parameters from message byte and keys
            # Encoding: c_real = byte/256 + key_offset (reversible)
            c_real = (float(byte_val) / 256.0 + key_offset) % 1.0
            c_imag = key_offset_imag

            # Generate initial z0 based on position and keys
            z0_real = float(combined_key[(param_idx + 2) % len(combined_key)])
            z0_imag = float(combined_key[(param_idx + 3) % len(combined_key)])
            
            # Validate and clamp values to ensure no NaN/Inf
            # c parameters must be in [0, 1) range
            # IMPORTANT: Don't clamp too aggressively to preserve precision for decoding
            if not math.isfinite(c_real):
                c_real = 0.0
            else:
                # Clamp to [0, 1) but preserve precision - use 0.9999999 instead of 0.999999
                # This ensures we stay in valid range while preserving decoding accuracy
                c_real = max(0.0, min(0.9999999, c_real))
            
            if not math.isfinite(c_imag):
                c_imag = 0.0
            else:
                # Same for c_imag
                c_imag = max(0.0, min(0.9999999, c_imag))
            
            # z0 parameters can be any finite float, but clamp extreme values
            if not math.isfinite(z0_real):
                z0_real = 0.0
            else:
                z0_real = max(-1e100, min(1e100, z0_real))
            
            if not math.isfinite(z0_imag):
                z0_imag = 0.0
            else:
                z0_imag = max(-1e100, min(1e100, z0_imag))

            fractal_params.append(
                {
                    "c": (float(c_real), float(c_imag)),
                    "z0": (float(z0_real), float(z0_imag)),
                    "iteration": int(i),
                    "byte_value": int(byte_val),
                }
            )

        return fractal_params

    def compute_fractal_point(self, z0: complex, c: complex) -> int:
        """
        Compute fractal iteration count for a point.

        Args:
            z0: Initial complex point
            c: Julia set parameter

        Returns:
            Iteration count
        """
        return self.julia.compute_fractal_point(z0, c)
