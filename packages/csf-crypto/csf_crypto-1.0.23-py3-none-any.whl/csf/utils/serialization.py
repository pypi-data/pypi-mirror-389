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
    
    # OPTIMIZED: Pre-allocate lists and use vectorized operations
    num_params = len(fractal_params)
    c_real_arr = []
    c_imag_arr = []
    z0_real_arr = []
    z0_imag_arr = []
    iterations_arr = []
    byte_values_arr = []
    
    # Extract all values in single pass
    for param in fractal_params:
        c_tuple = param["c"]
        z0_tuple = param["z0"]
        c_real = c_tuple[0] if isinstance(c_tuple, (tuple, list)) else c_tuple
        c_imag = c_tuple[1] if isinstance(c_tuple, (tuple, list)) else 0.0
        z0_real = z0_tuple[0] if isinstance(z0_tuple, (tuple, list)) else z0_tuple
        z0_imag = z0_tuple[1] if isinstance(z0_tuple, (tuple, list)) else 0.0
        
        c_real_arr.append(c_real)
        c_imag_arr.append(c_imag)
        z0_real_arr.append(z0_real)
        z0_imag_arr.append(z0_imag)
        iterations_arr.append(param["iteration"])
        byte_values_arr.append(param["byte_value"])
    
    # OPTIMIZED: Vectorized validation using NumPy (if available)
    try:
        import numpy as np
        c_real_np = np.array(c_real_arr, dtype=np.float64)
        c_imag_np = np.array(c_imag_arr, dtype=np.float64)
        z0_real_np = np.array(z0_real_arr, dtype=np.float64)
        z0_imag_np = np.array(z0_imag_arr, dtype=np.float64)
        
        # Vectorized finite check and replacement
        c_real_np = np.where(np.isfinite(c_real_np), c_real_np, 0.0)
        c_imag_np = np.where(np.isfinite(c_imag_np), c_imag_np, 0.0)
        z0_real_np = np.where(np.isfinite(z0_real_np), np.clip(z0_real_np, -1e100, 1e100), 0.0)
        z0_imag_np = np.where(np.isfinite(z0_imag_np), np.clip(z0_imag_np, -1e100, 1e100), 0.0)
        
        # Quantize and append
        for i in range(num_params):
            optimized["c_real"].append(quantize_c_float(c_real_np[i]))
            optimized["c_imag"].append(quantize_c_float(c_imag_np[i]))
            optimized["z0_real"].append(float(z0_real_np[i]))
            optimized["z0_imag"].append(float(z0_imag_np[i]))
            optimized["iterations"].append(iterations_arr[i])
            optimized["byte_values"].append(byte_values_arr[i])
    except ImportError:
        # Fallback to Python loops if NumPy not available
        for i in range(num_params):
            c_real = c_real_arr[i]
            c_imag = c_imag_arr[i]
            z0_real = z0_real_arr[i]
            z0_imag = z0_imag_arr[i]
            
            # Ensure finite values
            if not math.isfinite(c_real):
                c_real = 0.0
            if not math.isfinite(c_imag):
                c_imag = 0.0
            if not math.isfinite(z0_real):
                z0_real = 0.0
            if not math.isfinite(z0_imag):
                z0_imag = 0.0
            
            optimized["c_real"].append(quantize_c_float(c_real))
            optimized["c_imag"].append(quantize_c_float(c_imag))
            optimized["z0_real"].append(float(max(-1e100, min(1e100, z0_real))))
            optimized["z0_imag"].append(float(max(-1e100, min(1e100, z0_imag))))
            optimized["iterations"].append(iterations_arr[i])
            optimized["byte_values"].append(byte_values_arr[i])
    
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
        },
        "metadata": encrypted_dict["metadata"],
    }
    
    # Only include signature if present (OPTIMIZATION: signature is optional)
    if "signature_hash" in encrypted_data:
        optimized_dict["encrypted_data"]["signature_hash"] = encrypted_data["signature_hash"]
    if "signature_image_shape" in encrypted_data:
        optimized_dict["encrypted_data"]["signature_image_shape"] = list(encrypted_data["signature_image_shape"])
    
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

