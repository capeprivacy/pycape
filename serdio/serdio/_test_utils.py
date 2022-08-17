import dataclasses


def identity(x):
    return x


def multiple_identity(x, y, z=1):
    return x, y, z


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
