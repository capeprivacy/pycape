def pack_function_args_kwargs(args, kwargs):
    """Pack function args and kwargs into a dictionnary

    If multiple args and/or kwargs are supplied to the cape function through
    Cape.run or Cape.invoke, pack them into a dictionary with the following
    keys: {"cape_fn_args": <tuple_args>, "cape_fn_kwargs": <dict_kwargs>}.
    This way we can unpack them properly in IOLifter.as_bytes_handler before
    supplying them to the Cape function.
    """
    if len(args) == 1 and len(kwargs) == 0:
        fn_inputs = args[0]
    elif len(args) == 0 and len(kwargs) == 1:
        fn_inputs = kwargs.popitem()[1]
    else:
        fn_inputs = {"cape_fn_args": args, "cape_fn_kwargs": kwargs}
    return fn_inputs


def unpack_function_args_kwargs(packed_args_kwargs):
    """Unpack function inputs into args and kwargs

    If multiple args and/or kwargs are supplied to the cape function through Cape.run
    or Cape.invoke, they will be packed into a dictionary with the following
    keys: {"cape_fn_args": <tuple_args>, "cape_fn_kwargs": <dict_kwargs>}. This
    utils is responsible to unpack them in IOLifter.as_bytes_handler before they
    get supplied to the Cape function.
    """
    if isinstance(packed_args_kwargs, dict):
        args = packed_args_kwargs.get("cape_fn_args")
        kwargs = packed_args_kwargs.get("cape_fn_kwargs")
        return args, kwargs
    else:
        return None, None
