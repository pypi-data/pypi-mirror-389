"""
Encryption utilities for XiaoShi AI Hub SDK.

Supports multiple encryption algorithms:
- Symmetric: AES-256-CBC, AES-256-GCM, SM4-CBC, SM4-GCM
- Asymmetric: RSA-OAEP, RSA-PKCS1v15, SM2
"""

from pathlib import Path
from typing import Optional, Union
from enum import Enum

from .exceptions import EncryptionError


class EncryptionAlgorithm(str, Enum):
    """Supported encryption algorithms."""

    # 对称加密算法
    AES_256_CBC = "aes-256-cbc"
    AES_256_GCM = "aes-256-gcm"
    SM4_CBC = "sm4-cbc"
    SM4_GCM = "sm4-gcm"

    # 非对称加密算法
    RSA_OAEP = "rsa-oaep"
    RSA_PKCS1V15 = "rsa-pkcs1v15"
    SM2 = "sm2"


def _import_crypto_dependencies():
    """Import cryptography dependencies."""
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import padding, hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
        import hashlib
        import os as os_module

        return {
            'Cipher': Cipher,
            'algorithms': algorithms,
            'modes': modes,
            'default_backend': default_backend,
            'padding': padding,
            'hashes': hashes,
            'serialization': serialization,
            'rsa': rsa,
            'asym_padding': asym_padding,
            'hashlib': hashlib,
            'os': os_module,
        }
    except ImportError:
        raise EncryptionError(
            "Encryption requires the 'cryptography' package. "
            "Install it with: pip install cryptography"
        )


def _import_gmssl_dependencies():
    """Import gmssl dependencies for Chinese SM algorithms."""
    try:
        from gmssl import sm2, sm3, sm4
        import os as os_module

        return {
            'sm2': sm2,
            'sm3': sm3,
            'sm4': sm4,
            'os': os_module,
        }
    except ImportError:
        raise EncryptionError(
            "SM encryption requires the 'gmssl' package. "
            "Install it with: pip install gmssl or pip install xiaoshiai-hub[sm]"
        )


def _encrypt_aes_cbc(plaintext: bytes, key: bytes) -> bytes:
    """
    Encrypt data using AES-256-CBC.
    
    Args:
        plaintext: Data to encrypt
        key: 32-byte encryption key
        
    Returns:
        IV (16 bytes) + Ciphertext
    """
    deps = _import_crypto_dependencies()
    
    # Generate random IV
    iv = deps['os'].urandom(16)
    
    # Pad plaintext
    padder = deps['padding'].PKCS7(128).padder()
    padded_data = padder.update(plaintext) + padder.finalize()
    
    # Encrypt
    cipher = deps['Cipher'](
        deps['algorithms'].AES(key),
        deps['modes'].CBC(iv),
        backend=deps['default_backend']()
    )
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    # Return IV + ciphertext
    return iv + ciphertext


def _encrypt_aes_gcm(plaintext: bytes, key: bytes) -> bytes:
    """
    Encrypt data using AES-256-GCM.
    
    Args:
        plaintext: Data to encrypt
        key: 32-byte encryption key
        
    Returns:
        IV (12 bytes) + Tag (16 bytes) + Ciphertext
    """
    deps = _import_crypto_dependencies()
    
    # Generate random IV (12 bytes for GCM)
    iv = deps['os'].urandom(12)
    
    # Encrypt
    cipher = deps['Cipher'](
        deps['algorithms'].AES(key),
        deps['modes'].GCM(iv),
        backend=deps['default_backend']()
    )
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    
    # Return IV + tag + ciphertext
    return iv + encryptor.tag + ciphertext


