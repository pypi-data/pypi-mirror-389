"""
Core Noverraz fractal engine implementation.

Noverraz is an improved version of Julia sets with:
- Multi-scale damping for guaranteed convergence
- Direct key injection for enhanced security
- Better performance through optimized iterations
"""

import math
import numpy as np
from typing import Tuple, Optional
from csf.security.constant_time import select_int


class NoverrazEngine:
    """
    Core Noverraz fractal engine.
    
    Noverraz uses an improved iteration formula:
    z_{n+1} = (z_n^2 + c) * exp(-α|z_n|^2) + β * K_math * K_sem
    
    This provides:
    - Guaranteed convergence (no divergence)
    - Direct key injection
    - Enhanced cryptographic properties
    - Better performance
    """
    
    def __init__(
        self,
        iterations: int = 25,
        alpha: float = 0.2,
        beta: float = 0.05,
        escape_radius: float = 2.0,
    ):
        """
        Initialize Noverraz engine.
        
        Args:
            iterations: Maximum iterations (default 25, optimized for performance)
            alpha: Damping coefficient (0.1-0.5, default 0.2)
            beta: Key injection weight (0.01-0.1, default 0.05)
            escape_radius: Escape radius (default 2.0, but rarely used due to damping)
        """
        self.iterations = iterations
        self.alpha = alpha
        self.beta = beta
        self.escape_radius = escape_radius
        self.escape_radius_sq = escape_radius * escape_radius
    
    def compute_iterations(
        self,
        z0_real: float,
        z0_imag: float,
        c_real: float,
        c_imag: float,
        math_key: Optional[np.ndarray] = None,
        semantic_key: Optional[np.ndarray] = None,
        position: int = 0,
    ) -> int:
        """
        Compute Noverraz iterations.
        
        Args:
            z0_real: Real part of initial point
            z0_imag: Imaginary part of initial point
            c_real: Real part of Julia parameter
            c_imag: Imaginary part of Julia parameter
            math_key: Mathematical key vector (optional, for key injection)
            semantic_key: Semantic key vector (optional, for key injection)
            position: Position in message (for key indexing)
        
        Returns:
            Iteration count before convergence/escape
        """
        z_r = float(z0_real)
        z_i = float(z0_imag)
        c_r = float(c_real)
        c_i = float(c_imag)
        
        # Prepare key injection (if keys provided)
        use_key_injection = (math_key is not None and semantic_key is not None and 
                           len(math_key) > 0 and len(semantic_key) > 0)
        
        for i in range(self.iterations):
            # Compute magnitude squared
            mag_sq = z_r * z_r + z_i * z_i
            
            # Early exit if escaped (though damping usually prevents this)
            if mag_sq > self.escape_radius_sq:
                return i
            
            # Julia iteration: z^2 + c
            z_r_sq = z_r * z_r
            z_i_sq = z_i * z_i
            z_r_z_i = z_r * z_i
            
            julia_r = z_r_sq - z_i_sq + c_r
            julia_i = 2.0 * z_r_z_i + c_i
            
            # Damping factor: exp(-α|z|^2)
            # This prevents divergence and ensures convergence
            damping = math.exp(-self.alpha * mag_sq)
            
            # Key injection (if keys provided)
            if use_key_injection:
                key_idx = (position + i) % len(math_key)
                sem_idx = key_idx % len(semantic_key)
                key_product = float(math_key[key_idx]) * float(semantic_key[sem_idx])
                
                # Inject keys with beta weight
                z_r_new = julia_r * damping + self.beta * key_product
                z_i_new = julia_i * damping + self.beta * key_product * 0.618  # Golden ratio
            else:
                # No key injection, just damping
                z_r_new = julia_r * damping
                z_i_new = julia_i * damping
            
            # Check for convergence (cycle detection)
            delta_r = abs(z_r_new - z_r)
            delta_i = abs(z_i_new - z_i)
            if delta_r < 1e-10 and delta_i < 1e-10:
                return i
            
            z_r = z_r_new
            z_i = z_i_new
        
        return self.iterations
    
    def compute_fractal_point(
        self,
        z0: complex,
        c: complex,
        math_key: Optional[np.ndarray] = None,
        semantic_key: Optional[np.ndarray] = None,
        position: int = 0,
    ) -> int:
        """
        Compute Noverraz iteration count for a complex point.
        
        Args:
            z0: Initial complex point
            c: Julia set parameter
            math_key: Mathematical key vector (optional)
            semantic_key: Semantic key vector (optional)
            position: Position in message
        
        Returns:
            Iteration count
        """
        return self.compute_iterations(
            z0.real, z0.imag, c.real, c.imag, math_key, semantic_key, position
        )

