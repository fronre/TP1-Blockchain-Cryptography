from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

from blockchain_tp1.crypto import (
    aes_gcm_decrypt,
    aes_gcm_encrypt,
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
    try:
        aes_gcm_decrypt(key, nonce, bytes(tampered), tag, b"header")
        assert False, "Expected tamper detection to fail"
    except ValueError:
        pass


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
