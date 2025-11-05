"""
Encryption operations.

Provides high-level encryption API.
"""

import math
from typing import Dict, Optional, Union
import numpy as np
from csf.core.keys import KeyManager
from csf.fractal.encoder import FractalEncoder
from csf.semantic.vectorizer import SemanticVectorizer
from csf.fractal.visualizer import FractalSignature
from csf.security.validation import validate_string, validate_bytes, validate_string_or_bytes
from csf.security.constant_time import compare_digest
from csf.core.fractal_hash import fractal_hash
from csf.utils.serialization import serialize_encrypted_data


def _encrypt_core(
    message: str,
    semantic_key_text: str,
    math_public_key: Optional[bytes],
    math_private_key: Optional[bytes],
    pqc_scheme: str,
    return_dict: bool,
    compress: bool,
    generate_signature: bool = False,
) -> Union[bytes, Dict]:
    """
    Core encryption logic without recursion.
    
    This is the actual implementation that does the encryption work.
    """
    # Initialize components
    key_manager = KeyManager(pqc_scheme)
    fractal_encoder = FractalEncoder()
    semantic_vectorizer = SemanticVectorizer()

    # Generate or use provided mathematical keys (with caching)
    from csf.core.key_cache import get_global_cache
    cache = get_global_cache()
    
    if math_public_key is None or math_private_key is None:
        # Use key cache for performance
        math_public_key, math_private_key = cache.get_or_generate(
            semantic_key_text,
            pqc_scheme,
            lambda: key_manager.generate_key_pair()
        )
    else:
        validate_bytes(math_public_key, "math_public_key")
        validate_bytes(math_private_key, "math_private_key")

    # Derive shared secret (with caching)
    
    def compute_shared_secret():
        secret = key_manager.derive_shared_secret(math_public_key, math_private_key)
        secret_arr = np.frombuffer(secret[:128], dtype=np.float64)
        return secret, secret_arr
    
    shared_secret, shared_secret_arr = cache.get_shared_secret(
        semantic_key_text, pqc_scheme, math_public_key, math_private_key, compute_shared_secret
    )

    # Store fractal hash of shared secret for key validation during decryption
    # Using fractal hash instead of SHA-256 for post-quantum resistance and protocol alignment
    # OPTIMIZATION: Reduced to 16 bytes (sufficient for validation, 2x faster)
    shared_secret_hash = fractal_hash(shared_secret, output_length=16)

    # Transform semantic key (with caching)
    semantic_vector = cache.get_semantic_vector(
        semantic_key_text, lambda: semantic_vectorizer.text_to_vector(semantic_key_text)
    )

    # Encode message
    fractal_params = fractal_encoder.encode_message(message, shared_secret_arr, semantic_vector)

    # Generate signature (OPTIMIZATION: Optional, disabled by default for performance)
    signature_hash = None
    signature_image_shape = None
    if generate_signature:
        # OPTIMIZATION: Reduced resolution 32x32 → 8x8 (16x fewer pixels = 16x faster)
        signature_gen = FractalSignature(width=8, height=8)
        signature_image, signature_hash = signature_gen.generate_signature(
            message, shared_secret_arr, semantic_vector, math_private_key
        )
        signature_image_shape = list(signature_image.shape)

    # OPTIMIZED: Vectorized validation using NumPy (much faster than loops)
    num_params = len(fractal_params)
    if num_params > 0:
        # Pre-extract all values into arrays (single pass, direct access)
        c_real_arr = np.zeros(num_params, dtype=np.float64)
        c_imag_arr = np.zeros(num_params, dtype=np.float64)
        z0_real_arr = np.zeros(num_params, dtype=np.float64)
        z0_imag_arr = np.zeros(num_params, dtype=np.float64)
        iterations_arr = np.zeros(num_params, dtype=np.int32)
        byte_values_arr = np.zeros(num_params, dtype=np.uint8)
        
        # Extract in single pass (faster than list comprehension + np.array)
        for i, p in enumerate(fractal_params):
            c_tuple = p["c"]
            z0_tuple = p["z0"]
            c_real_arr[i] = c_tuple[0] if isinstance(c_tuple, (tuple, list)) else c_tuple
            c_imag_arr[i] = c_tuple[1] if isinstance(c_tuple, (tuple, list)) else 0.0
            z0_real_arr[i] = z0_tuple[0] if isinstance(z0_tuple, (tuple, list)) else z0_tuple
            z0_imag_arr[i] = z0_tuple[1] if isinstance(z0_tuple, (tuple, list)) else 0.0
            iterations_arr[i] = int(p["iteration"])
            byte_values_arr[i] = int(p["byte_value"]) % 256
        
        # Vectorized finite check and replacement (single pass)
        c_real_arr = np.where(np.isfinite(c_real_arr), c_real_arr, 0.0)
        c_imag_arr = np.where(np.isfinite(c_imag_arr), c_imag_arr, 0.0)
        z0_real_arr = np.where(np.isfinite(z0_real_arr), z0_real_arr, 0.0)
        z0_imag_arr = np.where(np.isfinite(z0_imag_arr), z0_imag_arr, 0.0)
        
        # Build validated params list (pre-allocated for better performance)
        validated_params = [None] * num_params
        for i in range(num_params):
            validated_params[i] = {
                "c": [c_real_arr[i], c_imag_arr[i]],  # Keep as list for compatibility
                "z0": [z0_real_arr[i], z0_imag_arr[i]],
                "iteration": int(iterations_arr[i]),
                "byte_value": int(byte_values_arr[i]),
            }
    else:
        validated_params = []
    
    result = {
        "encrypted_data": {
            "fractal_params": validated_params,
            "public_key": list(math_public_key),
            "shared_secret_hash": list(shared_secret_hash),  # Store hash for key validation
        },
        "metadata": {"message_length": len(message), "pqc_scheme": pqc_scheme},
    }
    
    # Only include signature if generated
    if signature_hash is not None:
        result["encrypted_data"]["signature_hash"] = signature_hash
        if signature_image_shape is not None:
            result["encrypted_data"]["signature_image_shape"] = signature_image_shape

    # Return optimized binary format by default, or dict if requested
    if return_dict:
        return result
    else:
        return serialize_encrypted_data(result, compress=compress)


