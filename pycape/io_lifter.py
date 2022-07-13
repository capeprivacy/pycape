"""Tools for lifting normal Python functions into Cape handlers.

We automatically convert between Python functions and Cape handlers by decorating
a given Python function with a version that deserializes inputs from msgpack-ed bytes,
executes the original function on those inputs, and then serializes outputs w/ msgpack.
Custom types are handled by user-supplied encode_hook and decode_hook functions,
bundled into a SerdeHookBundle dataclass.


Usage in app.py:

    @lift_io
    def my_cool_function(x: int, y: float) -> float:
        return x * y

    cape_handler = my_cool_function.as_cape_handler()


Usage with custom types:

    @dataclass
    class MyCoolResult:
        cool_result: float

    @dataclass
    class MyCoolClass:
        cool_float: float
        cool_int: int

        def mul(self):
            return MyCoolResult(self.cool_int * self.cool_float)

    def my_cool_encoder(x):
        if isinstance(x, MyCoolClass):
            return {
                "__type__": "MyCoolClass",
                "cool_float": x.cool_float,
                "cool_int": x.cool_int,
            }
        elif isinstance(x, MyCoolResult):
            return {"__type__": "MyCoolResult", "cool_result": x.cool_result}
        return x

    def my_cool_decoder(obj):
        if "__type__" in obj:
            obj_type = obj["__type__"]
            if obj_type == "MyCoolClass":
                return MyCoolClass(obj["cool_float"], obj["cool_int"])
            elif obj_type == "MyCoolResult":
                return MyCoolResult(obj["cool_result"])
        return obj


    @lift_io(encode_hook=my_cool_encoder, decode_hook=my_cool_decoder)
    def my_cool_function(x: MyCoolClass) -> MyCoolResult:
        return x.mul()

    cape_handler = my_cool_function.as_cape_handler()


Using custom types with Cape.run:

    my_cool_function_id = <noted during `cape deploy`>
    input = MyCoolClass(2, 3.0)  # input data we want to run with
    # the serde hook bundle, specifying how msgpack can deal w/ MyCoolClass/MyCoolResult
    # hook_bundle = SerdeHookBundle(my_cool_encoder, my_cool_decoder)
    # we can also pull it from the lifted function, since we already specified it there:
    hook_bundle = my_cool_function.hook_bundle
    cape = Cape()
    # TODO serde_bundle kwarg in cape.run
    my_cool_result = cape.run(my_cool_function_id, input, serde_bundle=hook_bundle)
    print(my_cool_result.cool_result)
    >> 6.0
"""
import dataclasses
import functools as ft
from operator import xor
from typing import Callable
from typing import Optional

from pycape import serialize as serde


@dataclasses.dataclass
class SerdeHookBundle:
    encoder_hook: Callable
    decoder_hook: Callable

    def to_dict(self):
        return dataclasses.asdict(self)

    def unbundle(self):
        return dataclasses.astuple(self)


def lift_io(f=None, *, encoder_hook=None, decoder_hook=None, hook_bundle=None):
    """Lift a function into a callable that abstracts input-output (de-)serialization.

    The resulting callable is nearly identical to the original function,
    however it can also easily be converted to a Cape handler with `as_cape_handler`.
    The Cape handler expects msgpack-ed bytes as input and also msgpacks its output,
    which conforms to the kinds of Python functions that can be `Cape.invoke`-ed.

    This decorator expects at most one of these sets of kwargs to be specified:
        - `encoder_hook` and `decoder_hook`
        - `hook_bundle`

    Args:
        f: A Callable to be invoked or run with Cape.
        encoder_hook: An optional Callable that specifies how to convert custom-typed
          inputs or outputs into msgpack-able Python types (e.g. converting
          MyCustomClass into a dictionary of Python natives).
        decoder_hook: An optional Callable that specifies how to invert encoder_hook
          for custom-typed inputs and outputs.
        hook_bundle: An optional tuple, list, or SerdeHookBundle that simply packages up
          encoder_hook and decoder_hook Callables into a single object.

    Returns:
        A CapeIOLifter wrapping up `f`, `encoder_hook`, and `decoder_hook` that can be
        used in a deployable Cape script or can be run/invoked by the Cape client.
    Raises:
        ValueError if wrong combination of encoder_hook, decoder_hook, hook_bundle is
          supplied.
        TypeError if hook_bundle is not coercible to SerdeHookBundle, or if
          encoder_hook/decoder_hook are not Callables.
    """
    _check_lift_io_kwargs(encoder_hook, decoder_hook, hook_bundle)
    if encoder_hook is not None:
        hook_bundle = SerdeHookBundle(encoder_hook, decoder_hook)
    elif hook_bundle is not None:
        if isinstance(hook_bundle, (tuple, list)):
            hook_bundle = SerdeHookBundle(*hook_bundle)
        elif isinstance(hook_bundle, dict):
            _check_dict_hook_bundle(hook_bundle)
            hook_bundle = SerdeHookBundle(**hook_bundle)
    if f is None:
        return ft.partial(CapeIOLifter, hook_bundle=hook_bundle)
    return CapeIOLifter(f, hook_bundle=hook_bundle)


