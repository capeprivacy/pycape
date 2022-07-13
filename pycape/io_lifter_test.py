import dataclasses
from typing import Callable

import numpy as np
from absl.testing import parameterized

from pycape import io_lifter as lifting
from pycape.serialize import deserialize
from pycape.serialize import serialize


@lifting.lift_io
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

    def test_wrong_liftio_kwargs_raises(self):
        with self.assertRaises(ValueError):
            lifting.lift_io(lambda x: x, encoder_hook=lambda x: x)

        with self.assertRaises(ValueError):
            lifting.lift_io(lambda x: x, decoder_hook=lambda x: x)

        with self.assertRaises(ValueError):
            hook_bundle = (lambda x: x, lambda x: x)
            lifting.lift_io(
                lambda x: x, encoder_hook=lambda x: x, hook_bundle=lambda x: x
            )

    def test_wrong_liftio_types(self):
        @dataclasses.dataclass
        class MyFakeHookBundle:
            encoder_hook: Callable
            decoder_hook: Callable

        with self.assertRaises(TypeError):
            lifting.lift_io(lambda x: x, encoder_hook=1, decoder_hook=2)

        with self.assertRaises(TypeError):
            fake_bundle = MyFakeHookBundle(lambda x: x, lambda x: x)
            lifting.lift_io(lambda x: x, hook_bundle=fake_bundle)

        with self.assertRaises(TypeError):
            also_fake_bundle = lifting.SerdeHookBundle(1, 2)
            lifting.lift_io(lambda x: x, hook_bundle=also_fake_bundle)
