import cbor2


def parse_attestation(attestation):
    # TODO verifies that the document was signed by a valid enclave
    # TODO verifies the PCRs
    payload = cbor2.loads(attestation)
    doc = cbor2.loads(payload[2])

    public_key = doc.get("public_key")
    if public_key is None:
        raise ValueError("The public key is missing in the attestation document.")

    return public_key