class CapeIOLifter:
    def __init__(
        self,
        f: Callable,
        hook_bundle: Optional[SerdeHookBundle],
    ):
        self._func = f
        self._hook_bundle = hook_bundle

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

    def as_cape_handler(self):
        if self.hook_bundle is not None:
            encoder_hook, decoder_hook = self.hook_bundle.unbundle()
        else:
            encoder_hook, decoder_hook = None, None

        def cape_handler(input_bytes):
            try:
                f_input = serde.deserialize(input_bytes, object_hook=decoder_hook)
            except ValueError:
                raise ValueError(
                    "Couldn't deserialize the function's input with MessagePack."
                    "Make sure your input is serialized with MessagePack manually or "
                    "by setting msgpack_serialize to True in cape.run or cape.invoke"
                )
            output = self._func(f_input)
            output_blob = serde.serialize(output, default=encoder_hook)
            return output_blob

        return cape_handler

    @property
    def hook_bundle(self):
        return self._hook_bundle


def _check_lift_io_kwargs(encoder_hook, decoder_hook, hook_bundle):
    _check_missing_kwargs_combo(encoder_hook, decoder_hook, hook_bundle)
    _typecheck_hooks(encoder_hook, decoder_hook)
    _typecheck_bundle(hook_bundle)


def _check_missing_kwargs_combo(encoder_hook, decoder_hook, hook_bundle):
    hooks_supplied = encoder_hook is not None and decoder_hook is not None
    bundle_supplied = hook_bundle is not None

    # don't want true xor, since both sets of args are optional
    if not hooks_supplied and not bundle_supplied:
        return

    # either hooks are supplied or bundle is supplied, but not both
    if xor(hooks_supplied, bundle_supplied):
        return

    raise ValueError(
        "The `lift_io` decorator expects at most one of these sets of kwargs "
        "to be specified:\n"
        "\t - `encoder_hook` and `decoder_hook`\n"
        "\t - `hook_bundle`\n"
        "Found:\n"
        f"\t - `encoder_hook: {type(encoder_hook)}\n"
        f"\t - `decoder_hook: {type(decoder_hook)}\n"
        f"\t - `hook_bundle: {type(hook_bundle)}\n"
    )


def _typecheck_hooks(encoder_hook, decoder_hook):
    if encoder_hook is None and decoder_hook is None:
        return
    if not callable(encoder_hook):
        raise TypeError(
            f"Expected callable `encoder_hook`, found type: {type(encoder_hook)}"
        )
    if not callable(decoder_hook):
        raise TypeError(
            f"Expected callable `decoder_hook`, found type: {type(decoder_hook)}"
        )


def _typecheck_bundle(hook_bundle):
    if hook_bundle is None:
        return
    if not isinstance(hook_bundle, (tuple, list, dict, SerdeHookBundle)):
        raise TypeError(
            "`hook_bundle` keyword-argument must be one of:\n"
            "\t- tuple\n"
            "\t- list\n"
            "\t- dict\n"
            "\t- SerdeHookBundle\n"
            f"but found type: {type(hook_bundle)}."
        )


def _check_dict_hook_bundle(hook_bundle):
    correct_size = len(hook_bundle) == 2
    correct_keys = "encoder_hook" in hook_bundle and "decoder_hook" in hook_bundle
    if not correct_size or not correct_keys:
        raise ValueError(
            "`hook_bundle` dict must have exactly two key-value pairs: 'encoder_hook'"
            f"and 'decoder_hook'. Found dict with keys: {list(hook_bundle.keys())}."
        )
