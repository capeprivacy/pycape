import base64
import logging
import os
import pathlib
import urllib
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import synchronicity
from pydantic import BaseModel
from websockets import client

from pycape import _attestation as attest
from pycape import _config as cape_config
from pycape import token as tkn
from pycape.llms import crypto

logging.basicConfig(format="%(message)s")
_logger = logging.getLogger("pycape")
_synchronizer = synchronicity.Synchronizer(multiwrap_warning=True)


@_synchronizer.create_blocking
class Cape:
    """A websocket client for interacting with LLMs.

    Args:
        url: The Cape platform's websocket URL, which is responsible for forwarding
            client requests to the proper enclave instances. If None, tries to load
            value from the ``CAPE_ENCLAVE_HOST`` environment variable. If no such
            variable value is supplied, defaults to ``"https://app.capeprivacy.com"``.
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

    async def close(self):
        """Closes the current enclave connection."""
        if self._ctx is not None:
            await self._ctx.close()
            self._ctx = None

    def token(self, token: Union[str, os.PathLike, tkn.Token]) -> tkn.Token:
        """Create or load a :class:`~token.Token`.

        Args:
            token: Filepath to a token file, or the raw token string itself.

        Returns:
            A :class:`~token.Token` that can be used to access users' deployed Cape
            functions.

        Raises:
            TypeError: if the ``token`` argument type is unrecognized.
        """
        token_out = None
        if isinstance(token, pathlib.Path):
            tokenfile = token
            return tkn.Token.from_disk(tokenfile)

        if isinstance(token, str):
            # str could be a filename
            if len(token) <= 255:
                token_as_path = pathlib.Path(token)
                token_out = _try_load_token_file(token_as_path)
            return token_out or tkn.Token(token)

        if isinstance(token, tkn.Token):
            return token

        raise TypeError(f"Expected token to be PathLike or str, found {type(token)}")

    async def completions(
        self,
        prompt: str,
        token: str,
        stream=True,
        model="llama",
        pcrs=None,
    ):
        await self._connect("/v1/cape/ws/completions", token, pcrs=pcrs)

        aes_key = os.urandom(32)
        user_key = base64.b64encode(aes_key).decode()

        data = crypto.envelope_encrypt(
            self.ctx.public_key,
            {"request": {"prompt": prompt, "stream": stream}, "user_key": user_key},
        )
        data = base64.b64encode(data).decode()

        msg = WSMessage(
            msg_type=WSMessageType.COMPLETIONS_REQUEST,
            data=data,
        ).model_dump_json()

        await self.ctx.websocket.send(msg)

        async for msg in self.ctx.websocket:
            msg = WSMessage.model_validate_json(msg)
            if msg.msg_type != WSMessageType.STREAM_CHUNK:
                raise Exception(
                    f"expected {WSMessageType.STREAM_CHUNK} not {msg.msg_type}"
                )

            dec = crypto.aes_decrypt(
                base64.b64decode(msg.data["data"].encode()), aes_key
            )

            content = dec.decode()
            yield content
            if "DONE" in content:
                await self.ctx.close()

    async def chat_completions(
        self,
        messages: Union[str, List[Dict[str, Any]]],
        token: str,
        stream=True,
        model="llama",
        pcrs=None,
    ):
        await self._connect("/v1/cape/ws/chat/completions", token, pcrs=pcrs)

        aes_key = os.urandom(32)
        user_key = base64.b64encode(aes_key).decode()

        data = crypto.envelope_encrypt(
            self.ctx.public_key,
            {"request": {"messages": messages, "stream": stream}, "user_key": user_key},
        )
        data = base64.b64encode(data).decode()

        msg = WSMessage(
            msg_type=WSMessageType.CHAT_COMPLETIONS_REQUEST,
            data=data,
        ).model_dump_json()

        await self.ctx.websocket.send(msg)

        async for msg in self.ctx.websocket:
            msg = WSMessage.model_validate_json(msg)
            if msg.msg_type != WSMessageType.STREAM_CHUNK:
                raise Exception(
                    f"expected {WSMessageType.STREAM_CHUNK} not {msg.msg_type}"
                )

            dec = crypto.aes_decrypt(
                base64.b64decode(msg.data["data"].encode()), aes_key
            )

            content = dec.decode()
            yield content
            if "DONE" in content:
                await self.ctx.close()

    @property
    def ctx(self):
        if self._ctx is None:
            raise Exception("must call _connect first")

        return self._ctx

    async def _connect(self, endpoint, token, pcrs=None):
        endpoint = self._url + endpoint
        self._root_cert = self._root_cert or attest.download_root_cert()
        self._ctx = _Context(
            endpoint=endpoint,
            auth_token=token.raw,
            root_cert=self._root_cert,
        )
        attestation_doc = await self._ctx.bootstrap(pcrs)

        return attestation_doc


class WSMessageType(str, Enum):
    NONCE = "nonce"
    ATTESTATION = "attestation"
    STREAM_CHUNK = "stream_chunk"
    CHAT_COMPLETIONS_REQUEST = "chat_completion_request"
    COMPLETIONS_REQUEST = "completions_request"


class WSMessage(BaseModel):
    msg_type: WSMessageType
    data: Any


class _Context:
    """A context managing a connection to a particular enclave instance."""

    def __init__(self, endpoint: str, auth_token: str, root_cert: str):
        self._endpoint = _transform_url(endpoint)
        self._auth_token = auth_token
        self._root_cert = root_cert

        # state to be explicitly created/destroyed by callers via bootstrap/close
        self._websocket = None
        self._public_key: Optional[bytes] = None

    async def bootstrap(self, pcrs: Optional[Dict[str, List[str]]] = None):
        _logger.debug(f"* Dialing {self._endpoint}")
        self._websocket = await client.connect(
            self._endpoint,
            extra_headers={"Authorization": f"Bearer {self._auth_token}"},
            max_size=None,
        )
        _logger.debug("* Websocket connection established")

        _logger.debug("* Sending nonce...")

        nonce = os.urandom(12)
        nonce_msg = WSMessage(
            msg_type=WSMessageType.NONCE,
            data={"nonce": base64.b64encode(nonce).decode()},
        )
        await self._websocket.send(nonce_msg.model_dump_json())

        _logger.debug("* Waiting for attestation document...")
        msg = await self._websocket.recv()
        msg = WSMessage.model_validate_json(msg)
        if msg.msg_type != WSMessageType.ATTESTATION:
            raise Exception(f"expected {WSMessageType.ATTESTATION} not {msg.msg_type}")

        if "attestation_document" in msg.data:
            doc = base64.b64decode(msg.data["attestation_document"].encode())
            attestation_doc = attest.parse_attestation(
                doc, self._root_cert, nonce=nonce
            )
            self._public_key = attestation_doc["public_key"]

            if pcrs is not None:
                attest.verify_pcrs(pcrs, attestation_doc)

            return attestation_doc

        self._public_key = msg.data["public_key"].encode()

    @property
    def websocket(self) -> client.WebSocketClientProtocol:
        if self._websocket is None:
            raise Exception("must call bootstrap first")

        return self._websocket

    @property
    def public_key(self) -> bytes:
        if self._public_key is None:
            raise Exception("must call bootstrap first")

        return self._public_key

    async def close(self):
        if self._websocket is not None:
            await self._websocket.close()
            self._websocket = None
        self._public_key = None


def _transform_url(url):
    url = urllib.parse.urlparse(url)
    if url.scheme == "https":
        return url.geturl().replace("https://", "wss://")
    elif url.scheme == "http":
        return url.geturl().replace("http://", "ws://")
    return url.geturl()


def _try_load_token_file(token_file: pathlib.Path):
    if token_file.exists():
        with open(token_file, "r") as f:
            token_output = f.read()
        return token_output
