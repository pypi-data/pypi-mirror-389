"""
Chunked parallel encryption for large files.

Implements chunking and parallel processing to improve performance for large data.
"""

import math
from typing import Dict, Optional, Union
import numpy as np
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing as mp
from csf.core.keys import KeyManager
from csf.fractal.encoder import FractalEncoder
from csf.semantic.vectorizer import SemanticVectorizer
from csf.fractal.visualizer import FractalSignature
from csf.security.validation import validate_string, validate_bytes, validate_string_or_bytes
from csf.core.fractal_hash import fractal_hash
from csf.utils.serialization import serialize_encrypted_data


def encrypt_chunk(chunk_data: bytes, chunk_index: int, semantic_key_text: str, 
                  shared_secret: bytes, semantic_vector: np.ndarray) -> Dict:
    """
    Encrypt a single chunk of data.
    
    Args:
        chunk_data: Chunk of data to encrypt
        chunk_index: Index of this chunk
        semantic_key_text: Semantic key text
        shared_secret: Shared secret bytes
        semantic_vector: Semantic vector
        
    Returns:
        Encrypted chunk dictionary
    """
    # Convert chunk to string
    message = chunk_data.decode('utf-8')
    
    # Use optimized encoder if available
    try:
        from csf.fractal.encoder_optimized import OptimizedFractalEncoder
        fractal_encoder = OptimizedFractalEncoder(iterations=25)
    except ImportError:
        # Fallback to standard encoder
        fractal_encoder = FractalEncoder(iterations=25)
    
    # Extract shared secret array
    shared_secret_arr = np.frombuffer(shared_secret[:128], dtype=np.float64)
    
    # Encode message
    fractal_params = fractal_encoder.encode_message(message, shared_secret_arr, semantic_vector)
    
    return {
        'index': chunk_index,
        'params': fractal_params,
        'size': len(chunk_data)
    }


def encrypt_chunked(
    message: Union[str, bytes],
    semantic_key_text: str,
    math_public_key: Optional[bytes] = None,
    math_private_key: Optional[bytes] = None,
    pqc_scheme: str = "Kyber768",
    chunk_size: int = 8192,  # 8KB chunks
    num_workers: Optional[int] = None,
    return_dict: bool = False,
    compress: bool = True,
) -> Union[bytes, Dict]:
    """
    Encrypt with chunking and parallel processing.
    
    Args:
        message: Message to encrypt
        semantic_key_text: Semantic key
        math_public_key: Optional public key
        math_private_key: Optional private key
        pqc_scheme: PQC scheme
        chunk_size: Size of each chunk (default 8KB)
        num_workers: Number of parallel workers (default: CPU count)
        return_dict: Return dict format
        compress: Compress output
        
    Returns:
        Encrypted data
    """
    # Validate inputs
    message = validate_string_or_bytes(message, "message")
    validate_string(semantic_key_text, "semantic_key_text")
    
    # Initialize components
    key_manager = KeyManager(pqc_scheme)
    semantic_vectorizer = SemanticVectorizer()
    
    # Generate or use provided keys
    if math_public_key is None or math_private_key is None:
        math_public_key, math_private_key = key_manager.generate_key_pair()
    else:
        validate_bytes(math_public_key, "math_public_key")
        validate_bytes(math_private_key, "math_private_key")
    
    # Derive shared secret
    shared_secret = key_manager.derive_shared_secret(math_public_key, math_private_key)
    shared_secret_hash = fractal_hash(shared_secret, output_length=32)
    
    # Transform semantic key
    semantic_vector = semantic_vectorizer.text_to_vector(semantic_key_text)
    
    # Convert message to bytes
    message_bytes = message.encode('utf-8')
    
    # Decide whether to use chunking
    if len(message_bytes) < chunk_size:
        # Small message: use regular encryption
        from csf.crypto.encrypt import encrypt
        return encrypt(message, semantic_key_text, math_public_key, math_private_key, 
                      pqc_scheme, return_dict, compress)
    
    # Large message: use chunked processing
    if num_workers is None:
        num_workers = min(mp.cpu_count(), 4)  # Limit to 4 workers max
    
    # Split into chunks
    chunks = []
    for i in range(0, len(message_bytes), chunk_size):
        chunk = message_bytes[i:i+chunk_size]
        chunks.append((chunk, i // chunk_size))
    
    # Process chunks in parallel
    fractal_params = []
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [
            executor.submit(encrypt_chunk, chunk, idx, semantic_key_text, 
                          shared_secret, semantic_vector)
            for chunk, idx in chunks
        ]
        
        # Collect results in order
        chunk_results = [future.result() for future in futures]
        chunk_results.sort(key=lambda x: x['index'])
        
        # Combine fractal params
        for result in chunk_results:
            fractal_params.extend(result['params'])
    
    # Generate signature (small and fast)
    signature_gen = FractalSignature(width=32, height=32)
    shared_secret_arr = np.frombuffer(shared_secret[:128], dtype=np.float64)
    signature_image, signature_hash = signature_gen.generate_signature(
        message, shared_secret_arr, semantic_vector
    )
    
    # Prepare output
    validated_params = []
    for p in fractal_params:
        validated_params.append({
            "c": [float(p["c"][0]), float(p["c"][1])],
            "z0": [float(p["z0"][0]), float(p["z0"][1])],
            "iteration": int(p["iteration"]),
            "byte_value": int(p["byte_value"]),
        })
    
    result = {
        "encrypted_data": {
            "fractal_params": validated_params,
            "public_key": list(math_public_key),
            "shared_secret_hash": list(shared_secret_hash),
            "signature_hash": signature_hash,
            "signature_image_shape": list(signature_image.shape),
        },
        "metadata": {"message_length": len(message), "pqc_scheme": pqc_scheme},
    }
    
    if return_dict:
        return result
    else:
        return serialize_encrypted_data(result, compress=compress)

