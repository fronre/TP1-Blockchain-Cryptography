from __future__ import annotations

import base64
import json
import os
import socket
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, ec

from .crypto import (
    aes_gcm_decrypt,
    aes_gcm_encrypt,
    derive_session_context,
    ecdh_shared_secret,
    generate_ecdh_keypair,
    hkdf_derive_key,
)


@dataclass
class NodeIdentity:
    name: str
    private_key: rsa.RSAPrivateKey
    cert: x509.Certificate
    public_key: rsa.RSAPublicKey
    ecdh_private: ec.EllipticCurvePrivateKey
    ecdh_public: ec.EllipticCurvePublicKey


class BlockchainNode:
    def __init__(self, name: str, root_ca_cert_path: Path | str, keys_dir: Path | str, port: int | None = None):
        self.name = name
        self.root_ca_cert_path = Path(root_ca_cert_path)
        self.keys_dir = Path(keys_dir)
        self.port = port or (5001 + ("alice bob carol dave".split().index(name) if name in ["alice", "bob", "carol", "dave"] else 0))
        self.entity = self._load_identity()
        self.incoming_messages: list[dict[str, Any]] = []
        self.lock = threading.Lock()

    def _load_identity(self) -> NodeIdentity:
        cert_path = self.keys_dir / self.name / f"{self.name}.crt"
        key_path = self.keys_dir / self.name / f"{self.name}.key"
        if not cert_path.exists() or not key_path.exists():
            raise FileNotFoundError(f"Missing node identity files for {self.name}: {cert_path} and {key_path}")

        cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
        private_key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
        ecdh_private, ecdh_public = self._load_or_create_ecdh_pair()
        return NodeIdentity(
            name=self.name,
            private_key=private_key,
            cert=cert,
            public_key=private_key.public_key(),
            ecdh_private=ecdh_private,
            ecdh_public=ecdh_public,
        )

    def _load_or_create_ecdh_pair(self) -> tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
        node_dir = self.keys_dir / self.name
        node_dir.mkdir(parents=True, exist_ok=True)
        private_path = node_dir / "ecdh_private.pem"
        public_path = node_dir / "ecdh_public.pem"

        if private_path.exists() and public_path.exists():
            private_key = serialization.load_pem_private_key(private_path.read_bytes(), password=None)
            public_key = serialization.load_pem_public_key(public_path.read_bytes())
            return private_key, public_key

        private_key, public_key = generate_ecdh_keypair("SECP256R1")
        private_path.write_bytes(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        public_path.write_bytes(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
        try:
            os.chmod(private_path, 0o600)
            os.chmod(public_path, 0o644)
        except OSError:
            pass
        return private_key, public_key

    def load_peer_ecdh_public(self, peer_name: str) -> ec.EllipticCurvePublicKey:
        pub_path = self.keys_dir / peer_name / "ecdh_public.pem"
        if not pub_path.exists():
            raise FileNotFoundError(f"ECDH public key for peer {peer_name} not found at {pub_path}")
        return serialization.load_pem_public_key(pub_path.read_bytes())

    def encrypt_to_peer(self, peer_public_key: rsa.RSAPublicKey, plaintext: bytes) -> bytes:
        return peer_public_key.encrypt(
            plaintext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    def decrypt_from_peer(self, ciphertext: bytes) -> bytes:
        return self.entity.private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    def derive_session_key(
        self,
        peer_public: ec.EllipticCurvePublicKey,
        salt: bytes = b"tp1-demo",
        peer_name: str | None = None,
        context_label: str = "session",
    ) -> bytes:
        shared_secret = ecdh_shared_secret(self.entity.ecdh_private, peer_public)
        session_peer = peer_name or self.name
        info = derive_session_context(self.name, session_peer, context_label)
        return hkdf_derive_key(shared_secret, salt=salt, info=info)

    def send_encrypted_message(self, peer_name: str, plaintext: str | bytes) -> dict[str, Any]:
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")

        peer_cert = x509.load_pem_x509_certificate((self.keys_dir / peer_name / f"{peer_name}.crt").read_bytes())
        peer_rsa_public = peer_cert.public_key()
        if not isinstance(peer_rsa_public, rsa.RSAPublicKey):
            raise TypeError(f"Peer certificate for {peer_name} does not contain an RSA public key")

        peer_ecdh_public = self.load_peer_ecdh_public(peer_name)
        salt = b"tp1-demo"
        session_context = derive_session_context(self.name, peer_name, "message")
        session_key = self.derive_session_key(peer_ecdh_public, salt=salt, peer_name=peer_name, context_label="message")
        nonce, encrypted, tag = aes_gcm_encrypt(session_key, plaintext, associated_data=session_context)
        wrapped_key = self.encrypt_to_peer(peer_rsa_public, session_key)
        frame = {
            "from": self.name,
            "to": peer_name,
            "salt": base64.b64encode(salt).decode("ascii"),
            "session_context": base64.b64encode(session_context).decode("ascii"),
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "ciphertext": base64.b64encode(encrypted).decode("ascii"),
            "tag": base64.b64encode(tag).decode("ascii"),
            "session_key": base64.b64encode(wrapped_key).decode("ascii"),
        }
        with socket.create_connection(("127.0.0.1", self.port_for(peer_name)), timeout=2) as sock:
            self._send_frame(sock, frame)
            response = self._recv_frame(sock)
        if response != b"ACK":
            raise RuntimeError(f"Peer {peer_name} did not acknowledge the encrypted message")
        return frame

    @staticmethod
    def _send_frame(sock: socket.socket, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        sock.sendall(encoded)

    @staticmethod
    def _recv_frame(sock: socket.socket) -> bytes:
        chunks = []
        while True:
            try:
                chunk = sock.recv(65536)
            except socket.timeout:
                break
            if not chunk:
                break
            chunks.append(chunk)
            if len(chunk) < 65536:
                break
        if not chunks:
            return b""

        data = b"".join(chunks)
        if len(data) >= 4 and data[0] in b"{[\"":
            return data

        try:
            length = int.from_bytes(data[:4], byteorder="big", signed=False)
        except ValueError:
            return data

        if 1 <= length <= len(data) - 4:
            framed = data[4:4 + length]
            if framed:
                return framed
        return data

    @staticmethod
    def port_for(peer_name: str) -> int:
        mapping = {"alice": 5001, "bob": 5002, "carol": 5003, "dave": 5004}
        return mapping[peer_name]

    def send_message(self, socket_obj: socket.socket, peer_name: str, payload: dict[str, Any]) -> None:
        frame = {"from": self.name, "to": peer_name, "payload": payload}
        self._send_frame(socket_obj, frame)

    def receive_message(self, data: bytes) -> dict[str, Any]:
        frame = json.loads(data.decode("utf-8"))
        with self.lock:
            self.incoming_messages.append(frame)
        return frame

    def process_incoming_message(self, data: bytes | dict[str, Any]) -> dict[str, Any]:
        if isinstance(data, bytes):
            frame = json.loads(data.decode("utf-8"))
        else:
            frame = data

        sender = frame.get("from")
        receiver = frame.get("to")
        if sender is None or receiver is None:
            raise ValueError("Malformed message: missing sender or recipient")
        if receiver != self.name:
            return frame

        required = ["nonce", "ciphertext", "tag", "session_key"]
        missing = [field for field in required if field not in frame]
        if missing:
            raise ValueError(f"Malformed encrypted message: missing {', '.join(missing)}")

        try:
            nonce = base64.b64decode(frame["nonce"])
            ciphertext = base64.b64decode(frame["ciphertext"])
            tag = base64.b64decode(frame["tag"])
            wrapped_key = base64.b64decode(frame["session_key"])
            session_context = base64.b64decode(frame.get("session_context", b""))
            salt = base64.b64decode(frame.get("salt", b"tp1-demo")) or b"tp1-demo"
        except (ValueError, TypeError) as exc:
            raise ValueError("Malformed encrypted message: invalid base64 encoding") from exc

        if not session_context:
            session_context = derive_session_context(sender, receiver, "message")

        peer_public = self.load_peer_ecdh_public(sender)
        session_key = self.decrypt_from_peer(wrapped_key)
        expected_key = self.derive_session_key(peer_public, salt=salt, peer_name=sender, context_label="message")
        if session_key != expected_key:
            raise ValueError("Session key does not match the peer's authenticated ECDH state")

        try:
            plaintext = aes_gcm_decrypt(session_key, nonce, ciphertext, tag, associated_data=session_context)
        except ValueError as exc:
            raise ValueError("Message authentication failed: ciphertext or AAD was tampered with") from exc

        result = {
            "from": sender,
            "to": receiver,
            "payload": {"message": plaintext.decode("utf-8")},
            "raw": plaintext.decode("utf-8"),
        }
        with self.lock:
            self.incoming_messages.append(result)
        return result

    def public_certificate(self) -> bytes:
        return self.entity.cert.public_bytes(serialization.Encoding.PEM)

    def verify_peer_certificate(self, peer_cert: x509.Certificate) -> bool:
        try:
            ca_cert = x509.load_pem_x509_certificate(self.root_ca_cert_path.read_bytes())
        except OSError:
            return False

        now = datetime.now(timezone.utc)
        if peer_cert.issuer != ca_cert.subject:
            return False
        if not (peer_cert.not_valid_before_utc <= now <= peer_cert.not_valid_after_utc):
            return False

        try:
            ca_cert.public_key().verify(
                peer_cert.signature,
                peer_cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                peer_cert.signature_hash_algorithm,
            )
            return True
        except Exception:
            return False

    def run_server(self, stop_event: threading.Event) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", self.port))
            server.listen(8)
            server.settimeout(0.5)
            while not stop_event.is_set():
                try:
                    conn, _ = server.accept()
                except socket.timeout:
                    continue
                with conn:
                    try:
                        data = self._recv_frame(conn)
                    except ValueError:
                        conn.sendall(b"ERROR")
                        continue
                    if not data:
                        conn.sendall(b"ERROR")
                        continue
                    try:
                        parsed = json.loads(data.decode("utf-8"))
                    except (TypeError, ValueError):
                        conn.sendall(b"ERROR")
                        continue
                    if not isinstance(parsed, dict):
                        conn.sendall(b"ERROR")
                        continue

                    try:
                        if "session_key" in parsed:
                            self.process_incoming_message(parsed)
                        else:
                            target = parsed.get("to")
                            if target == self.name:
                                with self.lock:
                                    self.incoming_messages.append(parsed)
                            elif target in {"alice": 5001, "bob": 5002, "carol": 5003, "dave": 5004}:
                                with socket.create_connection(("127.0.0.1", self.port_for(target)), timeout=2) as relay:
                                    self._send_frame(relay, parsed)
                                    relay.recv(4)
                        conn.sendall(b"ACK")
                    except Exception:
                        conn.sendall(b"ERROR")


if __name__ == "__main__":
    pass