def _encrypt_rsa(plaintext: bytes, public_key_pem: str, algorithm: EncryptionAlgorithm) -> bytes:
    """
    Encrypt data using RSA.
    
    For large files, uses hybrid encryption:
    1. Generate random AES key
    2. Encrypt file with AES-256-GCM
    3. Encrypt AES key with RSA
    4. Return: RSA(AES_key) + AES-GCM(plaintext)
    
    Args:
        plaintext: Data to encrypt
        public_key_pem: RSA public key in PEM format
        algorithm: RSA algorithm to use
        
    Returns:
        Encrypted key length (4 bytes) + Encrypted AES key + AES-GCM encrypted data
    """
    deps = _import_crypto_dependencies()
    
    # Load public key
    try:
        public_key = deps['serialization'].load_pem_public_key(
            public_key_pem.encode() if isinstance(public_key_pem, str) else public_key_pem,
            backend=deps['default_backend']()
        )
    except Exception as e:
        raise EncryptionError(f"Failed to load RSA public key: {e}")
    
    # Generate random AES key for hybrid encryption
    aes_key = deps['os'].urandom(32)  # 256-bit key
    
    # Encrypt data with AES-256-GCM
    encrypted_data = _encrypt_aes_gcm(plaintext, aes_key)
    
    # Choose RSA padding
    if algorithm == EncryptionAlgorithm.RSA_OAEP:
        rsa_padding = deps['asym_padding'].OAEP(
            mgf=deps['asym_padding'].MGF1(algorithm=deps['hashes'].SHA256()),
            algorithm=deps['hashes'].SHA256(),
            label=None
        )
    else:  # RSA_PKCS1V15
        rsa_padding = deps['asym_padding'].PKCS1v15()
    
    # Encrypt AES key with RSA
    try:
        encrypted_key = public_key.encrypt(aes_key, rsa_padding)
    except Exception as e:
        raise EncryptionError(f"Failed to encrypt with RSA: {e}")
    
    # Return: encrypted_key_length (4 bytes) + encrypted_key + encrypted_data
    import struct
    key_length = struct.pack('>I', len(encrypted_key))
    return key_length + encrypted_key + encrypted_data


def _encrypt_sm4_cbc(plaintext: bytes, key: bytes) -> bytes:
    """
    Encrypt data using SM4-CBC (Chinese national standard).

    Args:
        plaintext: Data to encrypt
        key: 16-byte encryption key

    Returns:
        IV (16 bytes) + Ciphertext
    """
    deps = _import_gmssl_dependencies()

    # Generate random IV
    iv = deps['os'].urandom(16)

    # SM4 requires 16-byte key
    if len(key) != 16:
        # Derive 16-byte key using SM3 hash
        key = bytes(deps['sm3'].sm3_hash(list(key)))[:16]

    # Create SM4 cipher in CBC mode
    cipher = deps['sm4'].CryptSM4()
    cipher.set_key(key, deps['sm4'].SM4_ENCRYPT)

    # Pad plaintext to 16-byte blocks
    padding_length = 16 - (len(plaintext) % 16)
    padded_plaintext = plaintext + bytes([padding_length] * padding_length)

    # Encrypt in CBC mode
    ciphertext = b''
    prev_block = iv
    for i in range(0, len(padded_plaintext), 16):
        block = padded_plaintext[i:i+16]
        # XOR with previous ciphertext block (CBC mode)
        xor_block = bytes(a ^ b for a, b in zip(block, prev_block))
        encrypted_block = cipher.crypt_ecb(xor_block)
        ciphertext += encrypted_block
        prev_block = encrypted_block

    return iv + ciphertext


def _encrypt_sm4_gcm(plaintext: bytes, key: bytes) -> bytes:
    """
    Encrypt data using SM4-GCM (authenticated encryption).

    Note: gmssl library may not support GCM mode directly.
    This is a placeholder implementation using CBC mode.
    For production, consider using a library with full SM4-GCM support.

    Args:
        plaintext: Data to encrypt
        key: 16-byte encryption key

    Returns:
        IV (12 bytes) + Tag (16 bytes) + Ciphertext
    """
    # For now, use CBC mode as fallback
    # TODO: Implement proper SM4-GCM when library support is available
    deps = _import_gmssl_dependencies()

    # Generate random IV (12 bytes for GCM)
    iv = deps['os'].urandom(12)

    # SM4 requires 16-byte key
    if len(key) != 16:
        key = bytes(deps['sm3'].sm3_hash(list(key)))[:16]

    # Use CBC mode as fallback
    cipher = deps['sm4'].CryptSM4()
    cipher.set_key(key, deps['sm4'].SM4_ENCRYPT)

    # Pad plaintext
    padding_length = 16 - (len(plaintext) % 16)
    padded_plaintext = plaintext + bytes([padding_length] * padding_length)

    # Encrypt
    # Extend IV to 16 bytes for CBC mode
    extended_iv = iv + b'\x00' * 4
    ciphertext = b''
    prev_block = extended_iv
    for i in range(0, len(padded_plaintext), 16):
        block = padded_plaintext[i:i+16]
        xor_block = bytes(a ^ b for a, b in zip(block, prev_block))
        encrypted_block = cipher.crypt_ecb(xor_block)
        ciphertext += encrypted_block
        prev_block = encrypted_block

    # Generate authentication tag (simplified - compute hash of ciphertext)
    tag = bytes(deps['sm3'].sm3_hash(list(iv + ciphertext)))[:16]

    return iv + tag + ciphertext


