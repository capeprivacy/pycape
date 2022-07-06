from typing import Callable
from typing import Optional

import msgpack

from pycape.serialize import decode
from pycape.serialize import encode


def iolift(f):
    return lift(f, encoder_hook=encode, decoder_hook=decode).as_cape_handler()


def lift(f, *, encoder_hook=None, decoder_hook=None):
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
            f_input = msgpack.unpackb(input_bytes, object_hook=self.decoder_hook)
            fargs = f_input
            # fargs, fkwargs = f_input[:-1], f_input[-1]
            # output_tuple = self.func(*fargs, **fkwargs)
            output_tuple = self.func(fargs)
            output_blob = msgpack.packb(output_tuple, default=self.encoder_hook)
            return output_blob

        return cape_handler
