"""The Cape Python client.

The :class:`Cape` client uses websockets to connect to Cape enclaves that are hosting a
user's deployed functions. Before being able to run functions from the Cape client,
users must have gone through the process of developing a Cape function in Python and
deploying it from the CLI.

**Usage**

::

    cape = Cape(url="wss://enclave.capeprivacy.com")

    cape.connect("9712r5dynf57l1rcns2")

    c1 = cape.invoke(3, 4, use_serdio=True)
    print(c1)  # 5

    c2 = cape.invoke(5, 12, use_serdio=True)
    print(c2)  # 13

    cape.close()  # release the websocket connection

"""
import asyncio
import base64
import contextlib
import hashlib
import io
import json
import logging
import os
import pathlib
import random
import ssl
import zipfile
from typing import Any
from typing import Optional
from typing import Union

import websockets

import serdio
from pycape import _attestation as attest
from pycape import _config as cape_config
from pycape import _enclave_encrypt as enclave_encrypt
from pycape import cape_encrypt
from pycape import function_ref as fref

logging.basicConfig(format="%(message)s")
logger = logging.getLogger("pycape")


class Cape:
    """A websocket client for interacting with enclaves hosting Cape functions.

    This is the main interface for interacting with Cape functions from Python.
    See module-level documentation :mod:`pycape.cape` for usage example.

    Args:
        url: The Cape platform's websocket URL, which is responsible for forwarding
            client requests to the proper enclave instances. If None, tries to load
            value from the ``CAPE_ENCLAVE_HOST`` environment variable. If no such
            variable value is supplied, defaults to ``"wss://enclave.capeprivacy.com"``.
        access_token: Optional string containing a Cape access token generated by the
            Cape CLI during ``cape login``. If None, tries to load the access token from
            a JSON at ``$HOME/.config/cape/auth`` (or OS-equivalent path).
        verbose: Boolean controlling verbose logging for the ``"pycape"`` logger.
            If True, sets log-level to ``DEBUG``.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        access_token: Optional[str] = None,
        verbose: bool = False,
    ):
        self._url = url or cape_config.ENCLAVE_HOST
        if access_token is None:
            config_dir = pathlib.Path(cape_config.LOCAL_CONFIG_DIR)
            cape_auth_path = config_dir / cape_config.LOCAL_AUTH_FILENAME
            access_token = _handle_default_auth(cape_auth_path)
        self._auth_token = access_token
        self._root_cert = None
        self._ctx = None
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop

        if verbose:
            logger.setLevel(logging.DEBUG)

    def close(self):
        """Closes the current enclave connection."""
        self._loop.run_until_complete(self._close())
        self._ctx = None

    def connect(self, function_ref: Union[str, fref.FunctionRef]):
        """Connects to the enclave hosting the function denoted by ``function_ref``.

        Note that this method creates a stateful websocket connection, which is a
        necessary precondition for callers of :meth:`~Cape.invoke`. Care should be taken
        to close the websocket connection with :meth:`~Cape.close` once all invocations
        have finished.

        Args:
            function_ref: A function ID string or :class:`~.function_ref.FunctionRef`
                representing a deployed Cape function.

        Raises:
            RuntimeError: if the websocket response or the enclave attestation doc is
                malformed, or if the enclave fails to return a function checksum
                matching our own.
            Exception: if the enclave threw an error while trying to fulfill the
                connection request.
        """
        function_ref = _convert_to_function_ref(function_ref)
        self._loop.run_until_complete(self._connect(function_ref))

    def deploy(self, function_path) -> fref.FunctionRef:
        """Deploy function to an enclave"""
        function_path = pathlib.Path(function_path)

        return self._loop.run_until_complete(self._deploy(function_path))

    def encrypt(
        self,
        input: bytes,
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
        cape_key = key or self.key(key_path)
        ctxt = cape_encrypt.encrypt(input, cape_key)
        # cape-encrypted ctxt must be b64-encoded and tagged
        ctxt = base64.b64encode(ctxt)
        return b"cape:" + ctxt

    @contextlib.contextmanager
    def function_context(self, function_ref: Union[str, fref.FunctionRef]):
        """Creates a context manager for a given ``function_ref``'s enclave connection.

        Note that this context manager accomplishes the same functionality as
        :meth:`~Cape.connect`, except that it will also automatically
        :meth:`~Cape.close` the connection when exiting the context.

        **Usage** ::

            cape = Cape(url="wss://enclave.capeprivacy.com")

            with cape.function_context("9712r5dynf57l1rcns2"):

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
            yield self.connect(function_ref)
        finally:
            self.close()

    def invoke(
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
        return self._loop.run_until_complete(
            self._invoke(serde_hooks, use_serdio, *args, **kwargs)
        )

    def key(self, key_path: Optional[Union[str, os.PathLike]] = None) -> bytes:
        """Load a Cape key from disk or download and persist an enclave-generated one.

        Args:
            key_path: The path to the Cape key file. If the file already exists, the key
                will be read from disk and returned. Otherwise, a Cape key will be
                requested from the Cape platform and written to this location.
                If None, the default path is ``"$HOME/.config/cape/capekey.pub.der"``,
                or alternatively whatever path is specified by expanding the env
                variables ``CAPE_LOCAL_CONFIG_DIR / CAPE_LOCAL_CAPE_KEY_FILENAME``.

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
        if key_path.exists():
            with open(key_path, "rb") as f:
                cape_key = f.read()
        else:
            cape_key = self._loop.run_until_complete(self._key(key_path))
        return cape_key

    def run(
        self,
        function_ref: Union[str, fref.FunctionRef],
        *args: Any,
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
            function_ref: A function ID string or :class:`~.function_ref.FunctionRef`
                representing a deployed Cape function.
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
        if function_ref.auth_type == fref.FunctionAuthType.AUTH0:
            function_token = self._auth_token
        else:
            function_token = function_ref.token
        fn_endpoint = f"{self._url}/v1/run/{function_ref.id}"

        self._root_cert = self._root_cert or attest.download_root_cert()
        self._ctx = _EnclaveContext(
            endpoint=fn_endpoint,
            auth_protocol=function_ref.auth_protocol,
            auth_token=function_token,
            root_cert=self._root_cert,
        )
        attestation_doc = await self._ctx.bootstrap()

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

    async def _close(self):
        await self._ctx.close()

    async def _deploy(self, function_path):
        zipped_function = _prepare_deployment_folder(function_path)
        checksum = hashlib.sha256()
        checksum.update(zipped_function)

        fn_endpoint = f"{self._url}/v1/deploy"

        self._root_cert = self._root_cert or attest.download_root_cert()
        self._ctx = _EnclaveContext(
            endpoint=fn_endpoint,
            auth_protocol="cape.runtime",
            auth_token=self._auth_token,
            root_cert=self._root_cert,
        )

        await self._ctx.bootstrap()
        await self._ctx.send_func_token_public_key()

        deploy_response = await self._ctx.deploy(zipped_function)
        return fref.FunctionRef(
            id=deploy_response.get("id"), checksum=checksum.hexdigest()
        )

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

        result = await self._ctx.invoke(inputs)

        if use_serdio:
            result = serdio.deserialize(result, decoder=decoder_hook)

        return result

    async def _key(self, key_path: pathlib.Path) -> bytes:
        key_endpoint = f"{self._url}/v1/key"
        auth_protocol = fref.get_auth_protocol(fref.FunctionAuthType.AUTH0)
        self._root_cert = self._root_cert or attest.download_root_cert()
        key_ctx = _EnclaveContext(
            key_endpoint,
            auth_protocol=auth_protocol,
            auth_token=self._auth_token,
            root_cert=self._root_cert,
        )
        attestation_doc = await key_ctx.bootstrap()
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

    async def _run(self, *args, function_ref, serde_hooks, use_serdio, **kwargs):
        await self._connect(function_ref)
        result = await self._invoke(serde_hooks, use_serdio, *args, **kwargs)
        await self._close()
        self._ctx = None
        return result


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
        request = _create_connection_request(nonce, self._auth_token)
        logger.debug("\n> Sending authentication request...")
        await self._websocket.send(request)
        logger.debug("* Waiting for attestation document...")
        msg = await self._websocket.recv()
        logger.debug("< Auth completed. Received attestation document.")
        return _parse_wss_response(msg)

    async def bootstrap(self):
        logger.debug(f"* Dialing {self._endpoint}")
        self._websocket = await websockets.connect(
            self._endpoint,
            ssl=self._ssl_ctx,
            subprotocols=[self._auth_protocol, self._auth_token],
            max_size=None,
        )
        logger.debug("* Websocket connection established")

        auth_response = await self.authenticate()
        attestation_doc = attest.parse_attestation(auth_response, self._root_cert)
        self._public_key = attestation_doc["public_key"]

        return attestation_doc

    async def close(self):
        await self._websocket.close()
        self._public_key = None

    async def invoke(self, inputs: bytes) -> bytes:
        input_ciphertext = enclave_encrypt.encrypt(self._public_key, inputs)

        logger.debug("> Sending encrypted inputs")
        await self._websocket.send(input_ciphertext)
        invoke_response = await self._websocket.recv()
        logger.debug("< Received function results")
        return _parse_wss_response(invoke_response)

    async def deploy(self, inputs: bytes) -> bytes:
        input_ciphertext = enclave_encrypt.encrypt(self._public_key, inputs)
        logger.debug("> Sending encrypted function")

        await self._websocket.send(input_ciphertext)
        deploy_response = await self._websocket.recv()
        logger.debug("< Received function id")
        return _parse_wss_response(deploy_response, inner_msg=False)

    async def send_func_token_public_key(self):
        public_key_pem = _get_function_token_public_key_pem()
        await self._websocket.send(
            _create_function_public_token_request(public_key_pem)
        )


# TODO What should be the length?
def _generate_nonce(length=8):
    """
    Generates a string of digits between 0 and 9 of a given length
    """
    nonce = "".join([str(random.randint(0, 9)) for i in range(length)])
    logger.debug(f"* Generated nonce: {nonce}")
    return nonce


def _create_connection_request(nonce, token):
    """
    Returns a json string with nonce
    """
    # TODO Remove auth token from initial request! Added temporarily
    # because deploy requires it but it's a bug
    request = {"message": {"nonce": nonce, "auth_token": token}}
    return json.dumps(request)


def _parse_wss_response(response, inner_msg=True):
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
    if inner_msg:
        inner_msg = _handle_expected_field(
            response_msg,
            "message",
            fallback_err=(
                "Malformed websocket response contents: missing inner 'message' field."
            ),
        )
        return base64.b64decode(inner_msg)
    else:
        return response_msg


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
    """
    Returns value of a provided key from dictionary, optionally raising
    a custom RuntimeError if it's missing.
    """
    v = dictionary.get(field, None)
    if v is None:
        if fallback_err is not None:
            logger.error(fallback_err)
            raise RuntimeError(fallback_err)
        raise RuntimeError(f"Dictionary {dictionary} missing key {field}.")
    return v


def _convert_to_function_ref(function_ref):
    """
    Returns a PyCape FunctionRef object that represents the Cape function
    """
    if isinstance(function_ref, str):
        return fref.FunctionRef(function_ref)
    elif isinstance(function_ref, fref.FunctionRef):
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


async def _persist_cape_key(cape_key: str, key_path: pathlib.Path):
    key_path.parent.mkdir(parents=True, exist_ok=True)
    with open(key_path, "wb") as f:
        f.write(cape_key)


def _prepare_deployment_folder(folder_path):
    if folder_path.is_dir():
        zipped_function, folder_size = _make_zipfile(folder_path)
    elif zipfile.is_zipfile(folder_path):
        folder_size = _get_zip_size(folder_path)
        with open(folder_path, "rb") as z:
            zipped_function = z.read()
    else:
        raise RuntimeError(
            f"Your deployment path ({folder_path}) should point"
            "to a folder or a zip file containing your function (app.py)"
        )

    if folder_size > cape_config.STORED_FUNCTION_MAX_BYTES:
        raise RuntimeError(
            f"Deployment folder size ({folder_size} bytes) exceeds size "
            "limit of {cape_config.STORED_FUNCTION_MAX_BYTES} bytes"
        )
    return zipped_function


def _make_zipfile(folder_path):
    folder_size = 0
    zipped_function = io.BytesIO()
    with zipfile.ZipFile(zipped_function, "w") as z:
        for folder_name, _, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(folder_name, filename)
                z.write(filepath, filepath)
                folder_size += os.path.getsize(filepath)
    return zipped_function.getvalue(), folder_size


def _get_zip_size(zip_path):
    z = zipfile.ZipFile(zip_path)
    z_size = sum([zinfo.file_size for zinfo in z.filelist])
    return z_size


def _get_function_token_public_key_pem():
    pubic_pem_file = pathlib.Path(cape_config.LOCAL_CONFIG_DIR) / "token.pub.pem"

    if not pubic_pem_file.is_file():
        _ = _generate_rsa_key_pair()

    with open(pubic_pem_file, "r") as f:
        public_key_pem = f.read()

    return public_key_pem


from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def _generate_rsa_key_pair():
    # Generate key pair
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    # Convert private key to PKCS#1
    pem_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    # Convert public key to SubjectPublicKeyInfo
    pem_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    pem_folder = pathlib.Path(cape_config.LOCAL_CONFIG_DIR)
    with open(pem_folder / "token.pem", "wb") as f:
        f.write(pem_private_key)

    with open(pem_folder / "token.pub.pem", "wb") as f:
        f.write(pem_public_key)


def _create_function_public_token_request(public_key_pem):
    return json.dumps({"message": {"function_token_pk": public_key_pem}})