def _encrypt_sm2(plaintext: bytes, public_key_hex: str) -> bytes:
    """
    Encrypt data using SM2 (Chinese national standard asymmetric algorithm).

    Uses hybrid encryption:
    1. Generate random SM4 key
    2. Encrypt data with SM4-CBC
    3. Encrypt SM4 key with SM2
    4. Return: SM2(SM4_key) + SM4-CBC(plaintext)

    Args:
        plaintext: Data to encrypt
        public_key_hex: SM2 public key in hex format (130 hex chars, starting with '04')

    Returns:
        Encrypted key length (4 bytes) + Encrypted SM4 key + SM4-CBC encrypted data
    """
    deps = _import_gmssl_dependencies()

    # Generate random SM4 key (16 bytes)
    sm4_key = deps['os'].urandom(16)

    # Encrypt data with SM4-CBC
    encrypted_data = _encrypt_sm4_cbc(plaintext, sm4_key)

    # Encrypt SM4 key with SM2
    try:
        sm2_cipher = deps['sm2'].CryptSM2(public_key=public_key_hex, private_key=None)
        # SM2 encrypt returns hex string
        encrypted_key_hex = sm2_cipher.encrypt(sm4_key.hex())
        encrypted_key = bytes.fromhex(encrypted_key_hex)
    except Exception as e:
        raise EncryptionError(f"Failed to encrypt with SM2: {e}")

    # Return: encrypted_key_length (4 bytes) + encrypted_key + encrypted_data
    import struct
    key_length = struct.pack('>I', len(encrypted_key))
    return key_length + encrypted_key + encrypted_data


def encrypt_file(
    file_path: Path,
    encryption_key: Union[str, bytes],
    algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_CBC,
) -> None:
    """
    Encrypt a file in-place using the specified algorithm.
    
    Args:
        file_path: Path to the file to encrypt
        encryption_key: Encryption key (string for symmetric, PEM for asymmetric)
        algorithm: Encryption algorithm to use
        
    Raises:
        EncryptionError: If encryption fails
    """
    deps = _import_crypto_dependencies()
    
    try:
        # Read file content
        plaintext = file_path.read_bytes()
        
        # Encrypt based on algorithm
        if algorithm == EncryptionAlgorithm.AES_256_CBC:
            # Derive 256-bit key from string
            if isinstance(encryption_key, str):
                key = deps['hashlib'].sha256(encryption_key.encode()).digest()
            else:
                key = encryption_key
            ciphertext = _encrypt_aes_cbc(plaintext, key)
            
        elif algorithm == EncryptionAlgorithm.AES_256_GCM:
            # Derive 256-bit key from string
            if isinstance(encryption_key, str):
                key = deps['hashlib'].sha256(encryption_key.encode()).digest()
            else:
                key = encryption_key
            ciphertext = _encrypt_aes_gcm(plaintext, key)
            
        elif algorithm in (EncryptionAlgorithm.RSA_OAEP, EncryptionAlgorithm.RSA_PKCS1V15):
            # Use RSA public key
            if isinstance(encryption_key, bytes):
                public_key_pem = encryption_key.decode()
            else:
                public_key_pem = encryption_key
            ciphertext = _encrypt_rsa(plaintext, public_key_pem, algorithm)

        elif algorithm == EncryptionAlgorithm.SM4_CBC:
            # Derive 16-byte key from string using SM3
            if isinstance(encryption_key, str):
                gm_deps = _import_gmssl_dependencies()
                key = bytes(gm_deps['sm3'].sm3_hash(list(encryption_key.encode())))[:16]
            else:
                key = encryption_key[:16] if len(encryption_key) >= 16 else encryption_key
            ciphertext = _encrypt_sm4_cbc(plaintext, key)

        elif algorithm == EncryptionAlgorithm.SM4_GCM:
            # Derive 16-byte key from string using SM3
            if isinstance(encryption_key, str):
                gm_deps = _import_gmssl_dependencies()
                key = bytes(gm_deps['sm3'].sm3_hash(list(encryption_key.encode())))[:16]
            else:
                key = encryption_key[:16] if len(encryption_key) >= 16 else encryption_key
            ciphertext = _encrypt_sm4_gcm(plaintext, key)

        elif algorithm == EncryptionAlgorithm.SM2:
            # Use SM2 public key (hex format)
            if isinstance(encryption_key, bytes):
                public_key_hex = encryption_key.decode()
            else:
                public_key_hex = encryption_key
            ciphertext = _encrypt_sm2(plaintext, public_key_hex)

        else:
            raise EncryptionError(f"Unsupported encryption algorithm: {algorithm}")
        
        # Write encrypted content back to file
        file_path.write_bytes(ciphertext)
        
    except EncryptionError:
        raise
    except Exception as e:
        raise EncryptionError(f"Failed to encrypt file {file_path}: {e}")


