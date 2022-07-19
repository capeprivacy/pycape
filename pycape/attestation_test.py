from pathlib import Path

import cbor2

from pycape.attestation import parse_attestation
from pycape.attestation import verify_signature


class TestAttestation:
    def test_parse_attestation(self):
        fixture_dir = Path(__file__).parent / "fixtures"
        with open(fixture_dir / "attestation_example_hpke.bin", "rb") as f:
            attestation = f.read()
        public_key = parse_attestation(attestation)
        assert len(public_key) == 32

    def test_verify_signature(self):
        fixture_dir = Path(__file__).parent / "fixtures"
        with open(fixture_dir / "attestation_example_hpke.bin", "rb") as f:
            attestation = f.read()

        payload = cbor2.loads(attestation)
        doc = cbor2.loads(payload[2])

        verify_signature(attestation, doc["certificate"])
