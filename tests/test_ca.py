from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from blockchain_tp1.ca import CertificateAuthority


def test_ca_and_node_certificates_are_created():
    authority = CertificateAuthority()
    ca_key, ca_cert = authority.create_root_ca("Blockchain TP1 Root CA")
    assert ca_key is not None
    assert ca_cert.subject.rfc4514_string().find("Blockchain TP1 Root CA") >= 0

    for node_name in ["alice", "bob", "carol", "dave"]:
        private_key, cert, csr = authority.create_node_cert(node_name, f"{node_name}@blockchain.local")
        assert private_key is not None
        assert cert.subject.rfc4514_string().find(node_name) >= 0
        assert csr.subject.rfc4514_string().find(node_name) >= 0

        cert_path = Path("nodes") / node_name / f"{node_name}.crt"
        assert cert_path.exists()


def test_node_certificate_validates_against_root_ca_and_rejects_expired_cert():
    authority = CertificateAuthority()
    authority.create_root_ca("Root CA")
    for name in ["alice", "bob"]:
        authority.create_node_cert(name)

    ca_cert = authority.load_certificate(authority.ca_dir / "ca.crt")
    node_cert = authority.load_certificate(authority.nodes_dir / "alice" / "alice.crt")
    assert node_cert.issuer == ca_cert.subject
    assert node_cert.not_valid_before_utc <= datetime.now(timezone.utc) <= node_cert.not_valid_after_utc

    builder = (
        x509.CertificateBuilder()
        .subject_name(node_cert.subject)
        .issuer_name(ca_cert.subject)
        .public_key(node_cert.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=30))
        .not_valid_after(datetime.now(timezone.utc) - timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(node_cert.public_key()), critical=False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_cert.public_key()), critical=False)
        .add_extension(x509.KeyUsage(digital_signature=True, key_encipherment=True, key_cert_sign=False, crl_sign=False, content_commitment=False, data_encipherment=False, key_agreement=False, encipher_only=False, decipher_only=False), critical=True)
    )
    expired = builder.sign(authority.load_private_key(authority.ca_dir / "ca.key"), hashes.SHA256())
    assert expired.not_valid_after_utc < datetime.now(timezone.utc)
