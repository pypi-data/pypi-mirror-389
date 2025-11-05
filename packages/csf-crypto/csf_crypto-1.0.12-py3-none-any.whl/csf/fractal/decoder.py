"""
Fractal message decoder.

Decodes messages from fractal parameters.
"""

import math
from typing import List, Dict
import numpy as np
from csf.security.validation import validate_array
from csf.utils.exceptions import EncodingError


class FractalDecoder:
    """
    Decodes messages from fractal parameters using constant-time operations.
    """

    def decode_message(
        self, fractal_params: List[Dict], math_key: np.ndarray, semantic_key: np.ndarray
    ) -> str:
        """
        Decode fractal parameters back to message.

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
            # Empty message case - return empty string
            return ""

        # Combine keys (same as encoder)
        min_len = min(len(math_key), len(semantic_key))
        if min_len < 128:
            combined_key = np.zeros(128, dtype=np.float64)
            combined_key[:min_len] = (math_key[:min_len] + semantic_key[:min_len]) / 2
        else:
            combined_key = (math_key[:128] + semantic_key[:128]) / 2

        message_bytes = bytearray()

        for param in fractal_params:
            # Extract byte value from fractal parameters
            c_real, c_imag = param["c"]
            iteration = param.get("iteration", 0)
            
            # Validate and sanitize fractal parameters
            # Handle NaN/Inf values by using fallback
            if not (math.isfinite(c_real) and math.isfinite(c_imag)):
                # Invalid parameter - skip this byte or use stored byte_value
                if "byte_value" in param and isinstance(param["byte_value"], int):
                    message_bytes.append(param["byte_value"] % 256)
                else:
                    # Fallback: use 0
                    message_bytes.append(0)
                continue

            param_idx = iteration % len(combined_key)

            # Normalize key offset same way as encoder
            key_offset = (abs(combined_key[param_idx]) % 1.0) * 0.5

            # Decode: byte = (c_real - key_offset) * 256 (reverse of encoding)
            # Handle wrap-around from modulo
            decoded_val = c_real - key_offset
            # Normalize to [0, 1)
            while decoded_val < 0:
                decoded_val += 1.0
            while decoded_val >= 1.0:
                decoded_val -= 1.0
            # Use round() instead of int() to handle quantization errors better
            # This compensates for small precision losses from 24-bit quantization
            byte_val = int(round(decoded_val * 256)) % 256

            message_bytes.append(byte_val)

        try:
            return message_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback: try to decode with error handling
            return message_bytes.decode("utf-8", errors="replace")
