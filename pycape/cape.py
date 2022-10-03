"""The Cape Python client.

The :class:`Cape` client uses websockets to connect to Cape enclaves that are hosting a
user's deployed functions. Before being able to run functions from the Cape client,
users must have gone through the process of developing a Cape function in Python and
deploying it from the CLI and generating a function token.

The majority of the :class:`Cape` client interface can be used in either synchronous or
asynchronous contexts via asyncio.

**Usage**

::

    cape = Cape()

    f = FunctionRef.from_json("function.json")
    cape.connect(f)

    c1 = cape.invoke(3, 4, use_serdio=True)
    print(c1)  # 5

    c2 = cape.invoke(5, 12, use_serdio=True)
    print(c2)  # 13

    cape.close()  # release the enclave connection

    # similar invocation, but async
    c3 = asyncio.run(
        cape.run("9712r5dynf57l1rcns2", 8, 15, use_serdio=True)
    )
    print(c3)  # 17

"""
import base64
import json
import logging
import os
import pathlib
import random
import ssl
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import synchronicity
import websockets

import serdio
from pycape import _attestation as attest
from pycape import _config as cape_config
from pycape import _enclave_encrypt as enclave_encrypt
from pycape import cape_encrypt
from pycape import function_ref as fref

logging.basicConfig(format="%(message)s")
_logger = logging.getLogger("pycape")
_synchronizer = synchronicity.Synchronizer(multiwrap_warning=True)


