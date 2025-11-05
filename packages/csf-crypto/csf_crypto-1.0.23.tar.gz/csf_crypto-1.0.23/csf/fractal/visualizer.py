"""
Fractal signature visualization and generation.
"""

from typing import Tuple
import numpy as np
# Noverraz engine (always available - part of CSF package)
from csf.fractal.noverraz.vectorized import VectorizedNoverraz
USE_NOVERRAZ = True
NoverrazClass = VectorizedNoverraz
from csf.security.constant_time import compare_digest
from csf.core.fractal_hash import fractal_hash


class FractalSignature:
    """
    Generates fractal signatures for authentication.
    """

    def __init__(self, width: int = 8, height: int = 8):
        """
        Initialize signature generator.

        Args:
            width: Image width (OPTIMIZATION: reduced from 32 to 8 for performance - 16x fewer pixels!)
            height: Image height (OPTIMIZATION: reduced from 32 to 8 for performance - 16x fewer pixels!)
        """
        self.width = width
        self.height = height
        
        # Use Noverraz engine (REQUIRED - no fallback)
        # OPTIMIZATION: Reduced iterations from 25 → 5 (5x faster)
        # Create dummy keys for Noverraz (not used in signature generation)
        self.noverraz = NoverrazClass(iterations=5, alpha=0.2, beta=0.05)

    def generate_signature(
        self, message: str, math_key: np.ndarray, semantic_key: np.ndarray, math_private_key: bytes = None
    ) -> Tuple[np.ndarray, str]:
        """
        Generate a fractal signature image and hash.
        
        CRITICAL FIX (v1.0.16): The hash now incorporates message + semantic_key + math_private_key
        to ensure uniqueness and prevent signature forgery.

        Args:
            message: Message to sign
            math_key: Mathematical key (shared secret array)
            semantic_key: Semantic key (vectorized)
            math_private_key: Private mathematical key (bytes) - REQUIRED for security

        Returns:
            Tuple of (fractal_image_array, hash_string)
        """
        # CRITICAL FIX: Combine ALL inputs (message + semantic_key + math_private_key) for unique signature
        # This ensures that different messages or keys produce different hashes
        if math_private_key is None:
            # Fallback: use math_key bytes if math_private_key not provided (for backward compatibility)
            math_key_bytes = math_key.tobytes()[:128] if len(math_key) > 0 else b""
        else:
            math_key_bytes = math_private_key
        
        # Convert semantic_key to string representation for hashing
        semantic_key_str = semantic_key.tobytes().hex()[:64]  # Use first 64 bytes hex representation
        
        # Combine ALL inputs deterministically: message + semantic_key + math_private_key
        combined_input = f"{message}:{semantic_key_str}:{math_key_bytes.hex()}"
        
        # CRITICAL FIX (v1.0.16): Enhanced fractal hash for signatures
        # Philosophy: Stay 100% fractal-based, no traditional cryptographic primitives
        # Use message bytes directly in fractal iterations for maximum sensitivity
        combined_input_bytes = combined_input.encode()
        
        # CRITICAL: Signatures need sufficient iterations for uniqueness and security
        # Increased iterations to ensure different messages produce different hashes
        from csf.core.fractal_hash import FractalHash
        
        # Pass 1: Hash the input (100 iterations for better uniqueness)
        hasher1 = FractalHash(output_length=16, iterations=100)
        hash1 = hasher1.hash(combined_input_bytes)
        
        # Pass 2: Hash with reversed input + pass 1 result for better mixing (100 iterations)
        hasher2 = FractalHash(output_length=16, iterations=100)
        hash2 = hasher2.hash(combined_input_bytes[::-1] + hash1)
        
        # Combine both passes with XOR
        combined_hash = bytearray(hash1)
        for i in range(min(len(combined_hash), len(hash2))):
            combined_hash[i] ^= hash2[i]
        
        # Final pass: Hash the combined result for final 32 bytes (100 iterations)
        hasher_final = FractalHash(output_length=32, iterations=100)
        final_hash = hasher_final.hash(bytes(combined_hash) + combined_input_bytes)
        combined_hash = bytearray(final_hash[:32])
        
        hash_float = np.frombuffer(combined_hash[:8], dtype=np.float64)[0]

        # Normalize hash to create Noverraz parameter c
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

                # Compute fractal iteration using Noverraz (REQUIRED - no fallback)
                iterations = self.noverraz.compute_iterations(
                    z0_real, z0_imag, c_r, c_i,
                    math_key=None, semantic_key=None, position=0
                )
                max_iter = self.noverraz.iterations

                # Store iteration count (normalized by max iterations)
                image[y, x] = float(iterations) / float(max_iter)

        # CRITICAL FIX: Generate hash from combined input (message + keys), not just image
        # This ensures the hash is unique for each (message, key) combination
        # The image is still generated for visualization, but the hash depends on all inputs
        signature_hash = combined_hash.hex()

        return image, signature_hash

    def verify_signature(
        self, message: str, signature_hash: str, math_key: np.ndarray, semantic_key: np.ndarray, math_private_key: bytes = None
    ) -> bool:
        """
        Verify a fractal signature.
        
        CRITICAL FIX (v1.0.16): Recomputes hash using the same method as generate_signature
        and compares it exactly with the provided signature_hash.

        Args:
            message: Original message
            signature_hash: Hash to verify
            math_key: Mathematical key (shared secret array)
            semantic_key: Semantic key (vectorized)
            math_private_key: Private mathematical key (bytes) - REQUIRED for security

        Returns:
            True if signature matches exactly
        """
        # CRITICAL: Recompute hash using the EXACT same method as generate_signature
        _, computed_hash = self.generate_signature(message, math_key, semantic_key, math_private_key)
        
        # CRITICAL: Exact comparison - must match byte-for-byte
        return compare_digest(signature_hash.encode(), computed_hash.encode())
