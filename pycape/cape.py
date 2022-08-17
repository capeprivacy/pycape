"""The Cape Python client.

The Cape client uses websockets to connect to Cape enclaves that are hosting a user's
deployed functions. Users must have gone through the process of developing a Cape
function in Python and deploying it with the CLI, before being able to run it from the
Cape client.

Usage:
    FUNCTION_ID = < given by CLI after `cape deploy` >
    cape = Cape(url="wss://enclave.capeprivacy.com")
    cape.connect(FUNCTION_ID)

    c1 = cape.invoke(3, 4, use_serdio=True)
    print(c1)  # 5

    c2 = cape.invoke(5, 12, use_serdio=True)
    print(c2)  # 13

    cape.close()  # release the websocket connection
"""

import asyncio
import base64
import json
import logging
import os
import pathlib
import random
import ssl

import websockets

import serdio
from pycape import attestation as attest
from pycape import enclave_encrypt
from pycape.function_ref import FunctionRef

_CAPE_CONFIG_PATH = pathlib.Path.home() / ".config" / "cape"
_DISABLE_SSL = os.environ.get("CAPEDEV_DISABLE_SSL", False)

logging.basicConfig(format="%(message)s")
logger = logging.getLogger("pycape")


class Cape:
    """A websocket client for interacting with enclaves hosting Cape functions.

    This is the main interface for interacting with Cape functions from Python.
    See module documentation for usage example.
    """

    def __init__(
        self, url="wss://enclave.capeprivacy.com", access_token=None, verbose=False
    ):
        """Cape client constructor.

        Args:
            url: The Cape platform websocket URL, which is responsible for forwarding
                client requests to the proper enclave instances.
            access_token: Optional string containing a Cape access token generated
                by the Cape CLI during `cape login`. If None, tries to load the access
                token from a JSON at "$HOME/.config/cape/auth" (or OS-equivalent path).
            verbose: Boolean controlling verbose logging for the "pycape" logger.
                If True, sets log-level to DEBUG.
        """
        self._url = url
        if access_token is None:
            cape_auth_path = _CAPE_CONFIG_PATH / "auth"
            access_token = _handle_default_auth(cape_auth_path)
        self._auth_token = access_token
        self._websocket = ""
        self._public_key = ""
        self._root_cert = None
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop

        if verbose:
            logger.setLevel(logging.DEBUG)

    def close(self):
        """Closes the enclave connection."""
        self._loop.run_until_complete(self._close())

    def connect(self, function_ref):
        """Connects to the enclave hosting the function denoted by `function_ref`.

        Note that this method creates a stateful websocket connection, which is a
        necessary precondition for callers of self.invoke. Care should be taken to
        close the websocket connection with self.close() once all invocations have
        finished.

        Args:
            function_ref: A function ID string or FunctionRef representing a deployed
                Cape function. If a FunctionRef, can also include the function hash,
                which  allows the user to verify that the enclave is hosting the same
                function they deployed.

        Raises:
            RuntimeError if the websocket response or the enclave attestation doc is
                malformed, or if the enclave fails to return a function hash matching
                our own.
            Exception if the enclave threw an error while trying to fulfill the
                connection request.
        """
        function_ref = _convert_to_function_ref(function_ref)
        self._loop.run_until_complete(self._connect(function_ref))

    def invoke(self, *args, serde_hooks=None, use_serdio=False, **kwargs):
        """Invokes a function call from the currently connected websocket.

        This method assumes that the client is currently maintaining an open websocket
        connection to an enclave hosting a particular Cape function. Care should be
        taken to ensure that the function_red that spawned the connection is the
        correct one. The connection should be closed with self.close() once the caller
        is finished with their invocations.

        Args:
            *args: Arguments to pass to the connected Cape function. If
                use_serdio=False, we expect a single argument of type `bytes`.
                Otherwise, these arguments should match the positional arguments
                of the undecorated Cape handler, and they will be auto-serialized by
                serdio before being sent in the request.
            serde_hooks: An optional pair of serdio encoder/decoder hooks convertible
                to serdio.SerdeHookBundle. The hooks are necessary if the args / kwargs
                have any custom (non-native) types that can't be handled by vanilla
                msgpack.
            use_serdio: Boolean controlling whether or not the inputs should be
                auto-serialized by serdio.
            kwargs: Keyword arguments to be passed to the connected Cape function.
                These are treated the same way as the `args` are.

        Returns:
            If use_serdio=True, returns the auto-deserialized result of calling the
            connected Cape function on the given args/kwargs.
            If use_serdio=False, returns the output of the Cape function as raw bytes.

        Raises:
            RuntimeError if serialized inputs could not be HPKE-encrypted, or if
                websocket response is malformed.
        """
        if serde_hooks is not None:
            serde_hooks = serdio.bundle_serde_hooks(serde_hooks)
        return self._loop.run_until_complete(
            self._invoke(serde_hooks, use_serdio, *args, **kwargs)
        )

    def run(self, function_ref, *args, serde_hooks=None, use_serdio=False, **kwargs):
        """Single-shot version of connect + invoke.

        This method takes care of establishing a websocket connection via self.connect,
        invoking it via self.invoke, and then finally closing the connection with
        self.close. `run` should be preferred when the caller doesn't need to invoke a
        Cape function more than once.

        Args:
            function_ref: A function ID string or FunctionRef representing a deployed
                Cape function. If a FunctionRef, can also include the function hash,
                which  allows the user to verify that the enclave is hosting the same
                function they deployed.
            *args: Arguments to pass to the connected Cape function. If
                use_serdio=False, we expect a single argument of type `bytes`.
                Otherwise, these arguments should match the positional arguments
                of the undecorated Cape handler, and they will be auto-serialized by
                serdio before being sent in the request.
            serde_hooks: An optional pair of serdio encoder/decoder hooks convertible
                to serdio.SerdeHookBundle. The hooks are necessary if the args / kwargs
                have any custom (non-native) types that can't be handled by vanilla
                msgpack.
            use_serdio: Boolean controlling whether or not the inputs should be
                auto-serialized by serdio.
            kwargs: Keyword arguments to be passed to the connected Cape function.
                These are treated the same way as the `args` are.

        Returns:
            If use_serdio=True, returns the auto-deserialized result of calling the
            connected Cape function on the given args/kwargs.
            If use_serdio=False, returns the output of the Cape function as raw bytes.

        Raises:
            RuntimeError if serialized inputs could not be HPKE-encrypted, or if
                websocket response is malformed.
        """
        function_ref = _convert_to_function_ref(function_ref)
        if serde_hooks is not None:
            serde_hooks = serdio.bundle_serde_hooks(serde_hooks)
        return self._loop.run_until_complete(
            self._run(
                *args,
                function_ref=function_ref,
                serde_hooks=serde_hooks,
                use_serdio=use_serdio,
                **kwargs,
            )
        )

    async def _connect(self, function_ref):
        function_id = function_ref.get_id()
        function_hash = function_ref.get_hash()
        endpoint = f"{self._url}/v1/run/{function_id}"

        ctx = ssl.create_default_context()

        if _DISABLE_SSL:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        logger.debug(f"* Dialing {self._url}")
        self._websocket = await websockets.connect(
            endpoint,
            ssl=ctx,
            subprotocols=["cape.runtime", self._auth_token],
            max_size=None,
        )
        logger.debug("* Websocket connection established")

        nonce = _generate_nonce()
        request = _create_connection_request(nonce)

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
            # Close the connection explicitly before throwing exception
            await self._close()
            raise RuntimeError(
                f"No function hash received from enclave, expected{function_hash}."
            )

        user_data_dict = json.loads(user_data)
        received_hash = user_data_dict.get("func_hash")
        if function_hash is not None:
            # Function hash is hex encoded, we manipulate it to string for comparison
            received_hash = str(base64.b64decode(received_hash).hex())
            if str(function_hash) != str(received_hash):
                # Close the connection explicitly before throwing exception
                await self._close()
                raise RuntimeError(
                    "Returned function hash did not match provided, "
                    f"got: {received_hash}, want: {function_hash}."
                )
        return

    async def _invoke(self, serde_hooks, use_serdio, *args, **kwargs):
        # If multiple args and/or kwargs are supplied to the Cape function through
        # Cape.run or Cape.invoke, before serialization, we pack them
        # into a dictionary with the following keys:
        # {"cape_fn_args": <tuple_args>, "cape_fn_kwargs": <dict_kwargs>}.
        single_input = _maybe_get_single_input(args, kwargs)
        if single_input is not None:
            inputs = single_input
        elif single_input is None and not use_serdio:
            raise ValueError(
                "Expected a single input of type 'bytes' when use_serdio=False.\n"
                "Found:"
                f"\t- args: {args}"
                f"\t- kwargs: {kwargs}"
            )

        if serde_hooks is not None:
            encoder_hook, decoder_hook = serde_hooks.unbundle()
            use_serdio = True
        else:
            encoder_hook, decoder_hook = None, None

        if use_serdio:
            inputs = serdio.serialize(*args, encoder=encoder_hook, **kwargs)

        if not isinstance(inputs, bytes):
            raise TypeError(
                f"The input type is: {type(inputs)}. Provide input as bytes or "
                "set use_serdio=True for PyCape to serialize your input "
                "with Serdio."
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
        await self._connect(function_ref)
        result = await self._invoke(serde_hooks, use_serdio, *args, **kwargs)
        await self._close()
        return result


# TODO What should be the length?
def _generate_nonce(length=8):
    nonce = "".join([str(random.randint(0, 9)) for i in range(length)])
    logger.debug(f"* Generated nonce: {nonce}")
    return nonce


def _create_connection_request(nonce):
    request = {"message": {"nonce": nonce}}
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
            "Malformed websocket response contents: missing inner 'message' field."
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


def _convert_to_function_ref(function_ref):
    if isinstance(function_ref, str):
        return FunctionRef(function_ref)
    elif isinstance(function_ref, FunctionRef):
        return function_ref
    else:
        raise TypeError(
            "`function_ref` arg must be a string function ID, "
            f"or a FunctionRef object, found {type(function_ref)}"
        )


def _maybe_get_single_input(args, kwargs):
    single_arg = len(args) == 1 and len(kwargs) == 0
    single_kwarg = len(args) == 0 and len(kwargs) == 1
    if single_arg:
        return args[0]
    elif single_kwarg:
        return kwargs.items()[0][1]
