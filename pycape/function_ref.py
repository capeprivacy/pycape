"""A structured representation of a deployed Cape function.

A FunctionRef is intended to capture any/all metadata related to a Cape function.
It is generally created from user-supplied metadata, which is given to the user
as output of the Cape CLI's `deploy` command.

Usage:
    fid = "asdf231lkg1324afdg"
    fhash = str(b"2l1h21jhgb2k1jh3".hex())
    fref = FunctionRef(fid, fhash)

    cape = Cape()
    cape.connect(fref)

    fref2 = FunctionRef(fid)
    fref2.set_hash(fhash)

    assert fref == fref2
"""


class FunctionRef:
    """A structured reference to a Cape function."""

    def __init__(self, function_id, function_hash=None):
        """Instantiate a FunctionRef.

        Args:
            function_id: Required string denoting the function ID of the deployed Cape
                function. This is typically given in the output of the Cape CLI's
                `deploy` command.
            function_hash: Optional string denoting the function hash of the deployed
                Cape function. If supplied, the Cape client will attempt to verify that
                enclave responses include a matching function hash whenever this
                FunctionRef is included in Cape requests.
        """
        if function_id is None:
            raise ValueError("Function id was not provided.")
        self._function_id = function_id
        self._function_hash = function_hash

    def get_id(self):
        return self._function_id

    def get_hash(self):
        return self._function_hash

    def set_hash(self, function_hash):
        self._function_hash = function_hash
