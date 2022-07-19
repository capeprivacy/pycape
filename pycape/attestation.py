import cbor2
from cose.keys import EC2Key
from cose.keys.curves import P384
from cose.messages import Sign1Message
from Crypto.Util.number import long_to_bytes
from OpenSSL import crypto


def parse_attestation(attestation):
    # TODO verifies the PCRs
    payload = cbor2.loads(attestation)
    doc = cbor2.loads(payload[2])

    if not verify_signature(attestation, doc["certificate"]):
        raise ValueError("wrong signature")

    public_key = doc.get("public_key")
    if public_key is None:
        raise ValueError("The public key is missing in the attestation document.")

    return public_key


def verify_signature(payload, cert) -> bool:
    cert = crypto.load_certificate(crypto.FILETYPE_ASN1, cert)

    # Get the key parameters from the cert public key
    cert_public_numbers = cert.get_pubkey().to_cryptography_key().public_numbers()
    x = cert_public_numbers.x
    y = cert_public_numbers.y

    x = long_to_bytes(x)
    y = long_to_bytes(y)

    # Create the EC2 key from public key parameters
    key = EC2Key(x=x, y=y, crv=P384)

    cose_obj = cbor2.loads(payload)
    msg = Sign1Message.from_cose_obj(cose_obj, allow_unknown_attributes=True)
    msg.key = key

    # Verify the signature using the EC2 key
    return msg.verify_signature()
