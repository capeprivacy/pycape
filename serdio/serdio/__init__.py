"""**Serdio**: Automatic serialization of function inputs and outputs using MessagePack.

The primary goal of Serdio is to lift arbitrary functions into useful "byte-handlers",
i.e. functions mapping bytes to bytes, that otherwise preserve their original behavior.
Serdio also comes with a MessagePack-based serialization format that allows one to
seamlessly convert Python values to and from Serdio-bytes.
:func:`serdio.lift_io` is responsible for decorating and lifting functions, whereas
:func:`serdio.serialize` and :func:`serdio.deserialize` implement an encoder and
decoder for the Serdio serialization spec.

**Usage** ::

    @serdio.lift_io
    def my_cool_function(x: int, y: float, b: float = 1.0) -> float:
        z = x * y
        z += b
        return z

    bytes_handler: Callable[bytes, bytes] = my_cool_function.as_bytes_handler()

    z = my_cool_function(2, 3.0)
    assert z == 7.0

We can now use the ``bytes_handler`` function to map Serdio-bytes to Serdio-bytes: ::

    xyb_bytes = serdio.serialize(2, 3.0, b=2.0)
    zbytes = bytes_handler(xyb_bytes)

    z = serdio.deserialize(zbytes)
    assert z == 8.0
"""
from serdio.io_lifter import lift_io
from serdio.serde import SerdeHookBundle
from serdio.serde import bundle_serde_hooks
from serdio.serde import deserialize
from serdio.serde import serialize

__version__ = "2.0.0"
__all__ = [
    "lift_io",
    "bundle_serde_hooks",
    "deserialize",
    "serialize",
    "SerdeHookBundle",
]
