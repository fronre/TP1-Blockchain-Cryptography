# TP1 — Blockchain Cryptography

A local secure blockchain-inspired cryptography lab built in Python. The project demonstrates how a small distributed system can use a local Root CA, X.509 certificates, RSA key transport, ECDH session-key exchange, and AES-GCM authenticated encryption to securely move data between nodes over loopback-only sockets.

## Project goal

This lab shows how the following primitives work together in practice:

- Public-key identity through a local Certificate Authority
- Certificate-based trust for each node
- Secure key exchange using ECDH
- Hybrid encryption using RSAش + AES-GCM
- Local socket communication without external network access
- Benchmarking to compare practical performance trade-offs

## Repository structure

- `ca/` — local Root CA certificate and private key
- `nodes/` — per-node certificates, CSRs, RSA keys, and ECDH public keys
- `src/blockchain_tp1/` — Python implementation
- `tests/` — validation tests
- `results/benchmark_results.json` — benchmark measurements

## Architecture overview

### 1. Local Root CA

The project creates a self-signed root certificate authority in `ca/ca.crt` and `ca/ca.key`.
The CA signs certificates for Alice, Bob, Carol, and Dave.
This gives each node a local identity trusted by the lab environment.

### 2. Node identity and certificates

Each node is created with:

- a 2048-bit RSA private key
- a certificate signed by the local CA
- a CSR for certificate generation
- a public ECDH key used for session-key exchange

### 3. Cryptographic primitives

The implementation in `src/blockchain_tp1/crypto.py` includes:

- RSA-OAEP encryption and decryption with SHA-256
- AES-256-GCM encryption and decryption with authentication tags
- tamper detection for modified ciphertext or tag values
- ECDH key agreement using SECP256R1
- HKDF-SHA256 derivation of session keys

### 4. Secure message flow

The data path is as follows:

1. Alice and Bob exchange ECDH public keys.
2. Each side derives the same shared secret.
3. HKDF turns that secret into a 32-byte session key.
4. The message payload is encrypted with AES-256-GCM.
5. The session key is wrapped using the peer RSA public key.
6. The encrypted payload and wrapped key are sent through a local socket.
7. The receiver decrypts the wrapped session key with its RSA private key.
8. The receiver decrypts the payload and validates the authentication tag.

This is the classic hybrid encryption pattern:

- RSA protects the session key
- AES protects the actual data
- GCM ensures confidentiality and integrity together

## Run the project

Create and activate the virtual environment:

```bash
cd /home/islamhala/Desktop/TP1-Blockchain
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run the demo:

```bash
cd /home/islamhala/Desktop/TP1-Blockchain
. .venv/bin/activate
export PYTHONPATH=src
python -m blockchain_tp1.socket_demo
```

Run the tests:

```bash
cd /home/islamhala/Desktop/TP1-Blockchain
. .venv/bin/activate
export PYTHONPATH=src
pytest -q
```

Run the benchmark suite:

```bash
cd /home/islamhala/Desktop/TP1-Blockchain
. .venv/bin/activate
export PYTHONPATH=src
python src/blockchain_tp1/benchmark.py
```

Launch the Qt dashboard:

```bash
cd /home/islamhala/Desktop/TP1-Blockchain
. .venv/bin/activate
export PYTHONPATH=src
python -m blockchain_tp1.gui.main
```

## Local network and traffic flow

The demo is intentionally loopback-only:

- Nodes listen on `127.0.0.1`
- Ports: `5001` to `5004`
- No internet access is used
- No external service is required
- Traffic is fully contained inside the current workspace environment

This makes the lab safe, deterministic, and easy to inspect with tools like `tcpdump` or Wireshark.

## Traffic inspection

To view loopback traffic with Wireshark:

```bash
sudo wireshark -i lo
```

Useful filters:

- `tcp.port == 5001 || tcp.port == 5002 || tcp.port == 5003 || tcp.port == 5004`
- `ip.addr == 127.0.0.1`

To inspect with tcpdump:

```bash
sudo tcpdump -i lo -nn -A port 5001 or port 5002 or port 5003 or port 5004
```

## Test status

The current automated test status is:

- 6 tests passed

This covers the CA, cryptographic primitives, node demo flow, and the GUI smoke test.

## Benchmark summary

The benchmark results in `results/benchmark_results.json` demonstrate the expected behavior:

- AES-GCM is very fast for large payloads
- Direct RSA encryption is limited by OAEP size constraints
- Hybrid RSA + AES is the practical solution for larger messages
- The lab validates that key transport and bulk encryption are separated cleanly

Representative results:

- AES-GCM on 10 MB: about 234 MiB/s
- Hybrid RSA + AES on 10 MB: about 310 MiB/s
- Direct RSA-OAEP is infeasible for payloads larger than about 190 bytes under a 2048-bit key

## Why this matters

This project shows a realistic minimum viable secure data flow:

- identify each party with certificates
- exchange shared ephemeral keys
- protect the payload with symmetric encryption
- preserve integrity with authentication tags
- keep the communication local and private by design

## Notes

- Private keys remain local to the workspace and are not transmitted externally.
- The demo is educational and intentionally restricted to localhost.
- The system is built for safe local experimentation and demonstration.

## Fixed cryptographic design

This repository uses a consistent hybrid-encryption flow for authenticated local messaging:

1. Each node keeps a persistent ECDH keypair on SECP256R1.
2. The public ECDH key is stored under each node directory and loaded by peers.
3. Alice and Bob derive the same shared secret using ECDH.
4. The shared secret is converted to a 32-byte AES key with HKDF-SHA256 using an order-invariant context derived from the sorted peer names and a fixed label.
5. The payload is encrypted with AES-256-GCM using a fresh nonce and authenticated data (AAD).
6. The AES key is wrapped with the peer RSA public key via RSA-OAEP-SHA256 for transport.
7. The receiver decrypts the wrapped key with its RSA private key, validates the HKDF context, decrypts with AES-GCM, and rejects any tampered nonce, ciphertext, or authentication tag.

This avoids the previous bug where the HKDF info string depended on the local node name and caused different session keys for the same peer pair.

## Security limitations

- The lab is intentionally loopback-only and is not a production PKI.
- The local CA is a demonstrator root; it should not be used outside a trusted lab environment.
- The ECDH keys are persistent in this project for simplicity and reproducibility, but they are still stored only under the local node directories and not exported.
- The network metadata such as sender, receiver, nonce, salt, and ciphertext length are visible on the wire; only the payload confidentiality and integrity are protected by AES-GCM.
- Packet capture may reveal the plaintext size and protocol metadata even when the payload itself is encrypted.

## Four-node demo and capture

Run the four-node local demo:

```bash
cd /home/islamhala/Desktop/TP1-Blockchain
. .venv/bin/activate
export PYTHONPATH=src
python -m blockchain_tp1.socket_demo
```

The secure demo uses the encrypted message path. To inspect loopback traffic, run:

```bash
sudo tcpdump -i lo -nn -A port 5001 or port 5002 or port 5003 or port 5004
```

or:

```bash
sudo wireshark -i lo
```

This project was not verified with an actual Wireshark or tcpdump capture in this session, so packet capture output should be treated as a documented procedure rather than a confirmed runtime result.