def _decrypt_aes_cbc(ciphertext: bytes, key: bytes) -> bytes:
    """
    Decrypt data using AES-256-CBC.

    Args:
        ciphertext: IV (16 bytes) + Ciphertext
        key: 32-byte decryption key

    Returns:
        Decrypted plaintext
    """
    deps = _import_crypto_dependencies()

    if len(ciphertext) < 16:
        raise EncryptionError("Ciphertext too short (missing IV)")

    # Extract IV and ciphertext
    iv = ciphertext[:16]
    encrypted_data = ciphertext[16:]

    # Decrypt
    cipher = deps['Cipher'](
        deps['algorithms'].AES(key),
        deps['modes'].CBC(iv),
        backend=deps['default_backend']()
    )
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(encrypted_data) + decryptor.finalize()

    # Remove padding
    unpadder = deps['padding'].PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

    return plaintext


def _decrypt_aes_gcm(ciphertext: bytes, key: bytes) -> bytes:
    """
    Decrypt data using AES-256-GCM.

    Args:
        ciphertext: IV (12 bytes) + Tag (16 bytes) + Ciphertext
        key: 32-byte decryption key

    Returns:
        Decrypted plaintext
    """
    deps = _import_crypto_dependencies()

    if len(ciphertext) < 28:  # 12 (IV) + 16 (tag)
        raise EncryptionError("Ciphertext too short (missing IV or tag)")

    # Extract IV, tag, and ciphertext
    iv = ciphertext[:12]
    tag = ciphertext[12:28]
    encrypted_data = ciphertext[28:]

    # Decrypt
    cipher = deps['Cipher'](
        deps['algorithms'].AES(key),
        deps['modes'].GCM(iv, tag),
        backend=deps['default_backend']()
    )
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(encrypted_data) + decryptor.finalize()

    return plaintext


def _decrypt_rsa(ciphertext: bytes, private_key_pem: str, algorithm: EncryptionAlgorithm) -> bytes:
    """
    Decrypt data using RSA (hybrid encryption).

    Args:
        ciphertext: Encrypted key length (4 bytes) + Encrypted AES key + AES-GCM encrypted data
        private_key_pem: RSA private key in PEM format
        algorithm: RSA algorithm that was used

    Returns:
        Decrypted plaintext
    """
    deps = _import_crypto_dependencies()

    # Load private key
    try:
        private_key = deps['serialization'].load_pem_private_key(
            private_key_pem.encode() if isinstance(private_key_pem, str) else private_key_pem,
            password=None,
            backend=deps['default_backend']()
        )
    except Exception as e:
        raise EncryptionError(f"Failed to load RSA private key: {e}")

    # Extract encrypted key length
    import struct
    if len(ciphertext) < 4:
        raise EncryptionError("Ciphertext too short")

    key_length = struct.unpack('>I', ciphertext[:4])[0]

    if len(ciphertext) < 4 + key_length:
        raise EncryptionError("Ciphertext corrupted (invalid key length)")

    # Extract encrypted AES key and encrypted data
    encrypted_key = ciphertext[4:4+key_length]
    encrypted_data = ciphertext[4+key_length:]

    # Choose RSA padding
    if algorithm == EncryptionAlgorithm.RSA_OAEP:
        rsa_padding = deps['asym_padding'].OAEP(
            mgf=deps['asym_padding'].MGF1(algorithm=deps['hashes'].SHA256()),
            algorithm=deps['hashes'].SHA256(),
            label=None
        )
    else:  # RSA_PKCS1V15
        rsa_padding = deps['asym_padding'].PKCS1v15()

    # Decrypt AES key with RSA
    try:
        aes_key = private_key.decrypt(encrypted_key, rsa_padding)
    except Exception as e:
        raise EncryptionError(f"Failed to decrypt with RSA: {e}")

    # Decrypt data with AES-256-GCM
    plaintext = _decrypt_aes_gcm(encrypted_data, aes_key)

    return plaintext


