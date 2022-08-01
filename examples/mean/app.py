import statistics

import serdio


@serdio.lift_io(as_handler=True)
def cape_handler(x):
    return statistics.mean(x)


# NOTE: this would have also worked, since `compute_mean` is trivial
#  cape_handler = serdio.lift_io(statistics.mean).as_cape_handler()
