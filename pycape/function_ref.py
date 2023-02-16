"""A structured set of metadata representing a deployed Cape function.

A :class:`FunctionRef` is intended to capture any/all metadata related to a Cape
function. The metadata is generally user-supplied, provided to them with the output of
the Cape CLI's ``deploy`` command.

Note: We recommend using the :meth:`pycape.Cape.function` method to create
a ``FunctionRef``.

**Usage**

::

    fid = "asdf231lkg1324afdg"
    fchecksum = str(b"2l1h21jhgb2k1jh3".hex())
    fref = FunctionRef(fid, fchecksum)
    token = pycape.Token("eY12shd...")

    cape = Cape()
    cape.connect(fref, token)
"""
from __future__ import annotations

import json
import logging
import os
import pathlib
from typing import Optional
from typing import Union

_logger = logging.getLogger("pycape")


class FunctionRef:
    """A reference to a Cape function.

    Args:
        id: String denoting the function ID of the deployed Cape function.
            Typically given with the output of the Cape CLI's ``deploy`` command.
        name: String denoting the name of the deployed Cape function. Must be of the
            form ``USER/FUNC_NAME`` where ``USER`` is the Github username of the Cape
            user and ``FUNC_NAME`` is the name they gave for the function at
            deploy-time.
        checksum: Optional string denoting the checksum of the deployed Cape function.
            If supplied as part of a ``FunctionRef``, the :class:`~pycape.cape.Cape`
            client will verify that enclave responses includes a matching checksum
            whenever the ``FunctionRef`` is included in Cape requests.
    """

    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        checksum: Optional[str] = None,
    ):
        id_ = id
        if id_ is None and name is None:
            raise ValueError(
                "Must provide one of `id` or `name` arguments, found None for both."
            )

        if id_ is not None and not isinstance(id_, str):
            raise TypeError(f"Function id must be a string, found {type(id_)}.")
        self._id = id_

        self._user = None
        self._name = None
        if name is not None:
            if not isinstance(name, str):
                raise TypeError(f"Function name must be a string, found {type(id_)}.")
            terms = name.split("/")
            if len(terms) != 2:
                raise ValueError(
                    "Function name must be of form '<username>/<function_name>', "
                    f"found '{name}'."
                )
            self._user, self._name = terms

        if checksum is not None and not isinstance(checksum, str):
            raise TypeError(
                f"Function checksum must be a string, found {type(checksum)}."
            )
        self._checksum = checksum

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(\n"
            f"  name={self.full_name},\n"
            f"  id={self.id},\n"
            f"  checksum={self.checksum},\n"
            f")"
        )

    @property
    def id(self):
        return self._id

    @property
    def checksum(self):
        return self._checksum

    @property
    def user(self):
        return self._user

    @property
    def name(self):
        return self._name

    @property
    def full_name(self):
        if self.user is not None and self.name is not None:
            return f"{self.user}/{self.name}"

    @classmethod
    def from_json(cls, function_json: Union[str, os.PathLike]) -> FunctionRef:
        """Construct a :class:`~.function_ref.FunctionRef` from a JSON string or file.

        Args:
            function_json: a JSON string or filepath containing function ID and
                optional function checksum.

        Returns:
            A :class:`~.function_ref.FunctionRef` representing the deployed Cape
            function.

        Raises:
            ValueError: if the json file doesn't exist, or the json is missing a
                ``function_id`` key-value.
            TypeError: if ``function_json`` is neither Path-like nor str.
        """
        if isinstance(function_json, pathlib.Path):
            function_config = _try_load_json_file(function_json)
            if function_config is None:
                raise ValueError(f"JSON file not found @ {str(function_json)}")

        elif isinstance(function_json, str):
            # try to treat function_json as filepath str
            json_path = pathlib.Path(function_json)
            function_config = _try_load_json_file(json_path)
            # if file not found, treat function_json as json str
            function_config = function_config or json.loads(function_json)

        else:
            raise TypeError(
                "The function_json argument expects a json string or "
                f"a path to a json file, found: {type(function_json)}."
            )

        function_id = function_config.get("function_id")
        function_name = function_config.get("function_name")
        if function_id is None and function_name is None:
            raise ValueError(
                "Function JSON must have either function_id or function_name values, "
                "found neither."
            )

        # warn user when they have a deprecated function token
        function_token = function_config.get("function_token")
        if function_token is not None:
            _logger.warn(
                "Ignoring function_token in FunctionRef json. Function tokens have "
                "been removed. Instead, request a Personal Access Token from the "
                "function owner and pass it to Cape.run. More info at "
                "https://docs.capeprivacy.com/reference/user-tokens."
            )

        function_checksum = function_config.get("function_checksum")

        return cls(function_id, function_name, function_checksum)

    def to_json(self, path: Optional[Union[str, os.PathLike]] = None) -> Optional[str]:
        """Write this :class:`~.function_ref.FunctionRef` to a JSON string or file.

        Args:
            path: Optional file path to write the resulting JSON to.

        Returns:
            If ``path`` is None, a string with this :class:`~.function_ref.FunctionRef`
            as a JSON struct.
        """
        fn_ref_dict = {}
        if self.id is not None:
            fn_ref_dict["function_id"] = self.id
        if self.user is not None and self.name is not None:
            fn_ref_dict["function_name"] = f"{self.user}/{self.name}"
        if self.checksum is not None:
            fn_ref_dict["function_checksum"] = self.checksum

        if path is None:
            return json.dumps(fn_ref_dict)

        with open(path, "w") as f:
            json.dump(fn_ref_dict, f)


def _try_load_json_file(json_file: pathlib.Path):
    if json_file.exists():
        with open(json_file, "r") as f:
            json_output = json.load(f)
        return json_output
