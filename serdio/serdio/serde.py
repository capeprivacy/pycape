"""The Serdio serialization and deserialization implementation.

The ``serdio.serde`` spec is an extension of MessagePack that can handle some extra
Python types, while also allowing users to supply their own hooks for seamless
encoding/decoding of user-defined types.

**Usage** ::

    xyb_bytes = serdio.serialize(2, 3.0, b=2.0)

    x, y = serdio.deserialize(xyb_bytes)
    print(f"{x}, {y}")
    # 2, 3.0

    args, kwargs = serdio.deserialize(xyb_bytes, as_signature=True)
    print(f"{args[0]}, {args[1]}, b={kwargs["b"]}")
    # 2, 3.0, b=2.0
"""
import dataclasses
import enum
from typing import Any
from typing import Callable
from typing import Dict
from typing import Tuple

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
    """
    An extension of the default MessagePack encoder.

    Supports Python types not usually handled by MessagePack (`complex`, `tuple`, `set`,
    `frozenset`), as well as optional user-supplied types.

    Args:
        x: input value
        custom_encoder: optional callable that implements an encoder for user-defined
            types that might be encountered inside collection types.

    Returns:
        The extended MessagePack encoder.
    """
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
    """An extension of the default MessagePack decoder.

    This is the inverse of ``_default_encoder``.

    Args:
        code: Data type encoded as 1 (complex), 2 (tuple), 3 (set), or 4 (frozen set)
        data: Byte array to unpack
        custom_decoder: Optional callable that implements a decoder for user-defined
            types that might be encountered inside collection types.

    Returns:
        The extended MessagePack decoder.
    """
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


def serialize(*args: Any, encoder: Callable = None, **kwargs: Any) -> bytes:
    """Serializes a set of ``args` and ``kwargs`` into bytes with MessagePack.

    Args:
        *args: Positional arguments to include in the serialized bytes
        encoder: Optional callable specifying MessagePack encoder for user-defined
            types. See :class:`.SerdeHookBundle` for details.
        kwargs: Keyword arguments to include in the serialized bytes

    Returns:
        Dictionary of ``args`` and ``kwargs``, serialized with MessagePack and optional
        custom ``encoder``.

    Raises:
        TypeError: if ``encoder`` is not callable. Other errors can be raised by
            MessagePack during packing.
    """
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


def deserialize(
    serdio_bytes: bytes, decoder: Callable = None, as_signature: bool = False
) -> Any:
    """Unpacks serdio-serialized bytes to an object

    Args:
        serdio_bytes: Byte array to deserialize.
        decoder: Optional callable specifying Messagepack decoder for user-defined
            types. See :class:`.SerdeHookBundle` for details.
        as_signature: Optional boolean determining return format. If True, unpack the
            serialized byte array into an ``args`` tuple and a ``kwargs`` dictionary.
            This argument is most useful when the user is trying to serialize the
            inputs to a function of unknown arity.

    Returns:
        The deserialized object. If ``as_signature=True``, assumes the resulting object
        is a dictionary with an ``args`` tuple and ``kwargs`` dict for values, and
        returns these two instead of the full dictionary.
    """
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
    """An encoder-decoder hook pair for user-defined types.

    The ``encoder_hook`` and ``decoder_hook`` specify how to convert from a user-defined
    type into an equivalent collection of Python-native values and back. Thus for any
    object ``X`` of user-defined type ``T``, the following relationship should hold: ::

        hook_bundle = SerdioHookBundle(f, g)
        native_X = hook_bundle.encoder_hook(X)  # f(X)
        Y = hook_bundle.decoder_hook(native_X)  # g(native_X)
        assert X == Y

    Note that ``native_X`` above needs to be some collection of native Python values,
    e.g. a simple dataclass can be represented as a dictionary of attributes mapping to
    values.

    Args:
        encoder_hook: An encoder function specifying how :func:`.serdio.serde.serialize`
            should break down any custom types into Python native types.
        decoder_hook: The inverse of ``encoder_hook``, specifying how
            :func:`.serdio.serde.deserialize` should re-assemble the ``encoder_hook``
            output into user-defined types.
    """

    encoder_hook: Callable
    decoder_hook: Callable

    def to_dict(self) -> Dict:
        """Return the encoder-decoder hook pair as a dictionary."""
        return dataclasses.asdict(self)

    def unbundle(self) -> Tuple:
        """Return the encoder-decoder hook pair as a tuple."""
        return dataclasses.astuple(self)


def bundle_serde_hooks(hook_bundle):
    """Helper to lift an encoder-decoder hook pair into a :class:`.SerdeHookBundle`.

    Args:
        hook_bundle: A tuple, list, dict or :class:`.SerdeHookBundle` containing an
            encoder-decoder hook pair.
            If a tuple or list, the encoder_hook must come first.
            If a dictionary, must have exactly two keys ``"encoder_hook"`` and
            ``"decoder_hook"``.

    Returns:
        A :class:`.SerdeHookBundle` encapsulating the encoder-decoder hook pair.

    Raises:
        ValueError: if the ``hook_bundle`` dictionary is malformed.
    """
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