class Cape:
    """A websocket client for interacting with enclaves hosting Cape functions.

    This is the main interface for interacting with Cape functions from Python.
    See module-level documentation :mod:`pycape.cape` for usage example.

    Args:
        url: The Cape platform's websocket URL, which is responsible for forwarding
            client requests to the proper enclave instances. If None, tries to load
            value from the ``CAPE_ENCLAVE_HOST`` environment variable. If no such
            variable value is supplied, defaults to ``"wss://enclave.capeprivacy.com"``.
        verbose: Boolean controlling verbose logging for the ``"pycape"`` logger.
            If True, sets log-level to ``DEBUG``.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        verbose: bool = False,
    ):
        self._url = url or cape_config.ENCLAVE_HOST
        self._root_cert = None
        self._ctx = None

        if verbose:
            _logger.setLevel(logging.DEBUG)

    @_synchronizer
    async def close(self):
        """Closes the current enclave connection."""
        if self._ctx is not None:
            await self._ctx.close()
            self._ctx = None

    @_synchronizer
    async def connect(
        self,
        function_ref: fref.FunctionRef,
        pcrs: Optional[Dict[str, List[str]]] = None,
    ):
        """Connects to the enclave hosting the function denoted by ``function_ref``.

        Note that this method creates a stateful websocket connection, which is a
        necessary precondition for callers of :meth:`~Cape.invoke`. When using the
        default Cape host, the enclave will terminate this websocket connection after
        60s of inactivity. Care should be taken to close the websocket connection with
        :meth:`~Cape.close` once all invocations have finished.

        Args:
            function_ref: A function ID string or :class:`~.function_ref.FunctionRef`
                representing a deployed Cape function.
            pcrs: A dictionary of PCR indexes to a list of potential values.

        Raises:
            RuntimeError: if the websocket response or the enclave attestation doc is
                malformed, or if the enclave fails to return a function checksum
                matching our own.
            Exception: if the enclave threw an error while trying to fulfill the
                connection request.
        """
        function_ref = _check_function_ref(function_ref)
        await self._request_connection(function_ref, pcrs)

    @_synchronizer
    async def encrypt(
        self,
        input: bytes,
        token: str,
        key: Optional[bytes] = None,
        key_path: Optional[Union[str, os.PathLike]] = None,
    ) -> bytes:
        """Encrypts inputs to Cape functions in Cape's encryption format.

        The encrypted value can be used as input to Cape handlers by other callers of
        :meth:`~Cape.invoke` or :meth:`~Cape.run` without giving them plaintext access
        to it. The core encryption functionality uses envelope encryption; the value is
        AES-encrypted with an ephemeral AES key, which is itself encrypted with the Cape
        user's assigned RSA public key. The corresponding RSA private key is only
        accessible from within a Cape enclave, which guarantees secrecy of the encrypted
        value. See the Cape encrypt docs for further detail.

        Args:
            input: Input bytes to encrypt.
            token: A Cape token scoped for retrieving a user's Cape public key.
                See :meth:`~Cape.key` for details.
            key: Optional bytes for the Cape key. If None, will delegate to calling
                :meth:`Cape.key` w/ the given ``key_path`` to retrieve the user's Cape
                key.
            key_path: Optional path to a locally-cached Cape key. Used to call
                :meth:`Cape.key` when an explicit ``key`` argument is not provided.

        Returns:
            Tagged ciphertext representing a base64-encoded Cape encryption of the
            ``input``.

        Raises:
            ValueError: if Cape key is not a properly-formatted RSA public key.
            RuntimeError: if the enclave attestation doc does not contain a Cape key,
                if the websocket response or the attestation doc is malformed.
            Exception: if the enclave threw an error while trying to fulfill the
                connection request.
        """
        cape_key = key or await self.key(token, key_path)
        ctxt = cape_encrypt.encrypt(input, cape_key)
        # cape-encrypted ctxt must be b64-encoded and tagged
        ctxt = base64.b64encode(ctxt)
        return b"cape:" + ctxt

    @_synchronizer
    @_synchronizer.asynccontextmanager
    async def function_context(
        self,
        function_ref: fref.FunctionRef,
        pcrs: Optional[Dict[str, List[str]]] = None,
    ):
        """Creates a context manager for a given ``function_ref``'s enclave connection.

        Note that this context manager accomplishes the same functionality as
        :meth:`~Cape.connect`, except that it will also automatically
        :meth:`~Cape.close` the connection when exiting the context.

        **Usage** ::

            cape = Cape(url="wss://enclave.capeprivacy.com")
            f = FunctionRef.from_json("function.json")

            with cape.function_context(f):

                c1 = cape.invoke(3, 4, use_serdio=True)
                print(c1)  # 5

                c2 = cape.invoke(5, 12, use_serdio=True)
                print(c2)  # 13

            # websocket connection is automatically closed

        Args:
            function_ref: A function ID or :class:`~.function_ref.FunctionRef`
                representing a deployed Cape function.

        Raises:
            RuntimeError: if the websocket response or the enclave attestation doc is
                malformed, or if the enclave fails to return a function checksum
                matching our own.
            Exception: if the enclave threw an error while trying to fulfill the
                connection request.
        """
        try:
            yield await self.connect(function_ref, pcrs)
        finally:
            await self.close()

    @_synchronizer
    async def invoke(
        self, *args: Any, serde_hooks=None, use_serdio: bool = False, **kwargs: Any
    ) -> Any:
        """Invokes a function call from the currently connected websocket.

        This method assumes that the client is currently maintaining an open websocket
        connection to an enclave hosting a particular Cape function. Care should be
        taken to ensure that the function_red that spawned the connection is the
        correct one. The connection should be closed with :meth:`~Cape.close` once the
        caller is finished with its invocations.

        Args:
            *args: Arguments to pass to the connected Cape function. If
                ``use_serdio=False``, we expect a single argument of type ``bytes``.
                Otherwise, these arguments should match the positional arguments
                of the undecorated Cape handler, and they will be auto-serialized by
                Serdio before being sent in the request.
            serde_hooks: An optional pair of serdio encoder/decoder hooks convertible
                to :class:`serdio.SerdeHookBundle`. The hooks are necessary if the
                ``args`` / ``kwargs`` have any user-defined types that can't be handled
                by vanilla Serdio. See :func:`serdio.bundle_serde_hooks` for supported
                types.
            use_serdio: Boolean controlling whether or not the inputs should be
                auto-serialized by serdio.
            kwargs: Keyword arguments to be passed to the connected Cape function.
                These are treated the same way as the ``args`` are.

        Returns:
            If ``use_serdio=True``, returns the auto-deserialized result of calling the
            connected Cape function on the given ``args`` / ``kwargs``.
            If ``use_serdio=False``, returns the output of the Cape function as raw
            bytes.

        Raises:
            RuntimeError: if serialized inputs could not be HPKE-encrypted, or if
                websocket response is malformed.
        """
        if serde_hooks is not None:
            serde_hooks = serdio.bundle_serde_hooks(serde_hooks)
        return await self._request_invocation(serde_hooks, use_serdio, *args, **kwargs)

    @_synchronizer
    async def key(
        self,
        token: str,
        key_path: Optional[Union[str, os.PathLike]] = None,
        pcrs: Optional[Dict[str, List[str]]] = None,
    ) -> bytes:
        """Load a Cape key from disk or download and persist an enclave-generated one.

        Args:
            token: A string representing a Cape authentication token. Usually retrieved
                from a :class:`~.function_ref.FunctionRef` via :attr:`FunctionRef.token`
            key_path: The path to the Cape key file. If the file already exists, the key
                will be read from disk and returned. Otherwise, a Cape key will be
                requested from the Cape platform and written to this location.
                If None, the default path is ``"$HOME/.config/cape/capekey.pub.der"``,
                or alternatively whatever path is specified by expanding the env
                variables ``CAPE_LOCAL_CONFIG_DIR / CAPE_LOCAL_CAPE_KEY_FILENAME``.
            pcrs: A dictionary of PCR indexes to a list of potential values.

        Returns:
            Bytes containing the Cape key. The key is also cached on disk for later
            use.

        Raises:
            RuntimeError: if the enclave attestation doc does not contain a Cape key,
                if the websocket response or the attestation doc is malformed.
            Exception: if the enclave threw an error while trying to fulfill the
                connection request.
        """
        if key_path is None:
            config_dir = pathlib.Path(cape_config.LOCAL_CONFIG_DIR)
            key_path = config_dir / cape_config.LOCAL_CAPE_KEY_FILENAME
        else:
            key_path = pathlib.Path(key_path)
        cape_key = await self._request_key(token, key_path, pcrs=pcrs)
        return cape_key

    @_synchronizer
    async def run(
        self,
        function_ref: fref.FunctionRef,
        *args: Any,
        pcrs: Optional[Dict[str, List[str]]] = None,
        serde_hooks=None,
        use_serdio: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Single-shot version of connect + invoke + close.

        This method takes care of establishing a websocket connection via
        :meth:`~Cape.connect`, invoking it via :meth:`~Cape.invoke`, and then finally
        closing the connection with :meth:`~Cape.close`. This method should be
        preferred when the caller doesn't need to invoke a Cape function more than once.

        Args:
            function_ref: A :class:`~.function_ref.FunctionRef` representing
                a deployed Cape function.
            *args: Arguments to pass to the connected Cape function. If
                ``use_serdio=False``, we expect a single argument of type ``bytes``.
                Otherwise, these arguments should match the positional arguments
                of the undecorated Cape handler, and they will be auto-serialized by
                Serdio before being sent in the request.
            serde_hooks: An optional pair of serdio encoder/decoder hooks convertible
                to :class:`serdio.SerdeHookBundle`. The hooks are necessary if the
                ``args`` / ``kwargs`` have any user-defined types that can't be handled
                by vanilla Serdio. See :func:`serdio.bundle_serde_hooks` for supported
                types.
            use_serdio: Boolean controlling whether or not the inputs should be
                auto-serialized by serdio.
            kwargs: Keyword arguments to be passed to the connected Cape function.
                These are treated the same way as the ``args`` are.

        Returns:
            If ``use_serdio=True``, returns the auto-deserialized result of calling the
            connected Cape function on the given ``args`` / ``kwargs``.
            If ``use_serdio=False``, returns the output of the Cape function as raw
            bytes.

        Raises:
            RuntimeError: if serialized inputs could not be HPKE-encrypted, or if
                websocket response is malformed.
        """
        function_ref = _check_function_ref(function_ref)
        if serde_hooks is not None:
            serde_hooks = serdio.bundle_serde_hooks(serde_hooks)
        async with self.function_context(function_ref, pcrs):
            result = await self.invoke(
                *args, serde_hooks=serde_hooks, use_serdio=use_serdio, **kwargs
            )
        return result

    async def _request_connection(self, function_ref, pcrs=None):
        fn_endpoint = f"{self._url}/v1/run/{function_ref.id}"

        self._root_cert = self._root_cert or attest.download_root_cert()
        self._ctx = _EnclaveContext(
            endpoint=fn_endpoint,
            auth_protocol="cape.function",
            auth_token=function_ref.token,
            root_cert=self._root_cert,
        )
        attestation_doc = await self._ctx.bootstrap(pcrs)

        user_data = attestation_doc.get("user_data")
        checksum = function_ref.checksum
        if checksum is not None and user_data is None:
            # Close the connection explicitly before throwing exception
            await self._ctx.close()
            raise RuntimeError(
                f"No function checksum received from enclave, expected{checksum}."
            )

        user_data_dict = json.loads(user_data)
        received_checksum = user_data_dict.get("func_checksum")
        if checksum is not None:
            # Checksum is hex encoded, we manipulate it to string for comparison
            received_checksum = str(base64.b64decode(received_checksum).hex())
            if str(checksum) != str(received_checksum):
                # Close the connection explicitly before throwing exception
                await self._ctx.close()
                raise RuntimeError(
                    "Returned checksum did not match provided, "
                    f"got: {received_checksum}, want: {checksum}."
                )
        return

    async def _request_invocation(self, serde_hooks, use_serdio, *args, **kwargs):
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

        result = await self._ctx.invoke(inputs)

        if use_serdio:
            result = serdio.deserialize(result, decoder=decoder_hook)

        return result

    async def _request_key(
        self,
        token: str,
        key_path: pathlib.Path,
        pcrs: Optional[Dict[str, List[str]]] = None,
    ) -> bytes:
        key_endpoint = f"{self._url}/v1/key"
        self._root_cert = self._root_cert or attest.download_root_cert()
        key_ctx = _EnclaveContext(
            key_endpoint,
            auth_protocol="cape.function",
            auth_token=token,
            root_cert=self._root_cert,
        )
        attestation_doc = await key_ctx.bootstrap(pcrs)
        await key_ctx.close()  # we have the attestation doc, no longer any need for ctx
        user_data = attestation_doc.get("user_data")
        user_data_dict = json.loads(user_data)
        cape_key = user_data_dict.get("key")
        if cape_key is None:
            raise RuntimeError(
                "Enclave response did not include a Cape key in attestation user data."
            )
        cape_key = base64.b64decode(cape_key)
        await _persist_cape_key(cape_key, key_path)
        return cape_key


