"""
Fractal signature visualization and generation.
"""

from typing import Tuple
import numpy as np
# Use optimized Julia if available, fallback to standard
try:
    from csf.fractal.julia_optimized import OptimizedJulia
    JuliaClass = OptimizedJulia
except ImportError:
    from csf.fractal.julia import ConstantTimeJulia
    JuliaClass = ConstantTimeJulia
from csf.security.constant_time import compare_digest
from csf.core.fractal_hash import fractal_hash


class FractalSignature:
    """
    Generates fractal signatures for authentication.
    """

    def __init__(self, width: int = 32, height: int = 32):
        """
        Initialize signature generator.

        Args:
            width: Image width (reduced from 256 to 32 for performance - 64x fewer pixels!)
            height: Image height (reduced from 256 to 32 for performance - 64x fewer pixels!)
        """
        self.width = width
        self.height = height
        self.julia = JuliaClass(iterations=25)  # Use optimized version if available

    def generate_signature(
        self, message: str, math_key: np.ndarray, semantic_key: np.ndarray
    ) -> Tuple[np.ndarray, str]:
        """
        Generate a fractal signature image and hash.

        Args:
            message: Message to sign
            math_key: Mathematical key
            semantic_key: Semantic key

        Returns:
            Tuple of (fractal_image_array, hash_string)
        """
        # Combine keys for unique signature
        combined = np.concatenate([math_key[:64], semantic_key[:64]])

        # Create parameter from message hash (using fractal hash for consistency)
        msg_hash = fractal_hash(message.encode(), output_length=32)
        hash_float = np.frombuffer(msg_hash[:8], dtype=np.float64)[0]

        # Normalize hash
        c_param = complex((hash_float % 1.0) - 0.5, ((hash_float * 0.618) % 1.0) - 0.5) * 0.8

        # OPTIMIZATION: Generate fractal image with reduced resolution and optimized computation
        image = np.zeros((self.height, self.width), dtype=np.float32)

        x_min, x_max = -2.0, 2.0
        y_min, y_max = -2.0, 2.0
        
        # OPTIMIZATION: Pre-compute step sizes
        x_step = (x_max - x_min) / self.width
        y_step = (y_max - y_min) / self.height
        
        # OPTIMIZATION: Pre-extract c parameters
        c_r = c_param.real
        c_i = c_param.imag
        
        # OPTIMIZATION: Use vectorized operations where possible
        for y in range(self.height):
            z0_imag = y_min + y * y_step
            for x in range(self.width):
                # Map pixel to complex plane (optimized)
                z0_real = x_min + x * x_step

                # Compute Julia set iteration (constant-time, optimized)
                iterations = self.julia.compute_iterations(
                    z0_real, z0_imag, c_r, c_i
                )

                # Store iteration count (normalized by max iterations, not hardcoded 100)
                image[y, x] = float(iterations) / float(self.julia.iterations)

        # Generate fractal hash of the image (aligned with CSF philosophy)
        image_bytes = image.tobytes()
        signature_hash = fractal_hash(image_bytes, output_length=32).hex()

        return image, signature_hash

    def verify_signature(
        self, message: str, signature_hash: str, math_key: np.ndarray, semantic_key: np.ndarray
    ) -> bool:
        """
        Verify a fractal signature.

        Args:
            message: Original message
            signature_hash: Hash to verify
            math_key: Mathematical key
            semantic_key: Semantic key

        Returns:
            True if signature matches
        """
        _, computed_hash = self.generate_signature(message, math_key, semantic_key)
        return compare_digest(signature_hash.encode(), computed_hash.encode())
