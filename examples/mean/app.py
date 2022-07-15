import statistics

import pycape


@pycape.lift_io
def compute_mean(x):
    return statistics.mean(x)


cape_handler = compute_mean.as_cape_handler()

# NOTE: this would have also worked, since `compute_mean` is trivial
#  cape_handler = pycape.lift_io(statistics.mean).as_cape_handler()
