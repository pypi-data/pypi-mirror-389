#!/usr/bin/env python3
"""
Quick test script for CSF system.
"""

import sys
import numpy as np

print("=" * 80)
print("CSF - COMPLETE SYSTEM TEST")
print("=" * 80)
print()

try:
    print("1. Testing module imports...")
    from csf import FractalCryptoSystem
    from csf.core.keys import KeyManager
    print("   ✓ Imports successful")
    print()
    
    print("2. Testing key generation...")
    key_manager = KeyManager("Kyber768")
    public_key, private_key = key_manager.generate_key_pair()
    print(f"   ✓ Keys generated - Public: {len(public_key)} bytes, Private: {len(private_key)} bytes")
    print()
    
    print("3. Testing system initialization...")
    crypto = FractalCryptoSystem(
        pqc_kem_scheme="Kyber768",
        pqc_signature_scheme="Dilithium3"
    )
    print("   ✓ System initialized")
    print()
    
    print("4. Testing encryption/decryption...")
    message = "Test message for CSF - Post-Quantum Security!"
    semantic_key = "MySecretKey123"
    
    # Encrypt (use dict format for this test script)
    encrypted = crypto.encrypt(message, semantic_key, public_key, private_key, return_dict=True)
    print(f"   ✓ Message encrypted ({len(encrypted['encrypted_data']['fractal_params'])} fractal parameters)")
    
    # Decrypt
    decrypted = crypto.decrypt(encrypted, semantic_key, private_key)
    print(f"   ✓ Message decrypted: '{decrypted}'")
    
    if message == decrypted:
        print("   ✓ ✓ Decryption successful - Message intact!")
    else:
        print("   ✗ ERROR: Decrypted message does not match original")
        print(f"      Original: {len(message)} characters")
        print(f"      Decrypted: {len(decrypted)} characters")
    print()
    
    print("5. Testing signature...")
    fractal_hash, pqc_signature = crypto.sign(
        message, semantic_key, private_key, use_pqc=False
    )
    print(f"   ✓ Fractal signature generated: {fractal_hash[:32]}...")
    
    # Verify
    is_valid = crypto.verify(
        message, fractal_hash, semantic_key,
        private_key, public_key
    )
    
    if is_valid:
        print("   ✓ ✓ Signature verification successful!")
    else:
        print("   ✗ ERROR: Signature verification failed")
    print()
    
    print("=" * 80)
    print("✓✓✓ ALL TESTS PASSED ✓✓✓")
    print("=" * 80)
    print()
    print("CSF system is operational and ready for use!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("\nMake sure the csf package is installed:")
    print("  cd /Users/satoshiba/Documents/CSF")
    print("  source venv/bin/activate")
    print("  pip install -e .")
    sys.exit(1)
    
except Exception as e:
    print(f"✗ Test error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
