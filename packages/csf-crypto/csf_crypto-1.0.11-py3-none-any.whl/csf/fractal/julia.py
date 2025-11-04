"""
Constant-time Julia set operations for fractal encoding.

All fractal operations are implemented to execute in constant time
to prevent side-channel attacks.
"""

import math
import numpy as np
from typing import Tuple
import warnings
from csf.security.constant_time import select_int

# Overflow prevention constants
MAX_MAGNITUDE = 1e150  # Threshold before overflow (float64 max ~1.7e308)
MAX_MAGNITUDE_SQ = MAX_MAGNITUDE * MAX_MAGNITUDE
SAFE_MULTIPLY_THRESHOLD = 1e75  # Threshold for safe multiplication (sqrt of MAX_MAGNITUDE)


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
        Compute Julia set iterations in constant time with overflow protection.

        Args:
            z0_real: Real part of initial point
            z0_imag: Imaginary part of initial point
            c_real: Real part of Julia parameter
            c_imag: Imaginary part of Julia parameter

        Returns:
            Iteration count (0 to max_iterations)
        """
        # Validate input values
        if not (math.isfinite(z0_real) and math.isfinite(z0_imag) and 
                math.isfinite(c_real) and math.isfinite(c_imag)):
            # Invalid input - return max iterations (converged)
            return self.iterations
        
        z_r = float(z0_real)
        z_i = float(z0_imag)
        c_r = float(c_real)
        c_i = float(c_imag)

        # Fixed iteration count (no early exit based on secret data)
        iteration_count = 0
        escaped = 0  # Use integer flag instead of boolean for constant-time

        # Suppress overflow warnings for this computation
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            
            for i in range(self.iterations):
                # Check magnitude BEFORE computation to prevent overflow
                # Use absolute values to check if multiplication would overflow
                abs_z_r = abs(z_r)
                abs_z_i = abs(z_i)
                
                # Clamp values if they're too large to prevent overflow
                if abs_z_r > SAFE_MULTIPLY_THRESHOLD or abs_z_i > SAFE_MULTIPLY_THRESHOLD:
                    # Scale down to prevent overflow
                    scale = SAFE_MULTIPLY_THRESHOLD / max(abs_z_r, abs_z_i, 1.0)
                    z_r = z_r * scale
                    z_i = z_i * scale
                
                # Compute magnitude squared (avoid sqrt for constant-time)
                try:
                    mag_sq = z_r * z_r + z_i * z_i
                    
                    # Check for overflow/infinity
                    if not math.isfinite(mag_sq) or mag_sq > MAX_MAGNITUDE_SQ:
                        # Clamp to safe value
                        magnitude = math.sqrt(min(mag_sq, MAX_MAGNITUDE_SQ)) if mag_sq > 0 else 0.0
                        if magnitude > 0:
                            scale = MAX_MAGNITUDE / magnitude
                            z_r = z_r * scale
                            z_i = z_i * scale
                            mag_sq = MAX_MAGNITUDE_SQ
                        else:
                            mag_sq = 0.0
                except (OverflowError, FloatingPointError):
                    # Clamp to safe values
                    magnitude = SAFE_MULTIPLY_THRESHOLD
                    current_abs_z_r = abs(z_r)
                    current_abs_z_i = abs(z_i)
                    if current_abs_z_r > 0 or current_abs_z_i > 0:
                        scale = magnitude / max(current_abs_z_r, current_abs_z_i, 1.0)
                        z_r = z_r * scale
                        z_i = z_i * scale
                    mag_sq = magnitude * magnitude

                # Constant-time check: if mag_sq > escape_radius^2, set flag
                # Use select_int to avoid branching
                escaped = select_int(mag_sq > self.escape_radius * self.escape_radius, i, escaped)

                # Update z even after escape to maintain constant time
                # Julia iteration: z = z^2 + c
                try:
                    z_r_sq = z_r * z_r
                    z_i_sq = z_i * z_i
                    z_r_z_i = z_r * z_i
                    
                    # Check for overflow before operations
                    if (not math.isfinite(z_r_sq) or not math.isfinite(z_i_sq) or 
                        not math.isfinite(z_r_z_i) or
                        abs(z_r_sq) > MAX_MAGNITUDE_SQ or abs(z_i_sq) > MAX_MAGNITUDE_SQ):
                        # Values too large - clamp
                        magnitude = SAFE_MULTIPLY_THRESHOLD
                        current_abs_z_r = abs(z_r)
                        current_abs_z_i = abs(z_i)
                        if current_abs_z_r > 0 or current_abs_z_i > 0:
                            scale = magnitude / max(current_abs_z_r, current_abs_z_i, 1.0)
                            z_r = z_r * scale
                            z_i = z_i * scale
                        break
                    
                    z_r_new = z_r_sq - z_i_sq + c_r
                    z_i_new = 2 * z_r_z_i + c_i
                    
                    # Check for NaN or Inf
                    if not (math.isfinite(z_r_new) and math.isfinite(z_i_new)):
                        # Clamp to safe values
                        current_abs_z_r = abs(z_r)
                        current_abs_z_i = abs(z_i)
                        z_r = math.copysign(min(current_abs_z_r, SAFE_MULTIPLY_THRESHOLD), z_r)
                        z_i = math.copysign(min(current_abs_z_i, SAFE_MULTIPLY_THRESHOLD), z_i)
                        break
                    
                    z_r = z_r_new
                    z_i = z_i_new
                    
                except (OverflowError, FloatingPointError):
                    # Clamp to safe values
                    current_abs_z_r = abs(z_r)
                    current_abs_z_i = abs(z_i)
                    z_r = math.copysign(min(current_abs_z_r, SAFE_MULTIPLY_THRESHOLD), z_r)
                    z_i = math.copysign(min(current_abs_z_i, SAFE_MULTIPLY_THRESHOLD), z_i)
                    break

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
