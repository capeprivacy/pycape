import enum

import msgpack
import numpy as np


class _MsgpackExtType(enum.IntEnum):
    """Messagepack custom type ids."""

    ndarray = 1
    native_complex = 2
    npscalar = 3


def encode(x):
    if isinstance(x, complex):
        return msgpack.ExtType(
            _MsgpackExtType.native_complex, msgpack.packb((x.real, x.imag))
        )
    elif isinstance(x, np.ndarray):
        return msgpack.ExtType(_MsgpackExtType.ndarray, _ndarray_to_bytes(x))
    elif np.issctype(type(x)):
        # pack scalar as ndarray
        return msgpack.ExtType(
            _MsgpackExtType.npscalar, _ndarray_to_bytes(np.asarray(x))
        )
    elif isinstance(x, tuple):
        return {"__type__": "tuple", "values": list(x)}
    elif isinstance(x, set):
        return {"__type__": "set", "values": list(x)}
    elif isinstance(x, frozenset):
        return {"__type__": "frozenset", "values": list(x)}
    return x


def decode(obj):
    if "__type__" in obj:
        if obj["__type__"] == "set":
            _assert_keys_in_dict(obj, ("values",))
            return set(obj["values"])
        elif obj["__type__"] == "frozenset":
            _assert_keys_in_dict(obj, ("values",))
            return frozenset(obj["values"])
        elif obj["__type__"] == "tuple":
            _assert_keys_in_dict(obj, ("values",))
            return tuple(obj["values"])
    return obj


def serialize(x, default=None):
    encode_hook = encode
    if default is not None:
        if not callable(default):
            raise TypeError(f"`default` needs to be callable, found type {type(default)}")
        encode_hook = lambda x: default(encode(x))
    return msgpack.packb(x, default=encode_hook, strict_types=True)


def deserialize(x_bytes, object_hook=None):
    decode_hook = decode
    if object_hook is not None:
        if not callable(object_hook):
            raise TypeError(f"`object_hook` needs to be a callable, found type {type(object_hook)}")
        decode_hook = lambda x: object_hook(decode(x))
    return msgpack.unpackb(x_bytes, ext_hook=_msgpack_ext_unpack, object_hook=decode_hook)


def _assert_keys_in_dict(d, keys):
    for key in keys:
        if key not in d:
            raise ValueError(f"Missing key in data object {key}")


def _msgpack_ext_unpack(code, data):
    """Messagepack decoders for custom types."""
    if code == _MsgpackExtType.ndarray:
        return _ndarray_from_bytes(data)
    elif code == _MsgpackExtType.native_complex:
        complex_tuple = msgpack.unpackb(data)
        return complex(complex_tuple[0], complex_tuple[1])
    elif code == _MsgpackExtType.npscalar:
        ar = _ndarray_from_bytes(data)
        return ar[()]  # unpack ndarray to scalar
    return msgpack.ExtType(code, data)


def _ndarray_to_bytes(arr) -> bytes:
    """Save ndarray to simple msgpack encoding."""
    if arr.dtype.hasobject or arr.dtype.isalignedstruct:
        raise ValueError(
            "Object and structured dtypes not supported "
            "for serialization of ndarrays."
        )
    tpl = (arr.shape, arr.dtype.name, arr.tobytes("C"))
    return msgpack.packb(tpl, use_bin_type=True)


def _ndarray_from_bytes(data: bytes) -> np.ndarray:
    """Load ndarray from simple msgpack encoding."""
    shape, dtype_name, buffer = msgpack.unpackb(data, raw=True)
    return np.frombuffer(
        buffer, dtype=np.dtype(dtype_name), count=-1, offset=0
    ).reshape(shape, order="C")
