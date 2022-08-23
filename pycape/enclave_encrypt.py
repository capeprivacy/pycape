import logging

import hybrid_pke

logger = logging.getLogger("pycape")


class EncryptionContext:
    def __init__(self, public_key: bytes):
        self._hpke = hybrid_pke.default()
        self._encap, self._ctx = self._hpke.setup_sender(public_key, info=b"")

    def seal(self, plain_txt: bytes) -> bytes:
        aad = b""
        cipher_txt = self._ctx.seal(aad, plain_txt)
        return self._encap + cipher_txt
