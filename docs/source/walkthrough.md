Walkthrough
=================

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#introduction">Introduction</a></li>
    <li><a href="#a-simple-example">A Simple Example</a></li>
    <li><a href="#mean-v2-running-functions-on-python-types-with-serdio">Mean v2</a></li>
    <li><a href="#invoking-a-cape-function-multiple-times">Invoking a Cape function multiple times</a></li>
  </ol>
</details>

## Introduction 
The PyCape SDK helps users write their Cape functions in Python, and allows users to run functions which have already been deployed to Cape. Users call these functions from Python using either Cape.run or Cape.invoke. The PyCape SDK also provides some extra utilities for Python users to prepare their functions for the enclave.

Prior to following this walkthrough, we encourage the reader to set up their local environment by following the [Quick Start guide](https://docs.capeprivacy.com/getting-started).

In this guide, we will walk through several examples of writing a Cape function and invoking it from Python.

## A Simple Example

Let’s start by writing a simple function.  In this example, we'll take the average, or mean, of a list of numbers. Cape expects a `cape_handler` function that takes a single parameter of bytes as input. We refer to this as a “Cape function”.

Here’s a Cape function that computes the mean of a list of numbers:
```python
import json
import statistics
 
def cape_handler(x_bytes):
   x = json.loads(x_bytes.decode())
   x_mean = statistics.mean(x)
   return json.dumps(x_mean).encode()
```

### Deploying our first function
To deploy this function, we can follow two steps.

First, save the code into an `app.py` file in a folder called `mean`, similar to the [“Writing Functions” guide](https://docs.capeprivacy.com/tutorials/writing). The result should look like [this example](https://github.com/capeprivacy/pycape/tree/main/examples/mean). 

Then deploy this folder by calling `cape deploy mean`, per the [“Deploying Functions” guide](https://docs.capeprivacy.com/tutorials/deploying).

### Running our first function

Once we’ve deployed the Cape function successfully, we’ll have a function ID and checksum. The next step is to generate a [function token](https://docs.capeprivacy.com/tutorials/tokens) based on the function ID as follow using `cape token`:
```
cape token <FUNCTION_ID> --function-checksum <FUNCTION_CHECKSUM> -o json > mean_token.json
```
The `mean_token.json` will contain the function ID, function token and function checksum. We can now use this json file to call the function from PyCape as follows:

```python
cape = Cape(url="wss://enclave.capeprivacy.com")
function_ref = FunctionRef.from_json("mean_token.json")
x_bytes = json.dumps([1, 2, 3, 4]).encode()
result_bytes = cape.run(function_ref, x_bytes)
print("Mean of x is:", json.loads(result_bytes.decode()))
# Mean of x is: 2.5
```

Congrats! We've called our first Cape function from PyCape.

## Mean v2: Running functions on Python types with Serdio

The previous example shows how to run a single-parameter function mapping bytes to bytes. However, handling serialization and deserialization of arbitrary inputs for every Cape function can lead to a lot of boilerplate. We can use Serdio to automate this for Cape functions with arbitrary signatures.

**Serdio**, or **SER**ialization and **D**eserialization of (function) **I**nputs and **O**utputs, is a small library that simplifies the Cape function development process. Serdio implements automatic serialization and deserialization of native Python types with [MessagePack](https://msgpack.org/index.html), with additional support for custom types via user-supplied helpers.

To use Serdio, we decorate our cape handler function with `@serdio.lift_io` and set `use_serdio=True` when we call `Cape.run` or `Cape.invoke`. See [examples/mean/app.py](https://github.com/capeprivacy/pycape/blob/main/examples/mean/app.py) for instructions on decorating.

Let’s rewrite the previous averaging example in `app.py` to use Serdio: 

```python
import statistics
import serdio
 
@serdio.lift_io(as_handler=True)
def cape_handler(x):
   return statistics.mean(x)
```
 
In our first example, the code includes `json.loads` and `json.dumps` to convert from Python types to bytes. In the second example where we’ve added Serdio, we no longer need this extra step, as Serdio handles it for us automatically.

However, we’ve introduced a new problem. Serdio is not part of the Python standard library, so the Cape enclave won’t know how to import it. We’ll need to add Serdio as a dependency to execute this Cape function in the enclave.

### Adding Serdio as a dependency

We can add the Serdio dependency similarly to how we would [add any other third-party dependency](https://docs.capeprivacy.com/how-to/dependencies). First, we add a `requirements.txt` file that specifies the version of Serdio we want to use. In this case, it should be equivalent to the version of PyCape we're using:

```
serdio~=1.0.0
```

Then, we install this into the folder that contains our application code in `app.py`. In the previous example, this was the `mean` folder which we'll use again.
```sh
pip install serdio --target mean/
```

```{important}
For more complicated Python dependencies that include C extension modules, this step will download and/or compile platform- and architecture-specific binaries. Therefore, running the installation step inside a Docker container like `python:3.9-slim-bullseye` is heavily recommended by the [third-party dependency guide](https://docs.capeprivacy.com/reference/functions#adding-3rd-party-dependencies).
```

Finally, re-deploy this code with `cape deploy mean`, and make note of the function ID, checksum, and generate the function token with `cape token`.

### Running Mean v2 with PyCape

After re-deploying this code, we can call it from PyCape like we did before.
```python
cape = Cape(url="wss://enclave.capeprivacy.com")
function_ref = FunctionRef.from_json("mean_token.json")
x = [1, 2, 3, 4]
result = cape.run(function_ref, x, use_serdio=True)
print(f"The mean of x is: {result}")
# Mean of x is: 2.5
```

## Invoking a Cape function multiple times
If we want to invoke the same Cape function more than once in a Python application, we can take more explicit control PyCape's connection to the function enclave via a three-step process.
1. Open the connection with `Cape.connect`
2. Call our function as many times as we'd like via `Cape.invoke`.
3. Close the connection with `Cape.close`

```python
cape = Cape()
function_ref = FunctionRef.from_json("mean_token.json")
cape.connect(function_ref)
low_list = [1, 2, 3, 4]
result = cape.invoke(low_list, use_serdio=True)
print(f"The mean is equal to: {result}")
# The mean is equal to: 2.5

high_list = [5, 6, 7, 8]
result = cape.invoke(high_list, use_serdio=True)
print(f"The mean is equal to: {result}")
# The mean is equal to: 6.5

result = cape.invoke(low_list + high_list, use_serdio=True)
print(f"The mean is equal to: {result}")
# The mean is equal to: 4.5

result = cape.invoke([9, 10, 11, 12], use_serdio=True)
print(f"The mean is equal to: {result}")
# The mean is equal to: 10.5

cape.close()
```

In fact, the `Cape.run` that we used before is simply a convenience function rolling these three commands into one: `Cape.run` = `Cape.connect` + `Cape.invoke` + `Cape.close`.
