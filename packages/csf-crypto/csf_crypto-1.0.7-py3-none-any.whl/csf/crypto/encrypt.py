"""
Encryption operations.

Provides high-level encryption API.
"""

from typing import Dict, Optional, Union
import numpy as np
from csf.core.keys import KeyManager
from csf.fractal.encoder import FractalEncoder
from csf.semantic.vectorizer import SemanticVectorizer
from csf.fractal.visualizer import FractalSignature
import hashlib
from csf.security.validation import validate_string, validate_bytes, validate_string_or_bytes
from csf.security.constant_time import compare_digest


def encrypt(
    message: Union[str, bytes],
    semantic_key_text: str,
    math_public_key: Optional[bytes] = None,
    math_private_key: Optional[bytes] = None,
    pqc_scheme: str = "Kyber768",
) -> Dict:
    """
    Encrypt a message using fractal encoding.

    Args:
        message: Plaintext message (str or bytes)
        semantic_key_text: Semantic key as text
        math_public_key: Optional pre-generated public key
        math_private_key: Optional pre-generated private key
        pqc_scheme: PQC scheme to use

    Returns:
        Dictionary containing encrypted data and signature
    """
    # Accept str or bytes, convert to str
    message = validate_string_or_bytes(message, "message")
    validate_string(semantic_key_text, "semantic_key_text")

    # Initialize components
    key_manager = KeyManager(pqc_scheme)
    fractal_encoder = FractalEncoder()
    semantic_vectorizer = SemanticVectorizer()

    # Generate or use provided mathematical keys
    if math_public_key is None or math_private_key is None:
        math_public_key, math_private_key = key_manager.generate_key_pair()
    else:
        validate_bytes(math_public_key, "math_public_key")
        validate_bytes(math_private_key, "math_private_key")

    # Derive shared secret
    shared_secret = key_manager.derive_shared_secret(math_public_key, math_private_key)
    shared_secret_arr = np.frombuffer(shared_secret[:128], dtype=np.float64)

    # Store hash of shared secret for key validation during decryption
    shared_secret_hash = hashlib.sha256(shared_secret).digest()

    # Transform semantic key
    semantic_vector = semantic_vectorizer.text_to_vector(semantic_key_text)

    # Encode message
    fractal_params = fractal_encoder.encode_message(message, shared_secret_arr, semantic_vector)

    # Generate signature
    signature_gen = FractalSignature()
    signature_image, signature_hash = signature_gen.generate_signature(
        message, shared_secret_arr, semantic_vector
    )

    # Prepare output
    result = {
        "encrypted_data": {
            "fractal_params": [
                {
                    "c": [float(p["c"][0]), float(p["c"][1])],
                    "z0": [float(p["z0"][0]), float(p["z0"][1])],
                    "iteration": int(p["iteration"]),
                    "byte_value": int(p["byte_value"]),
                }
                for p in fractal_params
            ],
            "public_key": list(math_public_key),
            "shared_secret_hash": list(shared_secret_hash),  # Store hash for key validation
            "signature_hash": signature_hash,
            "signature_image_shape": list(signature_image.shape),
        },
        "metadata": {"message_length": len(message), "pqc_scheme": pqc_scheme},
    }

    return result
