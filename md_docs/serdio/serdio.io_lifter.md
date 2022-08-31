<!-- markdownlint-disable -->

<a href="../../serdio/serdio/io_lifter.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `serdio.io_lifter`
Tools for lifting normal Python functions into Cape handlers. 

We automatically convert between Python functions and Cape handlers by decorating a given Python function with a version that deserializes inputs from msgpack-ed bytes, executes the original function on those inputs, and then serializes outputs w/ msgpack. Custom types are handled by user-supplied encode_hook and decode_hook functions, bundled into a SerdeHookBundle dataclass. 

Basic usage in app.py: :
``` 

     @serdio.lift_io(as_handler=True)      def cape_handler(x: int, y: float) -> float:          return x * y 

Then with Cape.run: :
``` 

     function_id = "1s25hd1s28f12"      cape = Cape()      z = cape.run(function_id, 2, 3.0, use_serdio=True)      print(z)      # 6.0 

```
Usage with custom types: 

```
@dataclasses.dataclass
class MyCoolResult:
     cool_result: float

@dataclasses.dataclass
class MyCoolClass:
     cool_int: float
     cool_float: int

     def mul(self):
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
def my_cool_function(x: MyCoolClass) -> MyCoolResult:
     return x.mul()

cape_handler = my_cool_function.as_cape_handler()
``` 

Then with Cape.run: ```
my_cool_function_id = "9af98r1c52nt735yg"
input = MyCoolClass(2, 3.0)  # input data we want to run with

# the serde hook bundle, specifies how msgpack can deal w/ MyCoolClass/MyCoolResult
# hook_bundle = SerdeHookBundle(my_cool_encoder, my_cool_decoder)
# we can also pull it from the lifted function, since we already specified it there:
from app import my_cool_function
hook_bundle = my_cool_function.hook_bundle

cape = Cape()
my_cool_result = cape.run(my_cool_function_id, input, serde_hooks=hook_bundle)
print(my_cool_result.cool_result)
# 6.0
``` 


---

<a href="../../serdio/serdio/io_lifter.py#L88"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `lift_io`

```python
lift_io(
    f=None,
    encoder_hook=None,
    decoder_hook=None,
    hook_bundle=None,
    as_handler=False
)
```

Lift a function into a callable that abstracts input-output (de-)serialization. 

The resulting callable is nearly identical to the original function, however it can also easily be converted to a Cape handler with `as_cape_handler`. The Cape handler expects msgpack-ed bytes as input and also msgpacks its output, which conforms to the kinds of Python functions that can be `Cape.invoke`-ed. 

This decorator expects at most one of these sets of kwargs to be specified: 
    - `encoder_hook` and `decoder_hook` 
    - `hook_bundle` 



**Args:**
 
 - <b>`f`</b>:  A Callable to be invoked or run with Cape. 
 - <b>`encoder_hook`</b>:  An optional Callable that specifies how to convert custom-typed  inputs or outputs into msgpack-able Python types (e.g. converting  MyCustomClass into a dictionary of Python natives). 
 - <b>`decoder_hook`</b>:  An optional Callable that specifies how to invert encoder_hook  for custom-typed inputs and outputs. 
 - <b>`hook_bundle`</b>:  An optional tuple, list, or SerdeHookBundle that simply packages up  encoder_hook and decoder_hook Callables into a single object. 
 - <b>`as_handler`</b>:  A boolean controlling the return type of the decorator. If False,  returns an IOLifter wrapping up `f` and the hook bundle specified by the  combination of `encoder_hook`/`decoder_hook`/`hook_bundle`. If True, returns 
 - <b>`the result of applying lambda x`</b>:  x.as_cape_handler() to the IOLifter. 



**Returns:**
 An IOLifter wrapping up `f`, `encoder_hook`, and `decoder_hook` that can be used in a deployable Cape script or can be run/invoked by the Cape client. If as_handler=True, instead returns the IO-lifted version of `f`. 



**Raises:**
 ValueError if wrong combination of encoder_hook, decoder_hook, hook_bundle is supplied. TypeError if hook_bundle is not coercible to SerdeHookBundle, or if encoder_hook/decoder_hook are not Callables. 


---

<a href="../../serdio/serdio/io_lifter.py#L141"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `IOLifter`




<a href="../../serdio/serdio/io_lifter.py#L142"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(f: Callable, hook_bundle: Optional[SerdeHookBundle])
```






---

#### <kbd>property</kbd> decoder





---

#### <kbd>property</kbd> encoder





---

#### <kbd>property</kbd> hook_bundle







---

<a href="../../serdio/serdio/io_lifter.py#L156"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `as_bytes_handler`

```python
as_bytes_handler()
```





---

<a href="../../serdio/serdio/io_lifter.py#L153"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `as_cape_handler`

```python
as_cape_handler()
```








---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
