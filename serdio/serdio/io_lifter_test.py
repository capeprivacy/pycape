import dataclasses
from typing import Callable

from absl.testing import parameterized

from serdio import io_lifter as lifting
from serdio import serde


def identity(x):
    return x


@dataclasses.dataclass
class MyCoolResult:
    cool_result: float


@dataclasses.dataclass
class MyCoolClass:
    cool_float: float
    cool_int: int

    def mul(self):
        return MyCoolResult(self.cool_int * self.cool_float)


def my_cool_encoder(x):
    if dataclasses.is_dataclass(x):
        return {"__type__": x.__class__.__name__, "fields": dataclasses.asdict(x)}
    return x


def my_cool_decoder(obj):
    if "__type__" in obj:
        obj_type = obj["__type__"]
        if obj_type == "MyCoolClass":
            return MyCoolClass(**obj["fields"])
        elif obj_type == "MyCoolResult":
            return MyCoolResult(**obj["fields"])
    return obj


class TestIoLifter(parameterized.TestCase):
    @parameterized.parameters({"x": x} for x in [1, "foo", [1, 2.0, 3]])
    def test_lifted_capehandler(self, x):
        lifted_identity = lifting.lift_io(identity)
        x_ser = serde.serialize(x)
        result = lifted_identity.as_cape_handler()(x_ser)
        result_deser = serde.deserialize(result)
        assert x == result_deser

    @parameterized.parameters({"x": x} for x in [1, "foo", [1, 2.0, 3]])
    def test_lifted_call(self, x):
        lifted_identity = lifting.lift_io(identity)
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
        @lifting.lift_io(encoder_hook=my_cool_encoder, decoder_hook=my_cool_decoder)
        def my_cool_function(x: MyCoolClass) -> MyCoolResult:
            return x.mul()

        # runs as normal
        cool_input = MyCoolClass(2, 3.0)
        expected_cool_result = MyCoolResult(6.0)
        res = my_cool_function(cool_input)
        assert res == expected_cool_result

        # cape handler runs on bytes
        cool_input_ser = serde.serialize(cool_input, encoder=my_cool_encoder)
        cape_handler = my_cool_function.as_cape_handler()
        cool_result_ser = cape_handler(cool_input_ser)
        cool_result = serde.deserialize(cool_result_ser, decoder=my_cool_decoder)
        assert cool_result == expected_cool_result