class _EnclaveContext:
    """A context managing a connection to a particular enclave instance."""

    def __init__(self, endpoint, auth_protocol, auth_token, root_cert):
        self._endpoint = endpoint
        self._auth_token = auth_token
        self._auth_protocol = auth_protocol
        self._root_cert = root_cert
        ssl_ctx = ssl.create_default_context()
        if cape_config.DEV_DISABLE_SSL:
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
        self._ssl_ctx = ssl_ctx

        # state to be explicitly created/destroyed by callers via bootstrap/close
        self._websocket = None
        self._public_key = None

    async def authenticate(self):
        nonce = _generate_nonce()
        request = _create_connection_request(nonce)
        _logger.debug("\n> Sending authentication request...")
        await self._websocket.send(request)
        _logger.debug("* Waiting for attestation document...")
        msg = await self._websocket.recv()
        _logger.debug("< Auth completed. Received attestation document.")
        return _parse_wss_response(msg)

    async def bootstrap(self, pcrs: Optional[Dict[str, List[str]]] = None):
        _logger.debug(f"* Dialing {self._endpoint}")
        self._websocket = await websockets.connect(
            self._endpoint,
            ssl=self._ssl_ctx,
            subprotocols=[self._auth_protocol, self._auth_token],
            max_size=None,
        )
        _logger.debug("* Websocket connection established")

        auth_response = await self.authenticate()
        attestation_doc = attest.parse_attestation(auth_response, self._root_cert)
        self._public_key = attestation_doc["public_key"]

        if pcrs is not None:
            attest.verify_pcrs(pcrs, attestation_doc)

        return attestation_doc

    async def close(self):
        if self._websocket is not None:
            await self._websocket.close()
            self._websocket = None
        self._public_key = None

    async def invoke(self, inputs: bytes) -> bytes:
        input_ciphertext = enclave_encrypt.encrypt(self._public_key, inputs)

        _logger.debug("> Sending encrypted inputs")
        try:
            await self._websocket.send(input_ciphertext)
        except websockets.exceptions.ConnectionClosedOK:
            await self.close()
            raise RuntimeError(
                "Enclave websocket connection was closed, likely due to timeout error. "
                "Please invoke your function more frequently to keep the connection "
                "alive for more than 60 seconds."
            )

        invoke_response = await self._websocket.recv()
        _logger.debug("< Received function results")

        return _parse_wss_response(invoke_response)


