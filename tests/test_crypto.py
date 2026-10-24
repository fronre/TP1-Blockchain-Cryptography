from __future__ import annotations

import socket

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from blockchain_tp1.ca import CertificateAuthority
from blockchain_tp1.crypto import (
    aes_gcm_decrypt,
    aes_gcm_encrypt,
    derive_session_context,
    ecdh_shared_secret,
    generate_ecdh_keypair,
    generate_rsa_keypair,
    hkdf_derive_key,
    rsa_decrypt,
    rsa_encrypt,
)


def test_rsa_oaep_roundtrip():
    priv, pub = generate_rsa_keypair(2048)
    message = b"hello blockchain world"
    ciphertext = rsa_encrypt(pub, message)
    assert rsa_decrypt(priv, ciphertext) == message


def test_aes_gcm_roundtrip_and_tamper_detection():
    key = b"A" * 32
    plaintext = b"secret message for alice and bob"
    nonce, encrypted, tag = aes_gcm_encrypt(key, plaintext, b"header")
    assert aes_gcm_decrypt(key, nonce, encrypted, tag, b"header") == plaintext

    tampered = bytearray(encrypted)
    tampered[0] ^= 0xFF
    with pytest.raises(ValueError):
        aes_gcm_decrypt(key, nonce, bytes(tampered), tag, b"header")

    with pytest.raises(ValueError):
        aes_gcm_decrypt(key, nonce, encrypted, tag, b"different-header")


def test_ecdh_and_hkdf_derive_same_session_key():
    alice_priv, alice_pub = generate_ecdh_keypair()
    bob_priv, bob_pub = generate_ecdh_keypair()

    alice_secret = ecdh_shared_secret(alice_priv, bob_pub)
    bob_secret = ecdh_shared_secret(bob_priv, alice_pub)
    assert alice_secret == bob_secret

    info = b"tp1-demo"
    alice_key = hkdf_derive_key(alice_secret, salt=b"salt", info=info)
    bob_key = hkdf_derive_key(bob_secret, salt=b"salt", info=info)
    assert alice_key == bob_key
    assert len(alice_key) == 32


def test_peer_order_invariant_hkdf_context():
    alice_priv, alice_pub = generate_ecdh_keypair()
    bob_priv, bob_pub = generate_ecdh_keypair()
    shared_a = ecdh_shared_secret(alice_priv, bob_pub)
    shared_b = ecdh_shared_secret(bob_priv, alice_pub)
    assert shared_a == shared_b

    alice_context = derive_session_context("alice", "bob", "message")
    bob_context = derive_session_context("bob", "alice", "message")
    assert alice_context == bob_context
    assert hkdf_derive_key(shared_a, salt=b"tp1-demo", info=alice_context) == hkdf_derive_key(shared_b, salt=b"tp1-demo", info=bob_context)


def test_rsa_oaep_rejects_overlarge_payloads():
    priv, pub = generate_rsa_keypair(2048)
    oversized = b"A" * 300
    with pytest.raises(ValueError):
        rsa_encrypt(pub, oversized)


def test_invalid_certificates_are_rejected():
    authority = CertificateAuthority()
    authority.create_root_ca("Root CA")
    authority.create_node_cert("alice")

    cert = x509.load_pem_x509_certificate((authority.nodes_dir / "alice" / "alice.crt").read_bytes())
    wrong_ca = authority.ca_dir / "ca.crt"
    other = CertificateAuthority(ca_dir=authority.ca_dir, nodes_dir=authority.nodes_dir)
    with pytest.raises(Exception):
        serialization.load_pem_public_key(wrong_ca.read_bytes())