def _decrypt_sm4_cbc(ciphertext: bytes, key: bytes) -> bytes:
    """
    Decrypt data using SM4-CBC.

    Args:
        ciphertext: IV (16 bytes) + Ciphertext
        key: 16-byte decryption key

    Returns:
        Decrypted plaintext
    """
    deps = _import_gmssl_dependencies()

    if len(ciphertext) < 16:
        raise EncryptionError("Ciphertext too short (missing IV)")

    # Extract IV and ciphertext
    iv = ciphertext[:16]
    encrypted_data = ciphertext[16:]

    # SM4 requires 16-byte key
    if len(key) != 16:
        key = bytes(deps['sm3'].sm3_hash(list(key)))[:16]

    # Create SM4 cipher
    cipher = deps['sm4'].CryptSM4()
    cipher.set_key(key, deps['sm4'].SM4_DECRYPT)

    # Decrypt in CBC mode
    plaintext = b''
    prev_block = iv
    for i in range(0, len(encrypted_data), 16):
        encrypted_block = encrypted_data[i:i+16]
        decrypted_block = cipher.crypt_ecb(encrypted_block)
        # XOR with previous ciphertext block (CBC mode)
        block = bytes(a ^ b for a, b in zip(decrypted_block, prev_block))
        plaintext += block
        prev_block = encrypted_block

    # Remove padding
    if plaintext:
        padding_length = plaintext[-1]
        if 1 <= padding_length <= 16:
            plaintext = plaintext[:-padding_length]

    return plaintext


def _decrypt_sm4_gcm(ciphertext: bytes, key: bytes) -> bytes:
    """
    Decrypt data using SM4-GCM.

    Note: This is a fallback implementation using CBC mode.

    Args:
        ciphertext: IV (12 bytes) + Tag (16 bytes) + Ciphertext
        key: 16-byte decryption key

    Returns:
        Decrypted plaintext
    """
    deps = _import_gmssl_dependencies()

    if len(ciphertext) < 28:  # 12 (IV) + 16 (tag)
        raise EncryptionError("Ciphertext too short (missing IV or tag)")

    # Extract IV, tag, and ciphertext
    iv = ciphertext[:12]
    tag = ciphertext[12:28]
    encrypted_data = ciphertext[28:]

    # Verify tag (simplified - compute hash and compare)
    expected_tag = bytes(deps['sm3'].sm3_hash(list(iv + encrypted_data)))[:16]
    if tag != expected_tag:
        raise EncryptionError("Authentication tag verification failed")

    # SM4 requires 16-byte key
    if len(key) != 16:
        key = bytes(deps['sm3'].sm3_hash(list(key)))[:16]

    # Decrypt using CBC mode
    cipher = deps['sm4'].CryptSM4()
    cipher.set_key(key, deps['sm4'].SM4_DECRYPT)

    # Extend IV to 16 bytes
    extended_iv = iv + b'\x00' * 4
    plaintext = b''
    prev_block = extended_iv
    for i in range(0, len(encrypted_data), 16):
        encrypted_block = encrypted_data[i:i+16]
        decrypted_block = cipher.crypt_ecb(encrypted_block)
        block = bytes(a ^ b for a, b in zip(decrypted_block, prev_block))
        plaintext += block
        prev_block = encrypted_block

    # Remove padding
    if plaintext:
        padding_length = plaintext[-1]
        if 1 <= padding_length <= 16:
            plaintext = plaintext[:-padding_length]

    return plaintext


