from __future__ import annotations

import base64
import hashlib
import os
from typing import Optional

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, hmac, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def generate_rsa_keypair(bits: int = 2048) -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    return private_key, private_key.public_key()


def rsa_public_key_from_bytes(data: bytes) -> rsa.RSAPublicKey:
    return serialization.load_pem_public_key(data)


def rsa_private_key_from_bytes(data: bytes) -> rsa.RSAPrivateKey:
    return serialization.load_pem_private_key(data, password=None)


def rsa_encrypt(public_key: rsa.RSAPublicKey, plaintext: bytes) -> bytes:
    return public_key.encrypt(
        plaintext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def rsa_decrypt(private_key: rsa.RSAPrivateKey, ciphertext: bytes) -> bytes:
    return private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def aes_gcm_encrypt(key: bytes, plaintext: bytes, associated_data: Optional[bytes] = None) -> tuple[bytes, bytes, bytes]:
    if len(key) != 32:
        raise ValueError("AES-256-GCM requires exactly 32 bytes key material.")
    nonce = os.urandom(12)
    aad = associated_data or b""
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, aad)
    tag = ciphertext[-16:]
    encrypted = ciphertext[:-16]
    return nonce, encrypted, tag


def aes_gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes, associated_data: Optional[bytes] = None) -> bytes:
    if len(key) != 32:
        raise ValueError("AES-256-GCM requires exactly 32 bytes key material.")
    aad = associated_data or b""
    try:
        return AESGCM(key).decrypt(nonce, ciphertext + tag, aad)
    except InvalidTag as exc:
        raise ValueError("Authentication failed: ciphertext or tag was tampered with") from exc


def generate_ecdh_keypair(curve: str = "SECP256R1") -> tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
    if curve == "SECP256R1":
        private_key = ec.generate_private_key(ec.SECP256R1())
    elif curve == "SECP384R1":
        private_key = ec.generate_private_key(ec.SECP384R1())
    else:
        raise ValueError(f"Unsupported curve: {curve}")
    return private_key, private_key.public_key()


def ecdh_shared_secret(private_key: ec.EllipticCurvePrivateKey, peer_public_key: ec.EllipticCurvePublicKey) -> bytes:
    shared = private_key.exchange(ec.ECDH(), peer_public_key)
    return shared


def hkdf_derive_key(shared_secret: bytes, salt: Optional[bytes] = None, info: bytes = b"tp1-session") -> bytes:
    if salt is None:
        salt = b"" 
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=info,
    ).derive(shared_secret)


def encode_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def decode_base64(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))
