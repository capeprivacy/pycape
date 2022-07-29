import asyncio
import base64
import json
import logging
import os
import pathlib
import random
import ssl
from functools import wraps

import websockets

import serdio
from pycape import attestation as attest
from pycape import enclave_encrypt
from serdio import func_utils as serdio_utils

from .function_ref import FunctionRef

_CAPE_CONFIG_PATH = pathlib.Path.home() / ".config" / "cape"
_DISABLE_SSL = os.environ.get("CAPEDEV_DISABLE_SSL", False)

logging.basicConfig(format="%(message)s")
logger = logging.getLogger("pycape")


def check_run(method):
    """
    check_run turns the positional arguments into function_ref if types match
    """

    @wraps(method)
    def new_method(*args, **kwargs):
        # take the first non named argument as function id and construct function_ref
        if len(args) >= 2:
            # ignore self
            function_id = args[1]
            if not isinstance(function_id, str):
                raise ValueError(
                    f"Expected function_id to be string, got {type(function_id)}"
                )
            if "function_ref" in kwargs:
                raise ValueError(
                    f"Invalid positional argument {function_id} provide, "
                    "function_ref was also provided"
                )
            kwargs["function_ref"] = FunctionRef(function_id=function_id)
            args = list(args[0:1]) + list(args[2:])
        if isinstance(kwargs["function_ref"], str):
            raise ValueError("Expected input to be FunctionRef, but got string.")
        return method(*args, **kwargs)

    return new_method


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
        self._root_cert = None
        self._loop = asyncio.get_event_loop()

        if verbose:
            logger.setLevel(logging.DEBUG)

    def close(self):
        self._loop.run_until_complete(self._close())

    def connect(self, function_id, function_hash=None):
        self._loop.run_until_complete(
            self._connect(function_id, function_hash=function_hash)
        )

    def invoke(self, *args, serde_hooks=None, use_serdio=False, **kwargs):
        if serde_hooks is not None:
            serde_hooks = serdio.bundle_serde_hooks(serde_hooks)
        return self._loop.run_until_complete(
            self._invoke(serde_hooks, use_serdio, *args, **kwargs)
        )

    def run(self, function_ref, *args, serde_hooks=None, use_serdio=False, **kwargs):
        if serde_hooks is not None:
            serde_hooks = serdio.bundle_serde_hooks(serde_hooks)
        return asyncio.run(
            self._run(
                *args,
                function_ref,
                serde_hooks=serde_hooks,
                use_serdio=use_serdio,
                **kwargs,
            )
        )

    async def _connect(self, function_id, function_hash):
        endpoint = f"{self._url}/v1/run/{function_id}"

        ctx = ssl.create_default_context()

        if _DISABLE_SSL:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        logger.debug(f"* Dialing {self._url}")
        self._websocket = await websockets.connect(endpoint, ssl=ctx)
        logger.debug("* Websocket connection established")

        nonce = _generate_nonce()
        request = _create_connection_request(self._auth_token, nonce)

        logger.debug("\n> Sending auth request...")
        await self._websocket.send(request)

        logger.debug("* Waiting for attestation document...")
        msg = await self._websocket.recv()
        logger.debug("< Auth completed. Received attestation document.")
        attestation_doc = _parse_wss_response(msg)
        self._root_cert = self._root_cert or attest.download_root_cert()
        self._public_key, user_data = attest.parse_attestation(
            attestation_doc, self._root_cert
        )
        if function_hash is not None and user_data is None:
            raise ValueError(
                f"No function hash received from enclave, expected{function_hash}."
            )

        user_data_dict = json.loads(user_data)
        received_hash = user_data_dict.get("func_hash")
        if function_hash is not None:
            # Function hash is hex encoded, we manipulate it to string for comparison.
            received_hash = str(base64.b64decode(received_hash).hex())
            if str(function_hash) != str(received_hash):
                raise ValueError(
                    f"Returned function hash did not match provided, "
                    f"got: {received_hash}, want: {function_hash}."
                )
        return

    async def _invoke(self, serde_hooks, use_serdio, *args, **kwargs):
        # If multiple args and/or kwargs are supplied to the Cape function through
        # Cape.run or Cape.invoke, before serialization, we pack them
        # into a dictionary with the following keys:
        # {"cape_fn_args": <tuple_args>, "cape_fn_kwargs": <dict_kwargs>}.
        inputs = serdio_utils.pack_function_args_kwargs(args, kwargs)

        if serde_hooks is not None:
            encoder_hook, decoder_hook = serde_hooks.unbundle()
            use_serdio = True
        else:
            encoder_hook, decoder_hook = None, None

        if use_serdio:
            inputs = serdio.serialize(inputs, encoder=encoder_hook)
        if not isinstance(inputs, bytes):
            raise TypeError(
                f"The input type is: {type(inputs)}. Provide input as bytes or "
                "set use_serdio=True for PyCape to serialize your input "
                "with MessagePack."
            )

        input_ciphertext = enclave_encrypt.encrypt(self._public_key, inputs)

        logger.debug("> Sending encrypted inputs")
        await self._websocket.send(input_ciphertext)
        response = await self._websocket.recv()
        logger.debug("< Received function results")
        result = _parse_wss_response(response)

        if use_serdio:
            result = serdio.deserialize(result, decoder=decoder_hook)

        return result

    async def _close(self):
        await self._websocket.close()

    async def _run(self, *args, function_ref, serde_hooks, use_serdio, **kwargs):
        result = await self._invoke(serde_hooks, use_serdio, *args, **kwargs)

        await self._close()

        return result


# TODO What should be the length?
def _generate_nonce(length=8):
    nonce = "".join([str(random.randint(0, 9)) for i in range(length)])
    logger.debug(f"* Generated nonce: {nonce}")
    return nonce


def _create_connection_request(token, nonce):
    request = {"message": {"auth_token": token, "nonce": nonce}}
    return json.dumps(request)


def _parse_wss_response(response):
    response = json.loads(response)
    if "error" in response:
        raise Exception(response["error"])
    response_msg = _handle_expected_field(
        response,
        "message",
        fallback_err="Missing 'message' field in websocket response.",
    )
    inner_msg = _handle_expected_field(
        response_msg,
        "message",
        fallback_err=(
            "Malformed websocket response contents: missing inner " "'message' field."
        ),
    )
    return base64.b64decode(inner_msg)


def _handle_default_auth(auth_path: pathlib.Path):
    if not auth_path.exists():
        raise ValueError(
            f"No Cape auth file found at {str(auth_path)}. Have you authenticated "
            "this device with the Cape CLI's `login` command?"
        )
    with open(auth_path, "r") as auth_file:
        auth_dict = json.load(auth_file)
    access_token = _handle_expected_field(
        auth_dict,
        "access_token",
        fallback_err="Malformed auth file found: missing 'access_token' JSON field.",
    )
    return access_token


def _handle_expected_field(dictionary, field, *, fallback_err=None):
    v = dictionary.get(field, None)
    if v is None:
        if fallback_err is not None:
            logger.error(fallback_err)
            raise RuntimeError(fallback_err)
        raise RuntimeError(f"Dictionary {dictionary} missing key {field}.")
    return v
