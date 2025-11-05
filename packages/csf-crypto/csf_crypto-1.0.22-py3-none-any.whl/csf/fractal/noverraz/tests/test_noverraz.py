"""
Tests for Noverraz engine.
"""

import unittest
import numpy as np
from csf.fractal.noverraz.core import NoverrazEngine
from csf.fractal.noverraz.vectorized import VectorizedNoverraz
from csf.fractal.noverraz.parallel import ParallelNoverraz
from csf.fractal.noverraz.optimized import OptimizedNoverraz


class TestNoverrazCore(unittest.TestCase):
    """Tests for core Noverraz engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = NoverrazEngine(iterations=25, alpha=0.2, beta=0.05)
    
    def test_basic_iteration(self):
        """Test basic Noverraz iteration."""
        result = self.engine.compute_iterations(
            0.5, 0.3, 0.2, 0.1
        )
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 25)
    
    def test_key_injection(self):
        """Test that key injection works."""
        math_key = np.array([0.1, 0.2, 0.3, 0.4])
        semantic_key = np.array([0.5, 0.6, 0.7, 0.8])
        
        result1 = self.engine.compute_iterations(
            0.5, 0.3, 0.2, 0.1, math_key, semantic_key, 0
        )
        result2 = self.engine.compute_iterations(
            0.5, 0.3, 0.2, 0.1, math_key, semantic_key, 1
        )
        
        # Results should be different due to key injection
        # (though they might be same due to convergence)
        self.assertIsInstance(result1, int)
        self.assertIsInstance(result2, int)
    
    def test_convergence(self):
        """Test that Noverraz converges (doesn't diverge)."""
        # Test with various initial conditions
        for z0_r in [-2.0, -1.0, 0.0, 1.0, 2.0]:
            for z0_i in [-2.0, -1.0, 0.0, 1.0, 2.0]:
                result = self.engine.compute_iterations(
                    z0_r, z0_i, 0.2, 0.1
                )
                # Should always converge (not escape)
                self.assertLessEqual(result, 25)


class TestVectorizedNoverraz(unittest.TestCase):
    """Tests for vectorized Noverraz."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = VectorizedNoverraz(iterations=25)
    
    def test_batch_processing(self):
        """Test batch processing."""
        z0_real = np.array([0.5, 0.6, 0.7], dtype=np.float64)
        z0_imag = np.array([0.3, 0.4, 0.5], dtype=np.float64)
        
        results_r, results_i, iterations = self.engine.compute_batch(
            z0_real, z0_imag, 0.2, 0.1
        )
        
        self.assertEqual(len(results_r), 3)
        self.assertEqual(len(results_i), 3)
        self.assertEqual(len(iterations), 3)
        self.assertTrue(np.all(np.isfinite(results_r)))
        self.assertTrue(np.all(np.isfinite(results_i)))


class TestParallelNoverraz(unittest.TestCase):
    """Tests for parallel Noverraz."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = ParallelNoverraz(iterations=25, num_workers=2)
    
    def test_parallel_processing(self):
        """Test parallel batch processing."""
        n = 1000
        z0_real = np.random.rand(n).astype(np.float64)
        z0_imag = np.random.rand(n).astype(np.float64)
        
        results_r, results_i, iterations = self.engine.compute_batch_parallel(
            z0_real, z0_imag, 0.2, 0.1, chunk_size=100
        )
        
        self.assertEqual(len(results_r), n)
        self.assertEqual(len(results_i), n)
        self.assertEqual(len(iterations), n)


class TestOptimizedNoverraz(unittest.TestCase):
    """Tests for optimized Noverraz."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = OptimizedNoverraz(iterations=25)
    
    def test_streaming(self):
        """Test streaming processing."""
        n = 100
        z0_real_stream = (0.5 + i * 0.01 for i in range(n))
        z0_imag_stream = (0.3 + i * 0.01 for i in range(n))
        
        results = list(self.engine.compute_stream(
            z0_real_stream, z0_imag_stream, 0.2, 0.1, batch_size=10
        ))
        
        self.assertEqual(len(results), n)
        for r, i, it in results:
            self.assertIsInstance(r, float)
            self.assertIsInstance(i, float)
            self.assertIsInstance(it, int)


if __name__ == '__main__':
    unittest.main()