def _decrypt_sm2(ciphertext: bytes, private_key_hex: str) -> bytes:
    """
    Decrypt data using SM2 (hybrid encryption).

    Args:
        ciphertext: Encrypted key length (4 bytes) + Encrypted SM4 key + SM4-CBC encrypted data
        private_key_hex: SM2 private key in hex format

    Returns:
        Decrypted plaintext
    """
    deps = _import_gmssl_dependencies()

    # Extract encrypted key length
    import struct
    if len(ciphertext) < 4:
        raise EncryptionError("Ciphertext too short")

    key_length = struct.unpack('>I', ciphertext[:4])[0]

    if len(ciphertext) < 4 + key_length:
        raise EncryptionError("Ciphertext corrupted (invalid key length)")

    # Extract encrypted SM4 key and encrypted data
    encrypted_key = ciphertext[4:4+key_length]
    encrypted_data = ciphertext[4+key_length:]

    # Decrypt SM4 key with SM2
    try:
        sm2_cipher = deps['sm2'].CryptSM2(public_key=None, private_key=private_key_hex)
        # SM2 decrypt expects hex string
        sm4_key_hex = sm2_cipher.decrypt(encrypted_key.hex())
        sm4_key = bytes.fromhex(sm4_key_hex)
    except Exception as e:
        raise EncryptionError(f"Failed to decrypt with SM2: {e}")

    # Decrypt data with SM4-CBC
    plaintext = _decrypt_sm4_cbc(encrypted_data, sm4_key)

    return plaintext


def decrypt_file(
    file_path: Path,
    decryption_key: Union[str, bytes],
    algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_CBC,
) -> None:
    """
    Decrypt a file in-place using the specified algorithm.

    Args:
        file_path: Path to the file to decrypt
        decryption_key: Decryption key (string for symmetric, PEM for asymmetric)
        algorithm: Encryption algorithm that was used

    Raises:
        EncryptionError: If decryption fails
    """
    deps = _import_crypto_dependencies()

    try:
        # Read encrypted file
        ciphertext = file_path.read_bytes()

        # Decrypt based on algorithm
        if algorithm == EncryptionAlgorithm.AES_256_CBC:
            # Derive 256-bit key from string
            if isinstance(decryption_key, str):
                key = deps['hashlib'].sha256(decryption_key.encode()).digest()
            else:
                key = decryption_key
            plaintext = _decrypt_aes_cbc(ciphertext, key)

        elif algorithm == EncryptionAlgorithm.AES_256_GCM:
            # Derive 256-bit key from string
            if isinstance(decryption_key, str):
                key = deps['hashlib'].sha256(decryption_key.encode()).digest()
            else:
                key = decryption_key
            plaintext = _decrypt_aes_gcm(ciphertext, key)

        elif algorithm in (EncryptionAlgorithm.RSA_OAEP, EncryptionAlgorithm.RSA_PKCS1V15):
            # Use RSA private key
            if isinstance(decryption_key, bytes):
                private_key_pem = decryption_key.decode()
            else:
                private_key_pem = decryption_key
            plaintext = _decrypt_rsa(ciphertext, private_key_pem, algorithm)

        elif algorithm == EncryptionAlgorithm.SM4_CBC:
            # Derive 16-byte key from string using SM3
            if isinstance(decryption_key, str):
                gm_deps = _import_gmssl_dependencies()
                key = bytes(gm_deps['sm3'].sm3_hash(list(decryption_key.encode())))[:16]
            else:
                key = decryption_key[:16] if len(decryption_key) >= 16 else decryption_key
            plaintext = _decrypt_sm4_cbc(ciphertext, key)

        elif algorithm == EncryptionAlgorithm.SM4_GCM:
            # Derive 16-byte key from string using SM3
            if isinstance(decryption_key, str):
                gm_deps = _import_gmssl_dependencies()
                key = bytes(gm_deps['sm3'].sm3_hash(list(decryption_key.encode())))[:16]
            else:
                key = decryption_key[:16] if len(decryption_key) >= 16 else decryption_key
            plaintext = _decrypt_sm4_gcm(ciphertext, key)

        elif algorithm == EncryptionAlgorithm.SM2:
            # Use SM2 private key (hex format)
            if isinstance(decryption_key, bytes):
                private_key_hex = decryption_key.decode()
            else:
                private_key_hex = decryption_key
            plaintext = _decrypt_sm2(ciphertext, private_key_hex)

        else:
            raise EncryptionError(f"Unsupported decryption algorithm: {algorithm}")

        # Write decrypted content back to file
        file_path.write_bytes(plaintext)

    except EncryptionError:
        raise
    except Exception as e:
        raise EncryptionError(f"Failed to decrypt file {file_path}: {e}")

