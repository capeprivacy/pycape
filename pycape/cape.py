import asyncio
import base64
import json
import pathlib
import random
import ssl

import websockets

from pycape.attestation import parse_attestation
from pycape.enclave_encrypt import encrypt

_CAPE_CONFIG_PATH = pathlib.Path.home() / ".config" / "cape"


class Cape:
    def __init__(self, url="wss://cape.run", access_token=None, insecure=False):
        self._url = url
        if access_token is None:
            cape_auth_path = _CAPE_CONFIG_PATH / "auth"
            access_token = _handle_default_auth(cape_auth_path)
        self._auth_token = access_token
        self._insecure = insecure
        self._websocket = ""
        self._public_key = ""
        self._loop = asyncio.get_event_loop()

    def run(self, function_id, input):
        return asyncio.run(self._run(function_id, input))

    def connect(self, function_id):
        self._loop.run_until_complete(self._connect(function_id))

    def invoke(self, input):
        return self._loop.run_until_complete(self._invoke(input))

    def close(self):
        self._loop.run_until_complete(self._close())

    async def _connect(self, function_id):
        endpoint = f"{self._url}/v1/run/{function_id}"

        ctx = ssl.create_default_context()

        if self._insecure:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        self._websocket = await websockets.connect(endpoint, ssl=ctx)

        nonce = _generate_nonce()
        request = _create_request(self._auth_token, nonce)

        await self._websocket.send(request)

        msg = await self._websocket.recv()
        attestation_doc = json.loads(msg)
        doc = base64.b64decode(attestation_doc["message"])
        self._public_key = parse_attestation(doc)

        return

    async def _invoke(self, input):
        input_bytes = _convert_input_to_bytes(input)
        ciphertext = encrypt(input_bytes, self._public_key)

        await self._websocket.send(ciphertext)
        result = await self._websocket.recv()
        result = _parse_result(result)

        return result

    async def _close(self):
        await self._websocket.close()

    async def _run(self, function_id, input):

        await self._connect(function_id)

        result = await self._invoke(input)

        await self._close()

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
    elif isinstance(input, bytes):
        return input
    else:
        raise ValueError(f"Run doesn't support input of type: {type(input)}")
    return bytes(input, "utf-8")


def _parse_result(result):
    result = json.loads(result)
    b64data = result["message"]
    data = base64.b64decode(b64data)
    return data


def _handle_default_auth(auth_path: pathlib.Path):
    if not auth_path.exists():
        raise ValueError(
            f"No Cape auth file found at {str(auth_path)}. Have you authenticated "
            "this device with the Cape CLI's `login` command?"
        )
    with open(auth_path, "r") as auth_file:
        auth_dict = json.load(auth_file)
    access_token = auth_dict.get("access_token", None)
    if access_token is None:
        raise ValueError(
            "Malformed auth file found: missing 'access_token' JSON field."
        )
    return access_token
