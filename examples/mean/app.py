import statistics

from pycape import io_serialize


@io_serialize
def cape_handler(x):
    return statistics.mean(x)
