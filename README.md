# PyCape

The Cape SDK for Python is a library that provides a simple way to interact with the Cape Privacy API.

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#installation">Installation</a></li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contributing">Contributing</a></li>
  </ol>
</details>


## Installation

### Prerequisites

* Python 3.7+
* [pip](https://pip.pypa.io/en/stable/installing/)
* [Make](https://www.gnu.org/software/make/) (if installing from source)

We recommend that you use a [Python "Virtual Environment"](https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments) when installing `pycape`.

### Install via pip
You can install the current release with:
```sh
pip install pycape
```

### Install from source

To install the library from source and all of its dependencies, run:
```sh
git clone https://github.com/capeprivacy/pycape.git
cd pycape
make install-release
```

## Usage

To run a function, you need to first deploy a function and generate a [function token](https://docs.capeprivacy.com/tutorials/tokens). You can deploy a function with the [Cape CLI](https://github.com/capeprivacy/cli) by running `cape deploy`. `cape deploy` will return a function ID and a checksum. Then this function ID will be used to generate a function token with `cape token`. When generating the function token, we recommend to include the function checksum, so Cape can perform additional validation that the function you are calling corresponds to the function you have deployed. You can checkout the [examples repository](https://github.com/capeprivacy/pycape/blob/main/examples/) to see the process end to end. 

### `run`

Run is used to invoke a function once with a single input. A connection to a Cape function is created, then terminated upon completion (no set up or tear down is required). If you wish to invoke the same function multiple times without terminating the connection between calls, please see [invoke](#invoke). By default, inputs and outputs are expected to be bytes.

> Note: You can optionally use [Serdio](https://github.com/capeprivacy/pycape/tree/main/serdio) to help with serialization and deserialization of inputs and outputs. To learn more, please check out [this example](https://pydocs.capeprivacy.com/walkthrough.html#mean-v2-running-functions-on-python-types-with-serdio).

Example [run_echo.py](https://github.com/capeprivacy/pycape/blob/main/examples/run_echo.py):

```python
from pycape import Cape
from pycape import FunctionRef

client = Cape(url="https://app.capeprivacy.com")
f = FunctionRef.from_json("echo_token.json")
result = client.run(f, b"Hello!")
print(result.decode())
# Hello!
```

### `invoke`

Invoke is used to run a function repeatedly with multiple inputs. The connection to your Cape function is not terminated between invocations. It gives you more control over the lifecycle, and can be more efficient. Prior to calling `invoke`, `connect` to your function and then `close` it when you are finished. You can also call `invoke` inside of a `Cape.function_context`, which will handle connecting and closing the connection for you. See the [docs](https://pydocs.capeprivacy.com/pycape.html#pycape.Cape.function_context) for a usage example.

Example [invoke_echo.py](https://github.com/capeprivacy/pycape/blob/main/examples/invoke_echo.py):

```python
from pycape import Cape
from pycape import FunctionRef

client = Cape(url="https://app.capeprivacy.com")
f = FunctionRef.from_json("echo_token.json")

client.connect(f)
result = client.invoke(b"Hello Alice!")
print(result.decode())
# Hello Alice!
result = client.invoke(b"Hello Bob!")
print(result.decode())
# Hello Bob!
result = client.invoke(b"Hello Carole!")
print(result.decode())
# Hello Carole!

client.close()
```

Please note that there is a 60-second inactivity timeout on the enclave connection. You may need to monitor the connection status and reconnect if there is a significant wait between inputs.

<p align="right">(<a href="#top">back to top</a>)</p>

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

Read more about how to contribute to the Cape SDK in [CONTRIBUTING](https://github.com/capeprivacy/pycape/tree/main/CONTRIBUTING.md).

<p align="right">(<a href="#top">back to top</a>)</p>

