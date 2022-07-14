from pathlib import Path

from pycape.attestation import parse_attestation


class TestAttestation:
    def test_parse_attestation(self):
        fixture_dir = Path(__file__).parent / "fixtures"
        with open(fixture_dir / "attestation_example_hpke.bin", "rb") as f:
            attestation = f.read()
        public_key = parse_attestation(attestation)
        assert len(public_key) == 32
