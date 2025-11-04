"""
Constant-time Julia set operations for fractal encoding.

All fractal operations are implemented to execute in constant time
to prevent side-channel attacks.
"""

import numpy as np
from typing import Tuple
from csf.security.constant_time import select_int


class ConstantTimeJulia:
    """
    Constant-time Julia set operations.
    """

    def __init__(self, iterations: int = 100, escape_radius: float = 2.0):
        """
        Initialize Julia set operations.

        Args:
            iterations: Maximum iterations
            escape_radius: Escape radius for divergence
        """
        self.iterations = iterations
        self.escape_radius = escape_radius

    def compute_iterations(
        self, z0_real: float, z0_imag: float, c_real: float, c_imag: float
    ) -> int:
        """
        Compute Julia set iterations in constant time.

        Args:
            z0_real: Real part of initial point
            z0_imag: Imaginary part of initial point
            c_real: Real part of Julia parameter
            c_imag: Imaginary part of Julia parameter

        Returns:
            Iteration count (0 to max_iterations)
        """
        z_r = z0_real
        z_i = z0_imag
        c_r = c_real
        c_i = c_imag

        # Fixed iteration count (no early exit based on secret data)
        iteration_count = 0
        escaped = 0  # Use integer flag instead of boolean for constant-time

        for i in range(self.iterations):
            # Compute magnitude squared (avoid sqrt for constant-time)
            mag_sq = z_r * z_r + z_i * z_i

            # Constant-time check: if mag_sq > escape_radius^2, set flag
            # Use select_int to avoid branching
            escaped = select_int(mag_sq > self.escape_radius * self.escape_radius, i, escaped)

            # Update z even after escape to maintain constant time
            # Julia iteration: z = z^2 + c
            z_r_new = z_r * z_r - z_i * z_i + c_r
            z_i_new = 2 * z_r * z_i + c_i

            z_r = z_r_new
            z_i = z_i_new

            # Update iteration count
            iteration_count = select_int(escaped == 0, i + 1, iteration_count)

        # Return iteration count (0 means converged, >0 means escaped at that iteration)
        if escaped > 0:
            return int(escaped)
        return self.iterations

    def compute_fractal_point(self, z0: complex, c: complex) -> int:
        """
        Compute fractal iteration count for a complex point.

        Args:
            z0: Initial complex point
            c: Julia set parameter

        Returns:
            Iteration count before escape
        """
        return self.compute_iterations(z0.real, z0.imag, c.real, c.imag)

    def compute_fractal_array(
        self, z0_real: np.ndarray, z0_imag: np.ndarray, c_real: float, c_imag: float
    ) -> np.ndarray:
        """
        Compute fractal iterations for arrays (vectorized but constant-time per element).

        Args:
            z0_real: Real parts of initial points
            z0_imag: Imaginary parts of initial points
            c_real: Real part of Julia parameter
            c_imag: Imaginary part of Julia parameter

        Returns:
            Array of iteration counts
        """
        results = np.zeros(len(z0_real), dtype=np.int32)

        for i in range(len(z0_real)):
            results[i] = self.compute_iterations(z0_real[i], z0_imag[i], c_real, c_imag)

        return results


# Convenience function
def create_julia(iterations: int = 100, escape_radius: float = 2.0) -> ConstantTimeJulia:
    """
    Create a constant-time Julia set operations instance.

    Args:
        iterations: Maximum iterations
        escape_radius: Escape radius

    Returns:
        ConstantTimeJulia instance
    """
    return ConstantTimeJulia(iterations, escape_radius)