# TODO What should be the length?
def _generate_nonce(length=8):
    """
    Generates a string of digits between 0 and 9 of a given length
    """
    nonce = "".join([str(random.randint(0, 9)) for i in range(length)])
    _logger.debug(f"* Generated nonce: {nonce}")
    return nonce


def _create_connection_request(nonce):
    """
    Returns a json string with nonce
    """
    request = {"message": {"nonce": nonce}}
    return json.dumps(request)


def _parse_wss_response(response):
    """
    Returns the inner message field received in a WebSocket message from enclave
    """
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


def _handle_expected_field(dictionary, field, *, fallback_err=None):
    """
    Returns value of a provided key from dictionary, optionally raising
    a custom RuntimeError if it's missing.
    """
    v = dictionary.get(field, None)
    if v is None:
        if fallback_err is not None:
            _logger.error(fallback_err)
            raise RuntimeError(fallback_err)
        raise RuntimeError(f"Dictionary {dictionary} missing key {field}.")
    return v


def _check_function_ref(function_ref):
    """
    Check if the FunctionRef object contains a function ID and token.
    """
    if isinstance(function_ref, fref.FunctionRef):
        if function_ref.id is None:
            raise ValueError("The function ID in the provided FunctionRef is empty.")

        if function_ref.token is None:
            raise ValueError("The function token in the provided FunctionRef is empty.")

        return function_ref
    else:
        raise TypeError(
            "`function_ref` arg must be a FunctionRef object, "
            f" found {type(function_ref)}."
        )


def _maybe_get_single_input(args, kwargs):
    single_arg = len(args) == 1 and len(kwargs) == 0
    single_kwarg = len(args) == 0 and len(kwargs) == 1
    if single_arg:
        return args[0]
    elif single_kwarg:
        return kwargs.items()[0][1]


async def _persist_cape_key(cape_key: str, key_path: pathlib.Path):
    key_path.parent.mkdir(parents=True, exist_ok=True)
    with open(key_path, "wb") as f:
        f.write(cape_key)
