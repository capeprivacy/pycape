"""Tools for lifting arbitrary functions into functions mapping bytes to bytes.

This module deals with automatically converting between arbitrary functions and
"byte-handlers", i.e. functions mapping bytes to bytes. The :func:`.lift_io` decorator
allows a user to convert an arbitrary function to a bytes-handler. :func:`.lift_io`
returns an :class:`.IOLifter`, a Callable class that wraps an arbitrary function with
the machinery needed to convert it into a byte-handler via
:meth:`.IOLifter.as_bytes_handler`. :class:`.IOLifter` does not otherwise change the
function's call-behavior.

**Usage** ::

    @serdio.lift_io
    def my_cool_function(x: int, y: float, b: float = 1.0) -> float:
        z = x * y
        z += b
        return z

    bytes_handler: Callable[bytes, bytes] = my_cool_function.as_bytes_handler()

    z = my_cool_function(2, 3.0)
    assert z == 7.0
"""
import functools as ft
import inspect
from operator import xor
from typing import Callable
from typing import Optional

from serdio import serde


def lift_io(
    f: Callable = None,
    *,
    encoder_hook: Optional[Callable] = None,
    decoder_hook: Optional[Callable] = None,
    hook_bundle=None,
    as_handler: bool = False,
):
    """Lift a function into an :class:`.IOLifter`.

    The resulting :class:`.IOLifter` Callable is nearly identical to the original
    function, however it can also easily be converted to a bytes-handler with
    :meth:`~IOLifter.as_bytes_handler`. The bytes-handler expects Serdio bytes as input
    and returns Serdio bytes as its output.

    This decorator expects at most one of these sets of kwargs to be specified:
        - ``encoder_hook`` and ``decoder_hook``
        - ``hook_bundle``

    Args:
        f: A Callable to be IO-lifted into a bytes-handler.
        encoder_hook: An optional Callable that specifies how to convert custom-typed
            inputs or outputs into msgpack-able Python types (e.g. converting
            MyCustomClass into a dictionary of Python natives). See
            :class:`serdio.SerdeHookBundle` for details.
        decoder_hook: An optional Callable that specifies how to invert ``encoder_hook``
            for custom-typed inputs and outputs. See :class:`serdio.SerdeHookBundle` for
            details.
        hook_bundle: An optional tuple, list, or :class:`~serdio.SerdeHookBundle` that
            simply packages up ``encoder_hook`` and ``decoder_hook`` Callables into a
            single object.
        as_handler: A boolean controlling the return type of the decorator. If
            ``False``, returns an :class:`.IOLifter` wrapping up ``f`` and the hook
            bundle specified by the supplied combination of ``encoder_hook``,
            ``decoder_hook``, and ``hook_bundle``. If True, returns the result of
            applying ``lambda x: x.as_bytes_handler()`` to the :class:`.IOLifter`.

    Returns:
        An :class:`.IOLifter` wrapping up ``f``, ``encoder_hook``, and ``decoder_hook``
        with the machinery needed to convert arbitrary functions into bytes-handlers. If
        ``as_handler=True``, returns the bytes-handler version of ``f``.

    Raises:
        ValueError: if user supplies wrong combination of ``encoder_hook``,
            ``decoder_hook``, and ``hook_bundle``.
        TypeError: if ``hook_bundle`` is not coercible to
            :class:`~serdio.SerdeHookBundle`, or if ``encoder_hook``/``decoder_hook``
            are not Callables.

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
    """A Callable for lifting arbitrary functions into equivalent bytes-handlers.

    Args:
        f: The function we want to lift.
        hook_bundle: An optional :class:`~.serdio.serde.SerdeHookBundle` for dealing
            with user-defined types
    """

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
        """Alias of :meth:`.IOLifter.as_bytes_handler`."""
        return self.as_bytes_handler()

    def as_bytes_handler(self):
        """Lift the wrapped Callable into its functionally-equivalent bytes-handler.

        A bytes-handler is a Callable mapping Serdio bytes to Serdio bytes.
        """
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
                    "Couldn't deserialize the function's input with Serdio. "
                    "Make sure your input is serialized according to the Serdio spec "
                    "manually, or by setting use_serdio=True in Cape.run / Cape.invoke."
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
