"""
Test bytes support for messages.
This is a regression test to ensure bytes input is always supported.
"""

import unittest
from csf import FractalCryptoSystem
from csf.core.keys import KeyManager


class TestBytesSupport(unittest.TestCase):
    """Test that bytes input is supported for encryption."""

    def setUp(self):
        """Set up test fixtures."""
        self.crypto = FractalCryptoSystem()
        self.key_manager = KeyManager()
        self.public_key, self.private_key = self.key_manager.generate_key_pair()

    def test_encrypt_bytes(self):
        """Test encryption with bytes input."""
        message_str = "secret message: hello Alice! Sponge Bob is not here yet"
        message_bytes = bytes(message_str, "utf-8")

        # Should not raise ValidationError
        encrypted = self.crypto.encrypt(message_bytes, "semantic_key", self.public_key, self.private_key)

        # Should decrypt correctly
        decrypted = self.crypto.decrypt(encrypted, "semantic_key", self.private_key)
        self.assertEqual(decrypted, message_str)

    def test_encrypt_bytes_exact_user_case(self):
        """Test the exact case reported by the user."""
        message = "secret message: hello Alice! Sponge Bob is not here yet"
        message_bytes = bytes(message, "utf-8")

        # This should work without ValidationError
        encrypted = self.crypto.encrypt(message_bytes, "semantic_key", self.public_key, self.private_key)

        decrypted = self.crypto.decrypt(encrypted, "semantic_key", self.private_key)
        self.assertEqual(decrypted, message)

    def test_encrypt_str_still_works(self):
        """Ensure str input still works (backward compatibility)."""
        message = "test message"
        encrypted = self.crypto.encrypt(message, "semantic_key", self.public_key, self.private_key)
        decrypted = self.crypto.decrypt(encrypted, "semantic_key", self.private_key)
        self.assertEqual(decrypted, message)


if __name__ == "__main__":
    unittest.main()

