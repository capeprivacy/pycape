from absl.testing import parameterized

from serdio import utils


class TestSerdioUtils(parameterized.TestCase):
    @parameterized.parameters(
        {
            "args": args,
            "kwargs": kwargs,
            "exp_packed_args_kwargs": exp_packed_args_kwargs,
        }
        for args, kwargs, exp_packed_args_kwargs in [
            ((1, 2), {"x": 3}, {"cape_fn_args": (1, 2), "cape_fn_kwargs": {"x": 3}}),
            ((1,), {}, 1),
            ((), {"x": 3}, 3),
        ]
    )
    def test_arg_kwargs_packing(self, args, kwargs, exp_packed_args_kwargs):
        packed_args_kwargs = utils.pack_function_args_kwargs(args, kwargs)
        assert packed_args_kwargs == exp_packed_args_kwargs

    @parameterized.parameters(
        {
            "packed_args_kwargs": packed_args_kwargs,
            "exp_args": exp_args,
            "exp_kwargs": exp_kwargs,
        }
        for packed_args_kwargs, exp_args, exp_kwargs in [
            ({"cape_fn_args": (1, 2), "cape_fn_kwargs": {"x": 3}}, (1, 2), {"x": 3}),
            ("foo", None, None),
        ]
    )
    def test_unpack_args_kwargs(self, packed_args_kwargs, exp_args, exp_kwargs):
        args, kwargs = utils.unpack_function_args_kwargs(packed_args_kwargs)
        assert args == exp_args
        assert kwargs == exp_kwargs
