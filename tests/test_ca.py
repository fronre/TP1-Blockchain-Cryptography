from pathlib import Path

from cryptography import x509

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
