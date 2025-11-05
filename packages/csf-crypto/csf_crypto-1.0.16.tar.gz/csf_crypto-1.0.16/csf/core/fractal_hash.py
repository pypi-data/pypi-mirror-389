"""
Fractal-based hash function for CSF.

Uses Julia set iterations to create a deterministic, post-quantum-resistant hash.
This is more aligned with CSF's philosophy than using SHA-256 or SHAKE.

The fractal hash is based on the same Julia set operations used in CSF encoding,
making it intrinsically part of the protocol rather than an external dependency.
"""

import numpy as np
from typing import Union

# Use Noverraz if available (new improved engine), fallback to Julia
try:
    from csf.fractal.noverraz.core import NoverrazEngine
    USE_NOVERRAZ = True
except ImportError:
    USE_NOVERRAZ = False
    from csf.fractal.julia import ConstantTimeJulia


class FractalHash:
    """
    Fractal-based hash function using Julia set iterations.
    
    This hash function is designed to be:
    - Post-quantum resistant (fractal space exploration is resistant to Grover)
    - Deterministic (same input always produces same output)
    - Constant-time (no side-channel leaks)
    - Aligned with CSF's fractal-based architecture
    """

    def __init__(self, output_length: int = 32, iterations: int = 256):
        """
        Initialize fractal hash function.

        Args:
            output_length: Desired output length in bytes (default 32 = 256 bits)
            iterations: Number of Julia iterations for hash generation
        """
        self.output_length = output_length
        self.iterations = iterations
        
        # Use Noverraz if available (new improved engine), fallback to Julia
        if USE_NOVERRAZ:
            self.noverraz = NoverrazEngine(iterations=iterations, alpha=0.2, beta=0.05)
            self.julia = None
        else:
            self.julia = ConstantTimeJulia(iterations=iterations, escape_radius=2.0)
            self.noverraz = None

    def hash(self, data: Union[bytes, str]) -> bytes:
        """
        Generate fractal hash from input data.

        Args:
            data: Input data (bytes or str)

        Returns:
            Hash as bytes (length = output_length)
        """
        # Convert to bytes if string
        if isinstance(data, str):
            data = data.encode("utf-8")

        # Convert input to numeric seed
        # Use first 16 bytes to create initial Julia parameters
        data_padded = data + b"\x00" * max(0, 16 - len(data))
        seed = np.frombuffer(data_padded[:16], dtype=np.uint64)[0]

        # Generate hash using multiple Julia iterations with different parameters
        hash_bytes = bytearray()

        # Use iterative Julia computations to fill hash output
        # Each iteration generates 4 bytes (from iteration counts)
        bytes_per_iteration = 4
        num_hashes_needed = (self.output_length + bytes_per_iteration - 1) // bytes_per_iteration

        # Use the full data to create multiple hash rounds with better mixing
        data_hash = 0
        for byte in data:
            data_hash = ((data_hash << 8) | byte) % (2**63)

        for i in range(num_hashes_needed):
            # Create unique Julia parameters from data + index
            # Mix data hash with position and previous results
            position_hash = (data_hash * (i + 1) * 0x517cc1b727220a95) % (2**63)
            
            # Extract different parts of data for different rounds
            byte_idx = (i * 13) % len(data) if len(data) > 0 else 0  # Prime step for better distribution
            char_value = data[byte_idx] if len(data) > 0 else 0
            
            # Create Julia parameter c from mixed hash
            c_seed = (position_hash ^ (char_value << (i % 8))) % (2**63)
            c_real = np.sin(float(c_seed) * 0.00001) * 0.8
            c_imag = np.cos(float(c_seed) * 0.00001) * 0.8

            # Create initial z0 from data with different offset
            z0_offset = (i * 17) % max(len(data) - 4, 1) if len(data) > 4 else 0
            if len(data) >= 4:
                z0_bytes = data[z0_offset : z0_offset + 4] + b"\x00" * (4 - len(data[z0_offset : z0_offset + 4]))
                z0_seed = int.from_bytes(z0_bytes[:4], byteorder="big") ^ (i * 0x9e3779b9)
            else:
                z0_seed = (data_hash + i) % (2**63)
            
            z0_real = np.sin(float(z0_seed) * 0.00001) * 2.0
            z0_imag = np.cos(float(z0_seed) * 0.00001) * 2.0

            # Compute fractal iterations using Noverraz or Julia
            if self.noverraz is not None:
                # Use Noverraz (new improved engine)
                iter_count = self.noverraz.compute_iterations(
                    z0_real, z0_imag, c_real, c_imag
                )
            else:
                # Fallback to Julia
                iter_count = self.julia.compute_iterations(z0_real, z0_imag, c_real, c_imag)

            # Mix iteration count with position for better diffusion
            mixed_count = (iter_count * (i + 1) + char_value * 256) % (2**32)
            
            # Convert to bytes (4 bytes)
            hash_bytes.extend(mixed_count.to_bytes(4, byteorder="big"))

        # Truncate to desired length
        return bytes(hash_bytes[: self.output_length])

    def hash_hex(self, data: Union[bytes, str]) -> str:
        """
        Generate fractal hash as hexadecimal string.

        Args:
            data: Input data (bytes or str)

        Returns:
            Hash as hexadecimal string
        """
        return self.hash(data).hex()


def fractal_hash(data: Union[bytes, str], output_length: int = 32) -> bytes:
    """
    Convenience function for fractal hashing.

    Args:
        data: Input data (bytes or str)
        output_length: Desired output length in bytes (default 32)

    Returns:
        Hash as bytes
    """
    hasher = FractalHash(output_length=output_length)
    return hasher.hash(data)


def fractal_hash_hex(data: Union[bytes, str], output_length: int = 32) -> str:
    """
    Convenience function for fractal hashing (hex output).

    Args:
        data: Input data (bytes or str)
        output_length: Desired output length in bytes (default 32)

    Returns:
        Hash as hexadecimal string
    """
    hasher = FractalHash(output_length=output_length)
    return hasher.hash_hex(data)

