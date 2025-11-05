"""
Parallel Noverraz implementation using multiprocessing.

Provides multi-core processing for large-scale fractal computations.
"""

import multiprocessing as mp
from typing import Tuple, Optional, List
import numpy as np
from csf.fractal.noverraz.vectorized import VectorizedNoverraz


def _process_chunk(args):
    """
    Process a chunk of data in a separate process.
    
    Args:
        args: Tuple of (z0_real, z0_imag, c_real, c_imag, math_key, semantic_key, positions, alpha, beta, max_iter)
    
    Returns:
        Tuple of (results_real, results_imag, iterations)
    """
    (z0_real, z0_imag, c_real, c_imag, math_key, semantic_key, 
     positions, alpha, beta, max_iter) = args
    
    engine = VectorizedNoverraz(
        iterations=max_iter, alpha=alpha, beta=beta
    )
    
    return engine.compute_batch(
        z0_real, z0_imag, c_real, c_imag, math_key, semantic_key, positions
    )


class ParallelNoverraz(VectorizedNoverraz):
    """
    Parallel Noverraz engine using multiprocessing.
    
    Distributes computation across multiple CPU cores for maximum performance.
    """
    
    def __init__(self, num_workers: Optional[int] = None, *args, **kwargs):
        """
        Initialize parallel Noverraz engine.
        
        Args:
            num_workers: Number of parallel workers (default: CPU count)
            *args, **kwargs: Arguments for VectorizedNoverraz
        """
        super().__init__(*args, **kwargs)
        if num_workers is None:
            num_workers = min(mp.cpu_count(), 8)  # Limit to 8 workers max
        self.num_workers = num_workers
    
    def compute_batch_parallel(
        self,
        z0_real_array: np.ndarray,
        z0_imag_array: np.ndarray,
        c_real: float,
        c_imag: float,
        math_key: Optional[np.ndarray] = None,
        semantic_key: Optional[np.ndarray] = None,
        positions: Optional[np.ndarray] = None,
        chunk_size: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute Noverraz iterations in parallel across multiple cores.
        
        Args:
            z0_real_array: Array of real parts
            z0_imag_array: Array of imaginary parts
            c_real: Real part of Julia parameter
            c_imag: Imaginary part of Julia parameter
            math_key: Mathematical key vector (optional)
            semantic_key: Semantic key vector (optional)
            positions: Array of positions (optional)
            chunk_size: Size of each chunk (default: auto-calculate)
        
        Returns:
            Tuple of (final_z_real, final_z_imag, iterations)
        """
        n = len(z0_real_array)
        
        # Auto-calculate chunk size if not provided
        if chunk_size is None:
            chunk_size = max(1, n // (self.num_workers * 4))  # 4 chunks per worker
        
        # Prepare arrays
        if positions is None:
            positions = np.arange(n, dtype=np.int32)
        
        if math_key is None:
            math_key = np.array([], dtype=np.float64)
        if semantic_key is None:
            semantic_key = np.array([], dtype=np.float64)
        
        # Split into chunks
        chunks = []
        for i in range(0, n, chunk_size):
            end = min(i + chunk_size, n)
            chunks.append((
                z0_real_array[i:end],
                z0_imag_array[i:end],
                c_real,
                c_imag,
                math_key,
                semantic_key,
                positions[i:end] if len(positions) > 0 else None,
                self.alpha,
                self.beta,
                self.iterations,
            ))
        
        # Process chunks in parallel
        if len(chunks) == 1 or self.num_workers == 1:
            # Single chunk or single worker: process directly
            return self.compute_batch(
                z0_real_array, z0_imag_array, c_real, c_imag,
                math_key, semantic_key, positions
            )
        
        # Multi-process processing
        with mp.Pool(processes=self.num_workers) as pool:
            results = pool.map(_process_chunk, chunks)
        
        # Combine results
        all_real = np.concatenate([r[0] for r in results])
        all_imag = np.concatenate([r[1] for r in results])
        all_iterations = np.concatenate([r[2] for r in results])
        
        return all_real, all_imag, all_iterations

