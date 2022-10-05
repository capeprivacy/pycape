"""A structured set of metadata representing a deployed Cape function.

A :class:`FunctionRef` is intended to capture any/all metadata related to a Cape
function. The metadata is generally user-supplied, provided to them with the output of
the Cape CLI's ``deploy`` command.

**Usage**

::

    fid = "asdf231lkg1324afdg"
    fchecksum = str(b"2l1h21jhgb2k1jh3".hex())
    fref = FunctionRef(fid, fchecksum)

    cape = Cape()
    cape.connect(fref)
"""
import json
import os
import pathlib
from typing import Optional
from typing import Union


class FunctionRef:
    """A reference to a Cape function.

    Args:
        id: Required string denoting the function ID of the deployed Cape function.
            Typically given with the output of the Cape CLI's ``deploy`` command.
        token: Required string containing a Cape function token generated by the Cape
            CLI during ``cape token``.
        checksum: Optional string denoting the checksum of the deployed Cape function.
            If supplied as part of a ``FunctionRef``, the :class:`~pycape.cape.Cape`
            client will verify that enclave responses includes a matching checksum
            whenever the ``FunctionRef`` is included in Cape requests.
    """

    def __init__(
        self,
        id: str,
        token: str,
        checksum: Optional[str] = None,
    ):
        id_ = id
        if not isinstance(id_, str):
            raise TypeError(f"Function id must be a string, found {type(id_)}.")
        if not isinstance(token, str):
            raise TypeError(f"Function token must be a string, found {type(token)}.")
        if checksum is not None and not isinstance(checksum, str):
            raise TypeError(
                f"Function checksum must be a string, found {type(checksum)}."
            )
        self._id = id_
        self._checksum = checksum
        self._token = token

    @property
    def id(self):
        return self._id

    @property
    def checksum(self):
        return self._checksum

    @property
    def token(self):
        return self._token

    @classmethod
    def from_json(cls, function_json: Union[str, os.PathLike]):
        """
        Load a json string or file containing a function ID, token & checksum.

        Args:
            function_json: a json string or a json file with a function ID, token
            and checksum (optional) generated by the Cape CLI's ``token`` command.

        Returns:
            A :class:`~.function_ref.FunctionRef` representing the deployed Cape
            function.

        Raises:
            ValueError: if the json token file doesn't exist or, the token file
                doesn't contain a `function_id` or a `function_token`.
        """

        try:
            if isinstance(function_json, pathlib.Path):
                function_config = json.loads(str(function_json))
            else:
                function_config = json.loads(function_json)
        except json.JSONDecodeError:
            if isinstance(function_json, str):
                function_json = pathlib.Path(function_json)

            if function_json.exists():
                with open(function_json, "r") as f:
                    function_config = json.load(f)
            else:
                raise ValueError(
                    "Couldn't parse the json string or couldn't find "
                    f"the function json file with the provided path: {str(function_json)}"
                )

        function_id = function_config.get("function_id")
        if function_id is None:
            raise ValueError("Couldn't find a `function_id` in the token file provided")

        function_token = function_config.get("function_token")
        if function_token is None:
            raise ValueError(
                "Couldn't find a `function_token` in the token file provided"
            )

        function_checksum = function_config.get("function_checksum")

        return cls(function_id, function_token, function_checksum)

    def to_json(self, path: Optional[Union[str, os.PathLike]] = None):
        """
        Save function ID, token & checksum in a json file or as a json string
        if path is None.

        Args:
            path: optional file path to save function ID, token & checksum
            as a json string. Otherwise it will return a json string.
        """

        fn_ref_dict = {
            "function_id": self._id,
            "function_token": self._token,
            "function_checksum": self._checksum,
        }

        if path is None:
            return json.dumps(fn_ref_dict)
        else:
            with open(path, "w") as f:
                json.dump(fn_ref_dict, f)
