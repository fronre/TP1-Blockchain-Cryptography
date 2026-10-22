from __future__ import annotations

import base64
import json
import socket
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, ec

from .crypto import aes_gcm_decrypt, aes_gcm_encrypt, ecdh_shared_secret, hkdf_derive_key


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
        cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
        private_key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
        ecdh_private, ecdh_public = self._generate_ecdh_pair()
        self._save_ecdh_public(ecdh_public)
        return NodeIdentity(
            name=self.name,
            private_key=private_key,
            cert=cert,
            public_key=private_key.public_key(),
            ecdh_private=ecdh_private,
            ecdh_public=ecdh_public,
        )

    def _save_ecdh_public(self, ecdh_public: ec.EllipticCurvePublicKey) -> None:
        self.keys_dir.joinpath(self.name).mkdir(parents=True, exist_ok=True)
        pub_path = self.keys_dir / self.name / "ecdh_public.pem"
        pub_path.write_bytes(ecdh_public.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ))

    def _generate_ecdh_pair(self) -> tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
        private_key = ec.generate_private_key(ec.SECP256R1())
        return private_key, private_key.public_key()

    def load_peer_ecdh_public(self, peer_name: str) -> ec.EllipticCurvePublicKey:
        key_bytes = (self.keys_dir / peer_name / "ecdh_public.pem").read_bytes()
        return serialization.load_pem_public_key(key_bytes)

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

    def derive_session_key(self, peer_public: ec.EllipticCurvePublicKey, salt: bytes = b"tp1-session") -> bytes:
        shared_secret = ecdh_shared_secret(self.entity.ecdh_private, peer_public)
        return hkdf_derive_key(shared_secret, salt=salt, info=f"session:{self.name}".encode())

    def send_encrypted_message(self, peer_name: str, plaintext: str | bytes) -> dict[str, Any]:
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")

        peer_cert = x509.load_pem_x509_certificate((self.keys_dir / peer_name / f"{peer_name}.crt").read_bytes())
        peer_rsa_public = peer_cert.public_key()
        peer_ecdh_public = self.load_peer_ecdh_public(peer_name)
        session_key = self.derive_session_key(peer_ecdh_public, salt=b"tp1-demo")
        nonce, encrypted, tag = aes_gcm_encrypt(session_key, plaintext, associated_data=f"{self.name}->{peer_name}".encode())
        wrapped_key = self.encrypt_to_peer(peer_rsa_public, session_key)
        frame = {
            "from": self.name,
            "to": peer_name,
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "ciphertext": base64.b64encode(encrypted).decode("ascii"),
            "tag": base64.b64encode(tag).decode("ascii"),
            "session_key": base64.b64encode(wrapped_key).decode("ascii"),
        }
        with socket.create_connection(("127.0.0.1", self.port_for(peer_name)), timeout=2) as sock:
            sock.sendall(json.dumps(frame).encode("utf-8"))
            ack = sock.recv(1024)
        return frame

    @staticmethod
    def port_for(peer_name: str) -> int:
        mapping = {"alice": 5001, "bob": 5002, "carol": 5003, "dave": 5004}
        return mapping[peer_name]

    def send_message(self, socket_obj: socket.socket, peer_name: str, payload: dict[str, Any]) -> None:
        frame = {"from": self.name, "to": peer_name, "payload": payload}
        socket_obj.sendall(json.dumps(frame).encode("utf-8"))

    def receive_message(self, data: bytes) -> dict[str, Any]:
        frame = json.loads(data.decode("utf-8"))
        with self.lock:
            self.incoming_messages.append(frame)
        return frame

    def process_incoming_message(self, data: bytes) -> dict[str, Any]:
        frame = json.loads(data.decode("utf-8"))
        sender = frame["from"]
        receiver = frame["to"]
        if receiver != self.name:
            return frame
        nonce = base64.b64decode(frame["nonce"])
        ciphertext = base64.b64decode(frame["ciphertext"])
        tag = base64.b64decode(frame["tag"])
        wrapped_key = base64.b64decode(frame["session_key"])
        session_key = self.decrypt_from_peer(wrapped_key)
        plaintext = aes_gcm_decrypt(session_key, nonce, ciphertext, tag, associated_data=f"{sender}->{receiver}".encode())
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
        ca_cert = x509.load_pem_x509_certificate(self.root_ca_cert_path.read_bytes())
        public_key = ca_cert.public_key()
        try:
            public_key.verify(
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
            server.listen(5)
            server.settimeout(0.5)
            while not stop_event.is_set():
                try:
                    conn, _ = server.accept()
                except socket.timeout:
                    continue
                with conn:
                    data = conn.recv(65536)
                    if not data:
                        continue
                    try:
                        parsed = json.loads(data.decode("utf-8"))
                    except Exception:
                        parsed = None
                    if parsed is None:
                        continue
                    if "session_key" in parsed:
                        result = self.process_incoming_message(data)
                        if result:
                            self.incoming_messages.append(result)
                    else:
                        target = parsed.get("to")
                        if target == self.name:
                            with self.lock:
                                self.incoming_messages.append(parsed)
                        elif target in {"alice": 5001, "bob": 5002, "carol": 5003, "dave": 5004}:
                            with socket.create_connection(("127.0.0.1", self.port_for(target)), timeout=2) as relay:
                                relay.sendall(data)
                                relay.recv(1024)
                    conn.sendall(b"ACK")


if __name__ == "__main__":
    pass
