from typing import Callable
from typing import Optional

import msgpack

from pycape.serialize import decode
from pycape.serialize import encode


def io_serialize(f):
    return lift(f, encoder_hook=encode, decoder_hook=decode).as_cape_handler()


def lift(f, encoder_hook=None, decoder_hook=None):
    return CapeIOLifter(f, encoder_hook, decoder_hook)


class CapeIOLifter:
    def __init__(
        self,
        f: Callable,
        encoder_hook: Optional[Callable] = None,
        decoder_hook: Optional[Callable] = None,
    ):
        self.encoder_hook = encoder_hook
        self.decoder_hook = decoder_hook
        self.func = f

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def as_cape_handler(self):
        def cape_handler(input_bytes):
            try:
                f_input = msgpack.unpackb(input_bytes, object_hook=self.decoder_hook)
            except ValueError:
                raise ValueError(
                    "Couldn't deserialize the function's input with MessagePack."
                    "Make sure your input is serialized with MessagePack manually or "
                    "by setting msgpack_serialize to True in cape.run or cape.invoke"
                )
            output_tuple = self.func(f_input)
            output_blob = msgpack.packb(output_tuple, default=self.encoder_hook)
            return output_blob

        return cape_handler
