"""
Fractal signature visualization and generation.
"""

from typing import Tuple
import numpy as np
import hashlib
from csf.fractal.julia import ConstantTimeJulia
from csf.security.constant_time import compare_digest


class FractalSignature:
    """
    Generates fractal signatures for authentication.
    """

    def __init__(self, width: int = 512, height: int = 512):
        """
        Initialize signature generator.

        Args:
            width: Image width
            height: Image height
        """
        self.width = width
        self.height = height
        self.julia = ConstantTimeJulia()

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

        # Create parameter from message hash
        msg_hash = hashlib.sha256(message.encode()).digest()
        hash_float = np.frombuffer(msg_hash[:8], dtype=np.float64)[0]

        # Normalize hash
        c_param = complex((hash_float % 1.0) - 0.5, ((hash_float * 0.618) % 1.0) - 0.5) * 0.8

        # Generate fractal image
        image = np.zeros((self.height, self.width), dtype=np.float32)

        x_min, x_max = -2.0, 2.0
        y_min, y_max = -2.0, 2.0

        for y in range(self.height):
            for x in range(self.width):
                # Map pixel to complex plane
                z0_real = x_min + (x / self.width) * (x_max - x_min)
                z0_imag = y_min + (y / self.height) * (y_max - y_min)

                # Compute Julia set iteration (constant-time)
                iterations = self.julia.compute_iterations(
                    z0_real, z0_imag, c_param.real, c_param.imag
                )

                # Store iteration count
                image[y, x] = iterations / 100.0

        # Generate hash of the image
        image_bytes = image.tobytes()
        signature_hash = hashlib.sha256(image_bytes).hexdigest()

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
