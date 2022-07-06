from pycape.io_lifter import io_serialize
from pycape.serialize import deserialize
from pycape.serialize import serialize


@io_serialize
def identity(x):
    return x


class TestIoLifter:
    def test_iolifter(self):
        x = 1
        x_ser = serialize(x)
        result = identity(x_ser)
        result_deser = deserialize(result)
        assert x == result_deser
