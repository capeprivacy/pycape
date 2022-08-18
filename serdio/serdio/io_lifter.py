"""Tools for lifting normal Python functions into Cape handlers.

We automatically convert between Python functions and Cape handlers by decorating
a given Python function with a version that deserializes inputs from msgpack-ed bytes,
executes the original function on those inputs, and then serializes outputs w/ msgpack.
Custom types are handled by user-supplied encode_hook and decode_hook functions,
bundled into a SerdeHookBundle dataclass.


Basic usage in app.py:

    @serdio.lift_io(as_handler=True)
    def cape_handler(x: int, y: float) -> float:
        return x * y

Then with Cape.run:
    function_id = <noted during `cape deploy`>
    cape = Cape()
    z = cape.run(function_id, 2, 3.0, use_serdio=True)
    print(z)
    >> 6.0


Usage with custom types:

    @dataclasses.dataclass
    class MyCoolResult:
        cool_result: float

    @dataclasses.dataclass
    class MyCoolClass:
        cool_int: float
        cool_float: int

        def mul(self):
            return MyCoolResult(self.cool_int * self.cool_float)

    def my_cool_encoder(x):
        if dataclasses.is_dataclass(x):
            return {
                "__type__": x.__class__.__name__,
                "fields": dataclasses.asdict(x)
            }
        return x

    def my_cool_decoder(obj):
        if "__type__" in obj:
            obj_type = obj["__type__"]
            if obj_type == "MyCoolClass":
                return MyCoolClass(**obj["fields"])
            elif obj_type == "MyCoolResult":
                return MyCoolResult(**obj["fields"])
        return obj


    @serdio.lift_io(encoder_hook=my_cool_encoder, decoder_hook=my_cool_decoder)
    def my_cool_function(x: MyCoolClass) -> MyCoolResult:
        return x.mul()

    cape_handler = my_cool_function.as_cape_handler()

Then with Cape.run:

    my_cool_function_id = <noted during `cape deploy`>
    input = MyCoolClass(2, 3.0)  # input data we want to run with

    # the serde hook bundle, specifies how msgpack can deal w/ MyCoolClass/MyCoolResult
    # hook_bundle = SerdeHookBundle(my_cool_encoder, my_cool_decoder)
    # we can also pull it from the lifted function, since we already specified it there:
    from app import my_cool_function
    hook_bundle = my_cool_function.hook_bundle

    cape = Cape()
    my_cool_result = cape.run(my_cool_function_id, input, serde_hooks=hook_bundle)
    print(my_cool_result.cool_result)
    >> 6.0
"""
import functools as ft
import inspect
from operator import xor
from typing import Callable
from typing import Optional

from serdio import serde


def lift_io(
    f=None, *, encoder_hook=None, decoder_hook=None, hook_bundle=None, as_handler=False
):
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
        as_handler: A boolean controlling the return type of the decorator. If False,
            returns an IOLifter wrapping up `f` and the hook bundle specified by the
            combination of `encoder_hook`/`decoder_hook`/`hook_bundle`. If True, returns
            the result of applying lambda x: x.as_cape_handler() to the IOLifter.

    Returns:
        An IOLifter wrapping up `f`, `encoder_hook`, and `decoder_hook` that can be
        used in a deployable Cape script or can be run/invoked by the Cape client.
        If as_handler=True, instead returns the IO-lifted version of `f`.

    Raises:
        ValueError if wrong combination of encoder_hook, decoder_hook, hook_bundle is
          supplied.
        TypeError if hook_bundle is not coercible to SerdeHookBundle, or if
          encoder_hook/decoder_hook are not Callables.
    """
    _check_lift_io_kwargs(encoder_hook, decoder_hook, hook_bundle)
    if encoder_hook is not None:
        _typecheck_hooks(encoder_hook, decoder_hook)
        hook_bundle = serde.SerdeHookBundle(encoder_hook, decoder_hook)
    elif hook_bundle is not None:
        hook_bundle = serde.bundle_serde_hooks(hook_bundle)
        _typecheck_hooks(hook_bundle.encoder_hook, hook_bundle.decoder_hook)
    if f is None:
        return ft.partial(lift_io, hook_bundle=hook_bundle, as_handler=as_handler)
    if as_handler:
        return IOLifter(f, hook_bundle=hook_bundle).as_bytes_handler()
    return IOLifter(f, hook_bundle=hook_bundle)


class IOLifter:
    def __init__(
        self,
        f: Callable,
        hook_bundle: Optional[serde.SerdeHookBundle],
    ):
        self._func = f
        self._hook_bundle = hook_bundle

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

    def as_cape_handler(self):
        return self.as_bytes_handler()

    def as_bytes_handler(self):
        if self.hook_bundle is not None:
            encoder_hook, decoder_hook = self.hook_bundle.unbundle()
        else:
            encoder_hook, decoder_hook = None, None

        def cape_handler(input_bytes):
            try:
                args, kwargs = serde.deserialize(
                    input_bytes, decoder=decoder_hook, as_signature=True
                )
            except ValueError:
                raise ValueError(
                    "Couldn't deserialize the function's input with MessagePack."
                    "Make sure your input is serialized with MessagePack manually or "
                    "by setting use_serdio=True in Cape.run or Cape.invoke"
                )
            _check_inputs_match_signature(self._func, args, kwargs)
            output = self._func(*args, **kwargs)

            output_blob = serde.serialize(output, encoder=encoder_hook)
            return output_blob

        return cape_handler

    @property
    def hook_bundle(self):
        return self._hook_bundle

    @property
    def encoder(self):
        return self._hook_bundle.encoder_hook

    @property
    def decoder(self):
        return self._hook_bundle.decoder_hook


def _check_lift_io_kwargs(encoder_hook, decoder_hook, hook_bundle):
    _check_missing_kwargs_combo(encoder_hook, decoder_hook, hook_bundle)
    _typecheck_hooks(encoder_hook, decoder_hook)
    _typecheck_bundle(hook_bundle)


def _check_missing_kwargs_combo(encoder_hook, decoder_hook, hook_bundle):
    only_single_hook = xor(encoder_hook is not None, decoder_hook is not None)
    both_hooks_supplied = encoder_hook is not None and decoder_hook is not None
    bundle_supplied = hook_bundle is not None

    # not a true xor, since both sets of args are optional
    if not only_single_hook and not both_hooks_supplied and not bundle_supplied:
        return

    # either hooks are supplied or bundle is supplied, but not both
    if not only_single_hook and xor(both_hooks_supplied, bundle_supplied):
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
    if not isinstance(hook_bundle, (tuple, list, dict, serde.SerdeHookBundle)):
        raise TypeError(
            "`hook_bundle` keyword-argument must be one of:\n"
            "\t- tuple\n"
            "\t- list\n"
            "\t- dict\n"
            "\t- SerdeHookBundle\n"
            f"but found type: {type(hook_bundle)}."
        )


def _check_inputs_match_signature(f, args, kwargs):
    sig = inspect.signature(f)
    n_inputs = len(args) + len(kwargs)
    n_sig_parameters = len(sig.parameters)

    if n_inputs != n_sig_parameters:
        raise ValueError(
            f"The number of inputs {n_inputs} provided in Cape.run or Cape invoke"
            f" doesn't match the number of inputs {n_sig_parameters} expected "
            "by the Cape handler"
        )
