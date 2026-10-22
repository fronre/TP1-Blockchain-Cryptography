from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CA_DIR = PROJECT_ROOT / "ca"
NODES_DIR = PROJECT_ROOT / "nodes"


class CertificateAuthority:
    def __init__(self, ca_dir: Path = CA_DIR, nodes_dir: Path = NODES_DIR):
        self.ca_dir = ca_dir
        self.nodes_dir = nodes_dir
        self.ca_dir.mkdir(parents=True, exist_ok=True)
        self.nodes_dir.mkdir(parents=True, exist_ok=True)

    def create_root_ca(self, common_name: str = "Blockchain TP1 Root CA") -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
        key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "FR"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "My Blockchain Consortium"),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ]
        )
        now = datetime.now(timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=3650))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .add_extension(x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ), critical=True)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(key.public_key()), critical=False)
            .sign(key, hashes.SHA256())
        )
        self.write_pem(self.ca_dir / "ca.key", key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
        self.write_pem(self.ca_dir / "ca.crt", cert.public_bytes(serialization.Encoding.PEM))
        return key, cert

    def create_node_cert(self, node_name: str, email: str = "node@blockchain.local") -> tuple[rsa.RSAPrivateKey, x509.Certificate, x509.CertificateSigningRequest]:
        node_dir = self.nodes_dir / node_name
        node_dir.mkdir(parents=True, exist_ok=True)

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "FR"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "My Blockchain Consortium"),
                x509.NameAttribute(NameOID.COMMON_NAME, node_name),
                x509.NameAttribute(NameOID.EMAIL_ADDRESS, email),
            ]
        )
        csr = (
            x509.CertificateSigningRequestBuilder()
            .subject_name(subject)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(f"{node_name}.local")]),
                critical=False,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=True,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH, x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .sign(private_key, hashes.SHA256())
        )

        ca_key = self.load_private_key(self.ca_dir / "ca.key")
        ca_cert = self.load_certificate(self.ca_dir / "ca.crt")
        cert = (
            x509.CertificateBuilder()
            .subject_name(csr.subject)
            .issuer_name(ca_cert.subject)
            .public_key(csr.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
            .not_valid_after(datetime.now(timezone.utc) + timedelta(days=1095))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(csr.public_key()), critical=False)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_cert.public_key()), critical=False)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=True,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH, x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .sign(ca_key, hashes.SHA256())
        )

        self.write_pem(node_dir / f"{node_name}.key", private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
        self.write_pem(node_dir / f"{node_name}.crt", cert.public_bytes(serialization.Encoding.PEM))
        self.write_pem(node_dir / f"{node_name}.csr", csr.public_bytes(serialization.Encoding.PEM))
        return private_key, cert, csr

    @staticmethod
    def write_pem(path: Path, data: bytes) -> None:
        path.write_bytes(data)

    @staticmethod
    def load_private_key(path: Path):
        return serialization.load_pem_private_key(path.read_bytes(), password=None)

    @staticmethod
    def load_certificate(path: Path):
        return x509.load_pem_x509_certificate(path.read_bytes())

    @staticmethod
    def load_csr(path: Path):
        return x509.load_pem_x509_csr(path.read_bytes())


def generate_project_certificates() -> dict[str, Path]:
    ca = CertificateAuthority()
    ca.create_root_ca()
    for name in ["alice", "bob", "carol", "dave"]:
        ca.create_node_cert(name)
    return {
        "ca_cert": CA_DIR / "ca.crt",
        "ca_key": CA_DIR / "ca.key",
    }


if __name__ == "__main__":
    generate_project_certificates()
