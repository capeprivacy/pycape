Serdio
===========

Automatic serialization of function inputs and outputs using MessagePack.

## Why Serdio?
Remotely executing Python code is complicated. A common pattern is to wrap the code into a function that maps serialized data to serialized data, however this leads to heavy amounts of boilerplate related to serialization of native and custom Python types.

Serdio makes this easy by handling this serialization boilerplate for you as much as possible. For any custom types, it only requires the user to provide a encoder/decoder helpers that break the types down into Python-native components. An example can be found <a href="#using-serdio-with-custom-types">below</a>.

## Installation

```sh
pip install serdio
```

## Usage

### Basic
Here, we use Serdio to lift a function that performs some simple math on native Python numbers.
```python
@serdio.lift_io
def my_cool_function(x: int, y: float, b: float = 1.0) -> float:
    z = x * y
    z += b
    return z

bytes_handler: Callable[bytes, bytes] = my_cool_function.as_bytes_handler()

z = my_cool_function(2, 3.0)
assert z == 7.0
```

Now we can use the `bytes_handler` function on Serdio-encoded bytes:

```python
xyb_bytes = serdio.serialize(2, 3.0, b=2.0)
zbytes = bytes_handler(xyb_bytes)

z = serdio.deserialize(zbytes)
assert z == 8.0
```

### Using Serdio with Custom Types
In this example, we reproduce the above example with custom types `MyCoolClass` and `MyCoolResult`, instead of native Python numbers.
To give Serdio a little guidance, we provide helper functions that can convert our custom types  into Python native values and back (`my_cool_encoder` and `my_cool_decoder`).

The resulting function can operate on our custom types, while Serdio automatically applies the encoder/decoder helpers to function inputs and outputs.

```python
@dataclasses.dataclass
class MyCoolResult:
    cool_result: float

    def shift(self, other: float) -> MyCoolResult:
        return MyCoolResult(self.cool_result + other)

@dataclasses.dataclass
class MyCoolClass:
    cool_int: float
    cool_float: int

    def mul(self) -> MyCoolResult:
        return MyCoolResult(self.cool_int * self.cool_float)

def my_cool_encoder(x):
    if dataclasses.is_dataclass(x):
        return {
            "__type__": x.__class__.__name__,
            "fields": dataclasses.asdict(x)
        }
    return x

def my_cool_decoder(obj):
    if "__type__" in obj:
        obj_type = obj["__type__"]
        if obj_type == "MyCoolClass":
            return MyCoolClass(**obj["fields"])
        elif obj_type == "MyCoolResult":
            return MyCoolResult(**obj["fields"])
    return obj

@serdio.lift_io(encoder_hook=my_cool_encoder, decoder_hook=my_cool_decoder)
def my_cool_function(a: MyCoolClass, b: float = 1.0) -> MyCoolResult:
    x: MyCoolResult = a.mul()
    return x.shift(b)

my_handler = my_cool_function.as_bytes_handler()

a = MyCoolClass(2, 3.0)
ab_bytes = serdio.serialize(a, b=2.0, encoder=my_cool_function.encoder)
c_bytes = my_handler(ab_bytes)
c = serdio.deserialize(c_bytes, my_cool_function.decoder)

assert c == my_cool_function(a, b=2.0)
print(c.cool_result)
# 8.0
```
