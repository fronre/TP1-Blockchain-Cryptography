# TP1 — Blockchain Cryptography

This project implements a local blockchain cryptography lab on Linux Mint using Python 3.12 and OpenSSL 3.0. It stays entirely inside the current workspace and does not use any external network services.

## Project structure

- `ca/` — local Root CA certificate and private key
- `nodes/` — generated node key material for Alice, Bob, Carol, and Dave
- `src/blockchain_tp1/` — Python implementation
- `tests/` — automated validation tests
- `results/benchmark_results.json` — measured benchmark output

## Virtual environment

Create and activate the project virtual environment:

```bash
cd /home/islamhala/TP1-Blockchain
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Stage 1 — local Root CA

A local Root Certificate Authority is created in `ca/ca.crt` and `ca/ca.key`.
The CA signs X.509 certificates for Alice, Bob, Carol, and Dave under `nodes/<name>/`.

Important note: private keys are written only inside the workspace and are never printed or transmitted. They stay local to the project.

## Stage 2 — RSA, CSR, and X.509 generation

The implementation in `src/blockchain_tp1/ca.py` creates:

- a 4096-bit root CA key and self-signed certificate
- 2048-bit RSA keypairs for each node
- per-node CSRs and CA-issued certificates
- node folders with `.key`, `.crt`, and `.csr` files

## Stage 3 — crypto primitives

The module `src/blockchain_tp1/crypto.py` implements:

- RSA-OAEP encryption/decryption with SHA-256
- AES-256-GCM encryption and decryption
- tamper detection for ciphertext/tag changes
- ECDH key agreement with SECP256R1
- HKDF-SHA256 session-key derivation

## Stage 4 — local socket messaging demo

The local four-node demo lives in `src/blockchain_tp1/socket_demo.py` and `src/blockchain_tp1/node.py`.
It starts local listeners on loopback ports 5001-5004, derives a shared ECDH session key, wraps it under the peer RSA public key, and then encrypts the payload with AES-256-GCM before sending it over the socket.

Run a demo message:

```bash
cd /home/islamhala/TP1-Blockchain
. .venv/bin/activate
export PYTHONPATH=src
python -m blockchain_tp1.socket_demo
```

## Stage 5 — traffic capture instructions

To inspect loopback traffic with Wireshark:

```bash
sudo wireshark -i lo
```

Then filter on:

- `tcp.port == 5001 || tcp.port == 5002 || tcp.port == 5003 || tcp.port == 5004`
- or `ip.addr == 127.0.0.1`

To capture with tcpdump on localhost only:

```bash
sudo tcpdump -i lo -nn -A port 5001 or port 5002 or port 5003 or port 5004
```

This is a local-only loopback capture; no real external network is used.

## Stage 6 — tests

Run the automated test suite:

```bash
cd /home/islamhala/TP1-Blockchain
. .venv/bin/activate
export PYTHONPATH=src
pytest -q
```

Current status: 5 tests passed.

## Stage 7 — benchmark and explanation

Run the benchmark suite:

```bash
cd /home/islamhala/TP1-Blockchain
. .venv/bin/activate
export PYTHONPATH=src
python src/blockchain_tp1/benchmark.py
```

Actual measured results from `results/benchmark_results.json`:

- AES-256-GCM on 1 KB: 0.000095 seconds total (about 10.28 MiB/s)
- AES-256-GCM on 1 MB: 0.00307 seconds total (about 326.08 MiB/s)
- AES-256-GCM on 10 MB: 0.04984 seconds total (about 200.65 MiB/s)
- RSA-OAEP direct encryption for 1 KB, 1 MB, and 10 MB: not feasible with a 2048-bit RSA key because the max OAEP plaintext size is only 190 bytes
- Hybrid RSA + AES: successful for all tested sizes, with 10 MB at 0.03708 seconds total (about 269.72 MiB/s)

Why hybrid encryption is used:

- RSA is excellent for key transport and authenticity, but it is not efficient for large payloads.
- AES-GCM is fast for bulk encryption and provides authenticated encryption.
- The practical workflow is: encrypt the session key with RSA, then encrypt the message body with AES-256-GCM using a random session key.
- This preserves the confidentiality and authenticity properties of public-key cryptography while keeping the performance for large data practical.

## Notes

- The project intentionally uses loopback-only traffic.
- No real external services, no internet network calls, and no private-key exposure are involved.
- The benchmark file is generated locally and kept under `results/`.
