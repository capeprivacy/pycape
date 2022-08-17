# Pycape

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

### Install from source

To install the library from source and all of its dependencies, run:
```sh
git clone https://github.com/capeprivacy/pycape.git
cd pycape
make install-release
```

## Usage

Before running a function, you need to first get an access token (`<AUTH_TOKEN>`) with the [Cape CLI](https://github.com/capeprivacy/cli) by running `cape login`. Once logged into Cape, your token can be found in the `~/.config/cape/auth` file. The access token will be used when instantiating `Cape` client. If `access_token` attribute is None, it will try to load automatically the access token from your config file. Then you'll obtain a function id (`<FUNCTION_ID>`) and function hash (`<FUNCTION_HASH>`) once you have deployed a function with `cape deploy`.

### `run`

Run is used to invoke a function once with a single input. By default, inputs and outputs are expected to be bytes. 
However you can easily serialize and deserialize inputs and outputs, using Serdio. To learn more about Serdio, check out [this example](https://github.com/capeprivacy/pycape/tree/main/examples#mean-running-functions-on-python-types).
Cape returns a function hash to the user during deploy. If function hash is specified to None, then
verification of function hash will not occur. It is encouraged to always provide the desired function
hash for security. 

Example [run_echo.py](https://github.com/capeprivacy/pycape/blob/main/examples/run_echo.py):

```py
from pycape import Cape, FunctionRef

client = Cape(url="wss://enclave.capeprivacy.com")
function_id = "ad134b923745c726"
function_hash = "1b5cb2a978697d6c5dadb876c8976adb"
f = FunctionRef(function_id, function_hash)
result = client.run(f, b"Hello!")
print(result.decode())
>> hello!
```

### `invoke`

Invoke is used to run a function repeatedly with multiple inputs. It gives you more control over the lifecycle of the function invocation.

Example [invoke_echo.py](https://github.com/capeprivacy/pycape/blob/main/examples/invoke_echo.py):

```py
from pycape import Cape

client = Cape(url="wss://enclave.capeprivacy.com")
function_id = "ad134b923745c726"
function_hash = "1b5cb2a978697d6c5dadb876c8976adb"
f = FunctionRef(function_id, function_hash)
client.connect(f)
result = client.invoke(b"Hello Alice!")
print(result.decode())
>> Hello Alice!
result = client.invoke(b"Hello Bob!")
print(result.decode())
>> Hello Bob!
result = client.invoke(b"Hello Carole!")
print(result.decode())
>> Hello Carole!
```

<p align="right">(<a href="#top">back to top</a>)</p>

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

Read more about how to contribute to the Cape SDK in [CONTRIBUTING](https://github.com/capeprivacy/pycape/tree/main/CONTRIBUTING.md).

<p align="right">(<a href="#top">back to top</a>)</p>

