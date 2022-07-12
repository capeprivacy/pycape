import numpy as np
from absl.testing import parameterized

from pycape import io_lifter as pycape
from pycape.serialize import deserialize
from pycape.serialize import serialize


@pycape.lift_io
def identity(x):
    return x


class TestIoLifter(parameterized.TestCase):
    @parameterized.parameters({"x": x} for x in [1, "foo", np.array([1, 2, 3, 4])])
    def test_lifted_capehandler(self, x):
        x_ser = serialize(x)
        result = identity.as_cape_handler()(x_ser)
        result_deser = deserialize(result)
        if isinstance(x, np.ndarray):
            np.testing.assert_array_equal(x, result_deser)
        else:
            assert x == result_deser

    @parameterized.parameters({"x": x} for x in [1, "foo", np.array([1, 2, 3, 4])])
    def test_lifted_call(self, x):
        result = identity(x)
        if isinstance(x, np.ndarray):
            np.testing.assert_array_equal(x, result)
        else:
            assert x == result
