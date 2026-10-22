from __future__ import annotations

import json
import os
import statistics
import time
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from blockchain_tp1.crypto import aes_gcm_decrypt, aes_gcm_encrypt, generate_rsa_keypair, hkdf_derive_key, rsa_decrypt, rsa_encrypt, ecdh_shared_secret, generate_ecdh_keypair


RESULTS_PATH = Path(__file__).resolve().parents[2] / "results" / "benchmark_results.json"


def time_call(label: str, func, *args, **kwargs) -> tuple[float, object]:
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return elapsed, result


def benchmark_aes(size: int) -> dict:
    key = os.urandom(32)
    plaintext = os.urandom(size)
    nonce, ciphertext, tag = aes_gcm_encrypt(key, plaintext, b"benchmark")
    encrypt_time, _ = time_call("aes_encrypt", aes_gcm_encrypt, key, plaintext, b"benchmark")
    decrypt_time, _ = time_call("aes_decrypt", aes_gcm_decrypt, key, nonce, ciphertext, tag, b"benchmark")
    return {
        "size_bytes": size,
        "encrypt_seconds": encrypt_time,
        "decrypt_seconds": decrypt_time,
        "total_seconds": encrypt_time + decrypt_time,
        "throughput_mib_per_s": (size / (1024 ** 2)) / (encrypt_time + decrypt_time),
    }


def benchmark_direct_rsa(size: int) -> dict:
    key_length = 2048
    public_key_bytes = max(0, key_length // 8 - 2 * 32 - 2)
    if size > public_key_bytes:
        return {
            "size_bytes": size,
            "status": "too_large_for_direct_oaep",
            "rsa_limit_bytes": public_key_bytes,
            "encrypt_seconds": None,
            "decrypt_seconds": None,
            "total_seconds": None,
        }
    priv, pub = generate_rsa_keypair(2048)
    plaintext = os.urandom(size)
    encrypt_time, ciphertext = time_call("rsa_encrypt", rsa_encrypt, pub, plaintext)
    decrypt_time, _ = time_call("rsa_decrypt", rsa_decrypt, priv, ciphertext)
    return {
        "size_bytes": size,
        "status": "ok",
        "rsa_limit_bytes": public_key_bytes,
        "encrypt_seconds": encrypt_time,
        "decrypt_seconds": decrypt_time,
        "total_seconds": encrypt_time + decrypt_time,
        "throughput_mib_per_s": (size / (1024 ** 2)) / (encrypt_time + decrypt_time),
    }


def benchmark_hybrid(size: int) -> dict:
    priv, pub = generate_rsa_keypair(2048)
    plaintext = os.urandom(size)
    aes_key = os.urandom(32)
    nonce, encrypted, tag = aes_gcm_encrypt(aes_key, plaintext, b"hybrid")
    encrypt_time, encrypted_session_key = time_call("rsa_encrypt_session_key", rsa_encrypt, pub, aes_key)
    decrypt_time, _ = time_call("rsa_decrypt_session_key", rsa_decrypt, priv, encrypted_session_key)
    aes_roundtrip_time, _ = time_call("aes_hybrid_round_trip", aes_gcm_decrypt, aes_key, nonce, encrypted, tag, b"hybrid")
    total = encrypt_time + decrypt_time + aes_roundtrip_time
    return {
        "size_bytes": size,
        "status": "ok",
        "encrypt_seconds": encrypt_time + aes_roundtrip_time,
        "decrypt_seconds": decrypt_time,
        "total_seconds": total,
        "throughput_mib_per_s": (size / (1024 ** 2)) / total,
    }


def run_benchmarks() -> dict:
    sizes = [1024, 1024 * 1024, 10 * 1024 * 1024]
    result = {"sizes": sizes, "aes": {}, "rsa_direct": {}, "hybrid": {}}
    for size in sizes:
        result["aes"][str(size)] = benchmark_aes(size)
        result["rsa_direct"][str(size)] = benchmark_direct_rsa(size)
        result["hybrid"][str(size)] = benchmark_hybrid(size)
    return result


def main() -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = run_benchmarks()
    RESULTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
