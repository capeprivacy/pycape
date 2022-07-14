import pathlib

from pycape.attestation import parse_attestation
from pycape.enclave_encrypt import encrypt


class TestEnclaveEncryption:
    def test_data_encryption(self):
        plaintext = b"private_data"

        fixture_dir = pathlib.Path(__file__).parent / "fixtures"
        with open(fixture_dir / "attestation_example_hpke.bin", "rb") as f:
            attestation = f.read()
        public_key = parse_attestation(attestation)
        _ = encrypt(public_key, plaintext)
