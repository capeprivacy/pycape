import dataclasses
from typing import Callable

from absl.testing import parameterized

from serdio import _test_utils as ut
from serdio import io_lifter as lifting
from serdio import serde


class TestIoLifter(parameterized.TestCase):
    @parameterized.parameters({"x": x} for x in [1, "foo", [1, 2.0, 3]])
    def test_lifted_capehandler(self, x):
        lifted_identity = lifting.lift_io(ut.identity)
        x_ser = serde.serialize(x)
        result = lifted_identity.as_cape_handler()(x_ser)
        result_deser = serde.deserialize(result)
        assert x == result_deser

    def test_lifted_capehandler_multiple_inputs(self):
        lifted_multiple_identity = lifting.lift_io(ut.multiple_identity)
        inputs_ser = serde.serialize(1, 2, z=4)
        result = lifted_multiple_identity.as_cape_handler()(inputs_ser)
        result_deser = serde.deserialize(result)
        assert (1, 2) == result_deser[:2]
        assert 4 == result_deser[2]

    def test_lifted_capehandler_wrong_nb_inputs(self):
        lifted_multiple_identity = lifting.lift_io(ut.multiple_identity)
        inputs_ser = serde.serialize(1, z=4)
        with self.assertRaises(ValueError):
            lifted_multiple_identity.as_cape_handler()(inputs_ser)

    @parameterized.parameters({"x": x} for x in [1, "foo", [1, 2.0, 3]])
    def test_lifted_call(self, x):
        lifted_identity = lifting.lift_io(ut.identity)
        result = lifted_identity(x)
        assert x == result

    def test_wrong_liftio_kwargs_raises(self):
        with self.assertRaises(ValueError):
            lifting.lift_io(lambda x: x, encoder_hook=lambda x: x)

        with self.assertRaises(ValueError):
            lifting.lift_io(lambda x: x, decoder_hook=lambda x: x)

        with self.assertRaises(ValueError):
            lifting.lift_io(
                lambda x: x,
                encoder_hook=lambda x: x,
                hook_bundle=(lambda x: x, lambda x: x),
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
            also_fake_bundle = serde.SerdeHookBundle(1, 2)
            lifting.lift_io(lambda x: x, hook_bundle=also_fake_bundle)

    def test_module_docstring_example(self):
        @lifting.lift_io(
            encoder_hook=ut.my_cool_encoder, decoder_hook=ut.my_cool_decoder
        )
        def my_cool_function(x: ut.MyCoolClass) -> ut.MyCoolResult:
            return x.mul()

        # runs as normal
        cool_input = ut.MyCoolClass(2, 3.0)
        expected_cool_result = ut.MyCoolResult(6.0)
        res = my_cool_function(cool_input)
        assert res == expected_cool_result

        # cape handler runs on bytes
        cool_input_ser = serde.serialize(cool_input, encoder=ut.my_cool_encoder)
        cape_handler = my_cool_function.as_cape_handler()
        cool_result_ser = cape_handler(cool_input_ser)
        cool_result = serde.deserialize(cool_result_ser, decoder=ut.my_cool_decoder)
        assert cool_result == expected_cool_result

    def test_multiple_not_native_python_types(self):
        @lifting.lift_io(
            encoder_hook=ut.my_cool_encoder, decoder_hook=ut.my_cool_decoder
        )
        def my_cool_function(
            x: ut.MyCoolClass, y: ut.MyCoolClass, z: ut.MyCoolClass
        ) -> ut.MyCoolResult:
            return x.mul(), y.mul(), z.mul()

        # # runs as normal
        cool_input = ut.MyCoolClass(2, 3.0)
        expected_cool_result = (
            ut.MyCoolResult(6.0),
            ut.MyCoolResult(6.0),
            ut.MyCoolResult(6.0),
        )
        res = my_cool_function(cool_input, cool_input, cool_input)
        assert res == expected_cool_result

        # cape handler runs on bytes
        cool_input_ser = serde.serialize(
            cool_input, cool_input, cool_input, encoder=ut.my_cool_encoder
        )
        cape_handler = my_cool_function.as_cape_handler()
        cool_result_ser = cape_handler(cool_input_ser)
        cool_result = serde.deserialize(cool_result_ser, decoder=ut.my_cool_decoder)
        assert cool_result == expected_cool_result
