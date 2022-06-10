import asyncio
import base64
import json
import random

import websockets

from pycape.attestation import parse_attestation
from pycape.enclave_encrypt import encrypt


class Cape:
    def __init__(self):
        self._url = "ws://localhost:8765"
        # self._url = "wss://cape.run"
        self._auth_token = "not_implemented"

    def run(self, function_id, input):
        return asyncio.run(self._run(function_id, input))

    async def _run(self, function_id, input):
        endpoint = f"{self._url}/v1/run/{function_id}"

        async with websockets.connect(endpoint) as websocket:

            nonce = _generate_nonce()
            request = _create_request(self._auth_token, nonce)
            await websocket.send(request)

            attestation = await websocket.recv()
            public_key = parse_attestation(attestation)

            input_bytes = _convert_input_to_bytes(input)
            ciphertext = encrypt(public_key, input_bytes)
            await websocket.send(ciphertext)

            result = await websocket.recv()
            result = _parse_result(result)

            return result


# TODO What should be the lenght?
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
    b64data = result["results"]["data"]
    data = base64.b64decode(b64data)
    b64stderr = result["results"]["stderr"]
    stderr = base64.b64decode(b64stderr)
    print("stderr", stderr)
    return data
