"""
Binary serialization for CSF encrypted data.

Optimized binary format using MessagePack with float quantization and compression.
This reduces file size by 10-45x compared to JSON format.
"""

import math
import zlib
from typing import Dict, Union, Any, Optional
from csf.utils.compression import compress_data, decompress_data

try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False

import json


# Float quantization parameters
# For c parameters: [0, 1) range -> 24-bit integers (improved precision for decoding accuracy)
# For z0 parameters: larger range -> 32-bit floats (preserve precision)
C_SCALE = 2**24  # 16777216 for 24-bit unsigned integers (c is in [0, 1))
# Increased from 16-bit to 24-bit to preserve decoding accuracy
C_RANGE = 1.0


def quantize_c_float(value: float) -> int:
    """
    Quantize a c parameter float to a 24-bit unsigned integer.
    c parameters are in [0, 1) range.
    Increased precision from 16-bit to 24-bit to avoid decoding errors.
    
    Args:
        value: Float value in [0, 1)
        
    Returns:
        Quantized integer value (0-16777215)
    """
    # Clamp to [0, 1) range and scale
    clamped = max(0.0, min(0.9999999, value))  # Avoid 1.0
    return int(clamped * C_SCALE)


def dequantize_c_float(value: int) -> float:
    """
    Dequantize a 24-bit integer back to c float.
    
    Args:
        value: Quantized integer value (0-16777215)
        
    Returns:
        Dequantized float value in [0, 1)
    """
    return float(value) / C_SCALE


def optimize_fractal_params(fractal_params: list) -> Dict[str, Any]:
    """
    Optimize fractal parameters for binary storage.
    
    Converts:
    - c parameters (in [0, 1)) to quantized 16-bit unsigned integers
    - z0 parameters to 32-bit floats (preserve precision for larger values)
    - Stores as compact arrays
    
    Args:
        fractal_params: List of fractal parameter dictionaries
        
    Returns:
        Optimized dictionary structure
    """
    optimized = {
        "c_real": [],  # 24-bit unsigned ints (increased from 16-bit for precision)
        "c_imag": [],  # 24-bit unsigned ints (increased from 16-bit for precision)
        "z0_real": [],  # 32-bit floats
        "z0_imag": [],  # 32-bit floats
        "iterations": [],  # 32-bit ints
        "byte_values": [],  # 8-bit values
    }
    
    for param in fractal_params:
        # Validate and sanitize parameters
        c_real = param["c"][0]
        c_imag = param["c"][1]
        z0_real = param["z0"][0]
        z0_imag = param["z0"][1]
        
        # Ensure finite values
        if not math.isfinite(c_real):
            c_real = 0.0
        if not math.isfinite(c_imag):
            c_imag = 0.0
        if not math.isfinite(z0_real):
            z0_real = 0.0
        if not math.isfinite(z0_imag):
            z0_imag = 0.0
        
        # Quantize c parameters (in [0, 1)) to 16-bit unsigned integers
        optimized["c_real"].append(quantize_c_float(c_real))
        optimized["c_imag"].append(quantize_c_float(c_imag))
        # Keep z0 as 32-bit floats (they can be any float64 value, but clamped)
        optimized["z0_real"].append(float(max(-1e100, min(1e100, z0_real))))
        optimized["z0_imag"].append(float(max(-1e100, min(1e100, z0_imag))))
        optimized["iterations"].append(param["iteration"])
        optimized["byte_values"].append(param["byte_value"])
    
    return optimized


def restore_fractal_params(optimized: Dict[str, Any]) -> list:
    """
    Restore fractal parameters from optimized format.
    
    Args:
        optimized: Optimized dictionary structure
        
    Returns:
        List of fractal parameter dictionaries
    """
    params = []
    
    for i in range(len(optimized["c_real"])):
        params.append({
            "c": (
                dequantize_c_float(optimized["c_real"][i]),
                dequantize_c_float(optimized["c_imag"][i]),
            ),
            "z0": (
                float(optimized["z0_real"][i]),  # Already a float
                float(optimized["z0_imag"][i]),  # Already a float
            ),
            "iteration": optimized["iterations"][i],
            "byte_value": optimized["byte_values"][i],
        })
    
    return params


