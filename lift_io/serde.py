import enum

import msgpack


class _MsgpackExtType(enum.IntEnum):
    """Messagepack custom type ids."""

    native_complex = 1
    native_tuple = 2
    native_set = 3
    native_frozenset = 4


def _default_encoder(x):
    if isinstance(x, complex):
        return msgpack.ExtType(
            _MsgpackExtType.native_complex, msgpack.packb((x.real, x.imag))
        )
    elif isinstance(x, tuple):
        return msgpack.ExtType(_MsgpackExtType.native_tuple, msgpack.packb(list(x)))
    elif isinstance(x, set):
        return msgpack.ExtType(_MsgpackExtType.native_set, msgpack.packb(list(x)))
    elif isinstance(x, frozenset):
        return msgpack.ExtType(_MsgpackExtType.native_frozenset, msgpack.packb(list(x)))
    return x


def _msgpack_ext_unpack(code, data):
    """Messagepack decoders for custom types."""
    if code == _MsgpackExtType.native_complex:
        complex_tuple = msgpack.unpackb(data)
        return complex(complex_tuple[0], complex_tuple[1])
    elif code == _MsgpackExtType.native_tuple:
        tuple_list = msgpack.unpackb(data)
        return tuple(tuple_list)
    elif code == _MsgpackExtType.native_set:
        set_list = msgpack.unpackb(data)
        return set(set_list)
    elif code == _MsgpackExtType.native_frozenset:
        frozenset_list = msgpack.unpackb(data)
        return frozenset(frozenset_list)
    return msgpack.ExtType(code, data)


def serialize(x, encoder=None):
    encode_hook = _default_encoder
    if encoder is not None:
        if not callable(encoder):
            raise TypeError(
                f"`encoder` arg needs to be callable, found type {type(encoder)}"
            )
        encode_hook = lambda x: encoder(_default_encoder(x))  # noqa: E731
    return msgpack.packb(x, default=encode_hook, strict_types=True)


def deserialize(x_bytes, decoder=None):
    if decoder is not None:
        if not callable(decoder):
            raise TypeError(
                f"`decoder` needs to be a callable, found type {type(decoder)}"
            )
    return msgpack.unpackb(x_bytes, ext_hook=_msgpack_ext_unpack, object_hook=decoder)


def _assert_keys_in_dict(d, keys):
    for key in keys:
        if key not in d:
            raise ValueError(f"Missing key in data object {key}")
