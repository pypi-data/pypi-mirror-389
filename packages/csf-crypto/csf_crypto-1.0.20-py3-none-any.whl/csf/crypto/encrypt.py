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
    shared_secret_hash = fractal_hash(shared_secret, output_length=32)

    # Transform semantic key (with caching)
    semantic_vector = cache.get_semantic_vector(
        semantic_key_text, lambda: semantic_vectorizer.text_to_vector(semantic_key_text)
    )

    # Encode message
    fractal_params = fractal_encoder.encode_message(message, shared_secret_arr, semantic_vector)

    # Generate signature (optimized with smaller image)
    signature_gen = FractalSignature(width=32, height=32)  # Small signature for performance
    signature_image, signature_hash = signature_gen.generate_signature(
        message, shared_secret_arr, semantic_vector
    )

    # Prepare output with validation
    validated_params = []
    for p in fractal_params:
        # Validate all values are finite
        c_real = float(p["c"][0])
        c_imag = float(p["c"][1])
        z0_real = float(p["z0"][0])
        z0_imag = float(p["z0"][1])
        
        # Ensure finite values (should already be validated by encoder, but double-check)
        if not (math.isfinite(c_real) and math.isfinite(c_imag) and 
                math.isfinite(z0_real) and math.isfinite(z0_imag)):
            # Replace invalid values with safe defaults
            if not math.isfinite(c_real):
                c_real = 0.0
            if not math.isfinite(c_imag):
                c_imag = 0.0
            if not math.isfinite(z0_real):
                z0_real = 0.0
            if not math.isfinite(z0_imag):
                z0_imag = 0.0
        
        validated_params.append({
            "c": [c_real, c_imag],
            "z0": [z0_real, z0_imag],
            "iteration": int(p["iteration"]),
            "byte_value": int(p["byte_value"]),
        })
    
    result = {
        "encrypted_data": {
            "fractal_params": validated_params,
            "public_key": list(math_public_key),
            "shared_secret_hash": list(shared_secret_hash),  # Store hash for key validation
            "signature_hash": signature_hash,
            "signature_image_shape": list(signature_image.shape),
        },
        "metadata": {"message_length": len(message), "pqc_scheme": pqc_scheme},
    }

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
            chunk_size=8192,  # Use 8KB chunks for parallel processing
            return_dict=return_dict,
            compress=compress,
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
    )
