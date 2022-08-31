"""A structured representation of a deployed Cape function.

A FunctionRef is intended to capture any/all metadata related to a Cape function.
It is generally created from user-supplied metadata, which is given to the user
as output of the Cape CLI's `deploy` command.

Usage:

::

    fid = "asdf231lkg1324afdg"
    fhash = str(b"2l1h21jhgb2k1jh3".hex())
    fref = FunctionRef(fid, fhash)

    cape = Cape()
    cape.connect(fref)

    fref2 = FunctionRef(fid)
    fref2.set_hash(fhash)

    assert fref == fref2
"""
import enum
from typing import Optional


class FunctionAuthType(enum.Enum):
    AUTH0 = 1
    FUNCTION_TOKEN = 2


class FunctionRef:
    """A structured reference to a Cape function."""

    def __init__(
        self,
        id: str,
        hash: Optional[str] = None,
        token: Optional[str] = None,
    ) -> "FunctionRef":
        """Instantiate a FunctionRef.

        Args:
            id: Required string denoting the function ID of the deployed Cape
                function. This is typically given in the output of the Cape CLI's
                `deploy` command.
            hash: Optional string denoting the function hash of the deployed
                Cape function. If supplied, the Cape client will attempt to verify that
                enclave responses include a matching function hash whenever this
                FunctionRef is included in Cape requests.
            token: Optional string containing a Cape function token generated
                by the Cape CLI during `cape token`. If None, the Cape access token
                will be used by `Cape.connect`/`Cape.run` instead.
        """
        id_ = id
        hash_ = hash
        if id_ is None:
            raise ValueError("Function id was not provided.")
        self._id = id_
        self._hash = hash_
        self._token = token
        if token is None:
            self.set_auth_type(FunctionAuthType.AUTH0)
        else:
            self.set_auth_type(FunctionAuthType.TOKEN)

    @property
    def id(self):
        return self._id

    @property
    def hash(self):
        return self._hash

    @property
    def token(self):
        return self._token

    @property
    def auth_type(self):
        return self._auth_type

    @property
    def auth_protocol(self):
        return self._auth_protocol

    def set_auth_type(self, auth_type: FunctionAuthType):
        self._auth_type = auth_type
        if auth_type == FunctionAuthType.AUTH0:
            self._auth_protocol = "cape.runtime"
        else:
            self._auth_protocol = "cape.function"
