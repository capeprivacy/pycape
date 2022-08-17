import dataclasses
import enum
from typing import Callable

import msgpack

ARGS_MARKER = "_serdio_args_"
KWARGS_MARKER = "_serdio_kwargs_"


class _MsgpackExtType(enum.IntEnum):
    """Messagepack custom type ids."""

    native_complex = 1
    native_tuple = 2
    native_set = 3
    native_frozenset = 4


def _default_encoder(x, custom_encoder=None):
    if custom_encoder is None:
        encoder = _default_encoder  # noqa: E731
    else:

        def encoder(x):
            uncollected = _default_encoder(x, custom_encoder=custom_encoder)
            return custom_encoder(uncollected)

    if isinstance(x, complex):
        return msgpack.ExtType(
            _MsgpackExtType.native_complex,
            msgpack.packb((x.real, x.imag), default=encoder, strict_types=True),
        )
    elif isinstance(x, tuple):
        return msgpack.ExtType(
            _MsgpackExtType.native_tuple,
            msgpack.packb(list(x), default=encoder, strict_types=True),
        )
    elif isinstance(x, set):
        return msgpack.ExtType(
            _MsgpackExtType.native_set,
            msgpack.packb(list(x), default=encoder, strict_types=True),
        )
    elif isinstance(x, frozenset):
        return msgpack.ExtType(
            _MsgpackExtType.native_frozenset,
            msgpack.packb(list(x), default=encoder, strict_types=True),
        )
    return x


def _msgpack_ext_unpack(code, data, custom_decoder=None):
    """Messagepack decoders for custom types."""
    if custom_decoder is None:
        custom_decoder = lambda x: x  # noqa: E731
        ext_hook = _msgpack_ext_unpack
    else:
        ext_hook = lambda c, d: _msgpack_ext_unpack(  # noqa: E731
            c, d, custom_decoder=custom_decoder
        )
    if code == _MsgpackExtType.native_complex:
        complex_tuple = msgpack.unpackb(
            data, ext_hook=ext_hook, object_hook=custom_decoder
        )
        return complex(complex_tuple[0], complex_tuple[1])
    elif code == _MsgpackExtType.native_tuple:
        tuple_list = msgpack.unpackb(
            data, ext_hook=ext_hook, object_hook=custom_decoder
        )
        return tuple(tuple_list)
    elif code == _MsgpackExtType.native_set:
        set_list = msgpack.unpackb(data, ext_hook=ext_hook, object_hook=custom_decoder)
        return set(set_list)
    elif code == _MsgpackExtType.native_frozenset:
        frozenset_list = msgpack.unpackb(
            data, ext_hook=ext_hook, object_hook=custom_decoder
        )
        return frozenset(frozenset_list)
    return msgpack.ExtType(code, data)


def serialize(*args, encoder=None, **kwargs):
    x = {ARGS_MARKER: args}
    if len(kwargs) > 0:
        x[KWARGS_MARKER] = kwargs
    encode_hook = _default_encoder
    if encoder is not None:
        if not callable(encoder):
            raise TypeError(
                f"`encoder` arg needs to be callable, found type {type(encoder)}"
            )
        encode_hook = lambda x: _default_encoder(  # noqa: E731
            x, custom_encoder=encoder
        )
    return msgpack.packb(x, default=encode_hook, strict_types=True)


def deserialize(serdio_bytes, decoder=None, as_signature=False):
    ext_hook = _msgpack_ext_unpack
    if decoder is not None:
        if not callable(decoder):
            raise TypeError(
                f"`decoder` needs to be a callable, found type {type(decoder)}"
            )
        ext_hook = lambda c, d: _msgpack_ext_unpack(  # noqa: E731
            c, d, custom_decoder=decoder
        )

    unpacked = msgpack.unpackb(serdio_bytes, ext_hook=ext_hook, object_hook=decoder)
    unpacked_args = unpacked.get(ARGS_MARKER)
    unpacked_kwargs = unpacked.get(KWARGS_MARKER, {})
    if as_signature:
        return unpacked_args, unpacked_kwargs
    return_vals = unpacked_args
    if len(return_vals) == 1:
        return return_vals[0]
    return return_vals


@dataclasses.dataclass
class SerdeHookBundle:
    encoder_hook: Callable
    decoder_hook: Callable

    def to_dict(self):
        return dataclasses.asdict(self)

    def unbundle(self):
        return dataclasses.astuple(self)


def bundle_serde_hooks(hook_bundle):
    if isinstance(hook_bundle, (tuple, list)):
        hook_bundle = SerdeHookBundle(*hook_bundle)
    elif isinstance(hook_bundle, dict):
        _check_dict_hook_bundle(hook_bundle)
        hook_bundle = SerdeHookBundle(**hook_bundle)
    return hook_bundle


def _check_dict_hook_bundle(hook_bundle):
    correct_size = len(hook_bundle) == 2
    correct_keys = "encoder_hook" in hook_bundle and "decoder_hook" in hook_bundle
    if not correct_size or not correct_keys:
        raise ValueError(
            "`hook_bundle` dict must have exactly two key-value pairs: 'encoder_hook'"
            f"and 'decoder_hook'. Found dict with keys: {list(hook_bundle.keys())}."
        )
