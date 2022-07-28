import asyncio
import base64
import io
import json
import logging
import os
import pathlib
import random
import ssl
import zipfile

import requests
import websockets

from pycape import attestation as attest
from pycape import enclave_encrypt
from pycape import io_lifter
from pycape import serde

_CAPE_CONFIG_PATH = pathlib.Path.home() / ".config" / "cape"
_DISABLE_SSL = os.environ.get("CAPEDEV_DISABLE_SSL", False)

logging.basicConfig(format="%(message)s")
logger = logging.getLogger("pycape")


class Cape:
    def __init__(
        self, url="wss://hackathon.capeprivacy.com", access_token=None, verbose=False
    ):
        self._url = url
        if access_token is None:
            cape_auth_path = _CAPE_CONFIG_PATH / "auth"
            access_token = _handle_default_auth(cape_auth_path)
        self._auth_token = access_token
        self._websocket = ""
        self._public_key = ""
        self._loop = asyncio.get_event_loop()

        if verbose:
            logger.setLevel(logging.DEBUG)

    def close(self):
        self._loop.run_until_complete(self._close())

    def connect(self, function_id):
        self._loop.run_until_complete(self._connect(function_id))

    def invoke(self, input, serde_hooks=None, msgpack_serialize=False):
        if serde_hooks is not None:
            serde_hooks = io_lifter.bundle_serde_hooks(serde_hooks)
        return self._loop.run_until_complete(
            self._invoke(
                input, serde_hooks=serde_hooks, msgpack_serialize=msgpack_serialize
            )
        )

    def run(self, function_id, input, serde_hooks=None, msgpack_serialize=False):
        if serde_hooks is not None:
            serde_hooks = io_lifter.bundle_serde_hooks(serde_hooks)
        return asyncio.run(
            self._run(
                function_id,
                input,
                serde_hooks=serde_hooks,
                msgpack_serialize=msgpack_serialize,
            )
        )

    async def _connect(self, function_id):
        endpoint = f"{self._url}/v1/run/{function_id}"

        ctx = ssl.create_default_context()

        if _DISABLE_SSL:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        logger.debug(f"* Dialing {self._url}")
        self._websocket = await websockets.connect(endpoint, ssl=ctx)
        logger.debug("* Websocket connection established")

        nonce = _generate_nonce()
        logger.debug(f"* Generated nonce: {nonce}")
        request = _create_connection_request(self._auth_token, nonce)

        logger.debug("\n> Sending nonce and auth token")
        await self._websocket.send(request)

        logger.debug("* Waiting for attestation document...")
        msg = await self._websocket.recv()
        logger.debug("< Auth completed. received attestation document")
        attestation_doc = _parse_attestation_response(msg)
        doc = base64.b64decode(attestation_doc["message"])
        self._public_key = attest.parse_attestation(doc, download_root_cert())

        return

    async def _invoke(self, input, serde_hooks, msgpack_serialize):
        if serde_hooks is not None:
            encoder_hook, decoder_hook = serde_hooks.unbundle()
            msgpack_serialize = True
        else:
            encoder_hook, decoder_hook = None, None

        if msgpack_serialize:
            input = serde.serialize(input, default=encoder_hook)
        if not isinstance(input, bytes):
            raise TypeError(
                f"The input type is: {type(input)}. Provide input as bytes or "
                "set msgpack_serialize=True for PyCape to serialize your input "
                "with MessagePack."
            )

        logger.debug("\n* Encrypting inputs with Hybrid Public Key Encryption (HPKE)")
        input_ciphertext = enclave_encrypt.encrypt(self._public_key, input)

        logger.debug("\n> Sending encrypted inputs")
        await self._websocket.send(input_ciphertext)
        result = await self._websocket.recv()
        logger.debug("< Received function results")
        result = _parse_websocket_result(result)

        if msgpack_serialize:
            result = serde.deserialize(result, object_hook=decoder_hook)

        return result

    async def _close(self):
        await self._websocket.close()

    async def _run(self, function_id, input, serde_hooks, msgpack_serialize):

        await self._connect(function_id)

        result = await self._invoke(input, serde_hooks, msgpack_serialize)

        await self._close()

        return result


# TODO What should be the length?
def _generate_nonce(length=8):
    return "".join([str(random.randint(0, 9)) for i in range(length)])


def _create_connection_request(token, nonce):
    request = {"message": {"auth_token": token, "nonce": nonce}}
    return json.dumps(request)


def _parse_attestation_response(result):
    result = json.loads(result)
    if "error" in result:
        raise Exception(result["error"])

    return result["message"]


def _parse_websocket_result(result):
    result = json.loads(result)
    if "error" in result:
        raise Exception(result["error"])

    msg = result["message"]
    data = base64.b64decode(msg["message"])
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


def download_root_cert():
    url = "https://aws-nitro-enclaves.amazonaws.com/AWS_NitroEnclaves_Root-G1.zip"
    r = requests.get(url)

    f = zipfile.ZipFile(io.BytesIO(r.content))
    with f.open("root.pem") as p:
        root_cert = p.read()

    return root_cert
