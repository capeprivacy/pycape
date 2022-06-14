import asyncio
import base64
import json
import random
import ssl

import websockets

from pycape.attestation import parse_attestation
from pycape.enclave_encrypt import encrypt


class Cape:
    def __init__(self, url="wss://cape.run", token="", insecure=False):
        self._url = url
        self._auth_token = token
        self._insecure = insecure

    def run(self, function_id, input):
        return asyncio.run(self._run(function_id, input))

    async def connect(self, function_id):
        endpoint = f"{self._url}/v1/run/{function_id}"

        ctx = ssl.create_default_context()

        if self._insecure:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        async with websockets.connect(endpoint, ssl=ctx) as websocket:
            nonce = _generate_nonce()
            request = _create_request(self._auth_token, nonce)
            await websocket.send(request)

            msg = await websocket.recv()
            attestation_doc = json.loads(msg)
            doc = base64.b64decode(attestation_doc["message"])
            public_key = parse_attestation(doc)

            input_bytes = _convert_input_to_bytes(input)
            ciphertext = encrypt(input_bytes, public_key)

            await websocket.send(ciphertext)

        result = await self.invoke(input)

        await self.close()

        return result

# TODO What should be the length?
def _generate_nonce(length=8):
    return "".join([str(random.randint(0, 9)) for i in range(length)])


def _create_request(token, nonce):
    request = {"auth_token": token, "nonce": nonce}
    return json.dumps(request)


def _convert_input_to_bytes(input):
    if isinstance(input, dict):
        input = json.dumps(input)
    elif isinstance(input, list):
        input = json.dumps(input)
    elif isinstance(input, int):
        input = json.dumps(input)
    elif isinstance(input, float):
        input = json.dumps(input)
    elif isinstance(input, str):
        pass
    else:
        raise ValueError("Is this an error situation?")
    return bytes(input, "utf-8")


def _parse_result(result):
    result = json.loads(result)
    b64data = result["data"]
    data = base64.b64decode(b64data)
    return data