def serialize_encrypted_data(encrypted_dict: Dict, compress: bool = True) -> bytes:
    """
    Serialize encrypted data to optimized binary format.
    
    Args:
        encrypted_dict: Dictionary from encrypt() function
        compress: Whether to apply zlib compression (default: True)
        
    Returns:
        Binary serialized data as bytes
    """
    if not MSGPACK_AVAILABLE:
        # Fallback to JSON if msgpack not available (less optimal)
        json_str = json.dumps(encrypted_dict, ensure_ascii=False)
        data = json_str.encode("utf-8")
        if compress:
            data = zlib.compress(data, level=6)
        return data
    
    # Optimize fractal parameters
    encrypted_data = encrypted_dict["encrypted_data"].copy()
    fractal_params = encrypted_data["fractal_params"]
    optimized_params = optimize_fractal_params(fractal_params)
    
    # Optimize binary data: convert lists to compact binary format
    # Public key: bytes instead of list of integers
    public_key_list = encrypted_data["public_key"]
    if isinstance(public_key_list, list):
        public_key_bytes = bytes(public_key_list)
    else:
        public_key_bytes = public_key_list if isinstance(public_key_list, bytes) else bytes(public_key_list)
    
    # Shared secret hash: bytes instead of list
    shared_secret_hash_list = encrypted_data["shared_secret_hash"]
    if isinstance(shared_secret_hash_list, list):
        shared_secret_hash_bytes = bytes(shared_secret_hash_list)
    else:
        shared_secret_hash_bytes = shared_secret_hash_list if isinstance(shared_secret_hash_list, bytes) else bytes(shared_secret_hash_list)
    
    # Build optimized structure with binary data
    optimized_dict = {
        "encrypted_data": {
            "fractal_params": optimized_params,
            "public_key": public_key_bytes,  # Binary bytes (much more compact)
            "shared_secret_hash": shared_secret_hash_bytes,  # Binary bytes
            "signature_hash": encrypted_data["signature_hash"],
            "signature_image_shape": list(encrypted_data["signature_image_shape"]),
        },
        "metadata": encrypted_dict["metadata"],
    }
    
    # Serialize with MessagePack
    packed = msgpack.packb(optimized_dict, use_bin_type=True, strict_types=False)
    
    # Apply compression if requested (use optimized compression)
    if compress:
        packed = compress_data(packed, algorithm="auto", level=1)  # Fast compression
    
    return packed


def deserialize_encrypted_data(data: bytes, compressed: Optional[bool] = None) -> Dict:
    """
    Deserialize encrypted data from binary format.
    
    Args:
        data: Binary serialized data
        compressed: Whether data is compressed (auto-detect if None)
        
    Returns:
        Dictionary compatible with decrypt() function
    """
    # Auto-detect compression by trying to decompress
    if compressed is None:
        try:
            # Try decompressing - if it fails, data is not compressed
            data = decompress_data(data, algorithm="auto")
        except:
            # Not compressed, use as-is
            pass
    elif compressed:
        data = decompress_data(data, algorithm="auto")
    
    # Try MessagePack first
    if MSGPACK_AVAILABLE:
        try:
            unpacked = msgpack.unpackb(data, raw=False, strict_map_key=False)
            
            # Restore fractal parameters from optimized format
            if "encrypted_data" in unpacked and "fractal_params" in unpacked["encrypted_data"]:
                optimized_params = unpacked["encrypted_data"]["fractal_params"]
                
                # Check if it's already in dict format (backward compatibility)
                if isinstance(optimized_params, list) and len(optimized_params) > 0:
                    # Old format (list of dicts) - return as-is
                    return unpacked
                
                # New optimized format - restore
                restored_params = restore_fractal_params(optimized_params)
                unpacked["encrypted_data"]["fractal_params"] = restored_params
            
            # Restore binary data to list format for backward compatibility with decrypt()
            if "encrypted_data" in unpacked:
                # Public key: convert bytes back to list if needed (for backward compatibility)
                public_key = unpacked["encrypted_data"].get("public_key")
                if isinstance(public_key, bytes):
                    unpacked["encrypted_data"]["public_key"] = list(public_key)
                
                # Shared secret hash: convert bytes back to list if needed
                shared_secret_hash = unpacked["encrypted_data"].get("shared_secret_hash")
                if isinstance(shared_secret_hash, bytes):
                    unpacked["encrypted_data"]["shared_secret_hash"] = list(shared_secret_hash)
            
            return unpacked
        except (msgpack.exceptions.ExtraData, msgpack.exceptions.UnpackException):
            # Not MessagePack, try JSON
            pass
    
    # Fallback to JSON
    try:
        json_str = data.decode("utf-8")
        return json.loads(json_str)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("Invalid encrypted data format: cannot deserialize as MessagePack or JSON")


def is_binary_format(data: Union[bytes, Dict]) -> bool:
    """
    Check if data is in binary format.
    
    Args:
        data: Data to check (bytes or dict)
        
    Returns:
        True if data is bytes (binary format), False if dict (legacy format)
    """
    return isinstance(data, bytes)