def encrypt(
    message: Union[str, bytes],
    semantic_key_text: str,
    math_public_key: Optional[bytes] = None,
    math_private_key: Optional[bytes] = None,
    pqc_scheme: str = "Kyber768",
    return_dict: bool = False,
    compress: bool = True,
    generate_signature: bool = False,
) -> Union[bytes, Dict]:
    """
    Encrypt a message using fractal encoding.
    
    For large messages (>1KB), automatically uses chunked parallel processing for better performance.

    Args:
        message: Plaintext message (str or bytes)
        semantic_key_text: Semantic key as text
        math_public_key: Optional pre-generated public key
        math_private_key: Optional pre-generated private key
        pqc_scheme: PQC scheme to use
        return_dict: If True, return dict format (legacy). If False, return bytes (optimized binary format)
        compress: Whether to compress the output (only applies if return_dict=False)
        generate_signature: If True, generate fractal signature (default False for performance)

    Returns:
        Binary serialized encrypted data (bytes) by default, or dictionary if return_dict=True
    """
    # Accept str or bytes, convert to str
    message = validate_string_or_bytes(message, "message")
    validate_string(semantic_key_text, "semantic_key_text")
    
    # AUTO-DETECT: Use chunked encryption for large messages (>1KB)
    # This provides massive performance improvements for large files
    CHUNK_THRESHOLD = 1024  # 1KB (optimized from 8KB for better performance)
    message_len = len(message)
    if message_len >= CHUNK_THRESHOLD:
        from csf.crypto.encrypt_chunked import encrypt_chunked
        return encrypt_chunked(
            message,
            semantic_key_text,
            math_public_key,
            math_private_key,
            pqc_scheme,
            chunk_size=131072,  # OPTIMIZATION: 128KB chunks (was 64KB) for better performance
            return_dict=return_dict,
            compress=compress,
            generate_signature=generate_signature,
        )
    
    # Small message: use core encryption directly
    return _encrypt_core(
        message,
        semantic_key_text,
        math_public_key,
        math_private_key,
        pqc_scheme,
        return_dict,
        compress,
        generate_signature,
    )
