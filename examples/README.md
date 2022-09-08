# Examples

Before running a function, you need to first get an access token (`<AUTH_TOKEN>`) with the [Cape CLI](https://github.com/capeprivacy/cli) by running `cape login`. Once logged into Cape, you can find the access token in your `~/.config` directory as follows: `cat ~/.config/cape/auth`. The access token will be used when instantiating `Cape` client. If `access_token` attribute is None, it will try to automatically load the access token from your config file. Then you'll obtain a function id ('<FUNCTION_ID>') and a checksum (`<CHECKSUM>`) once you have deployed your function with `cape deploy`. If a checksum is not specified then the verification of the checksum will not occur. It is encouraged to always provide the desired checksum for security. 

## Echo: running functions on raw bytes

By default, Cape functions expect bytes as input and return bytes as output. For this first example, we run an echo function which expects bytes and return bytes as output.

To automatically deploy and run an example function that performs `echo`, run:
```
python3 deploy_run_echo.py
```

Alternatively, you can use the Cape CLI directly via `cape login` and `cape deploy` as follows. 
Once you have logged into Cape with `cape login` deploy the echo functions by running:
```
cape deploy echo/
```

After deploying the function, to run a function once, you can run the following example:
```
export CAPE_HOST=<WSS_URL>
export CAPE_FUNCTION_ID=<FUNCTION_ID returned from cape deploy>
export CAPE_CHECKSUM=<CHECKSUM returned from cape deploy>
python run_echo.py
```

To run a function repeatedly, you can run the following example:
```
export CAPE_HOST=<WSS_URL>
export CAPE_FUNCTION_ID=<FUNCTION_ID returned from cape deploy>
export CAPE_CHECKSUM=<CHECKSUM returned from cape deploy>
python invoke_echo.py
```

## Mean: running functions on Python types

To facilate serialization and deserialization of the input and output, we use Serdio, which can automatically handle serialization for native python types with [MessagePack](https://msgpack.org/index.html). To use Serdio, we decorate our cape handler function with `@serdio.lift_io` and set `use_serdio=True` when we call `cape.run` or `cape.invoke`. See `examples/mean/app.py` for instructions on decorating.

As an example, we will compute the mean of a list of numbers. All commands should be run from the root directory of the repo.

### Step 0: Define vars for Cape endpoint and deployment folder
```sh
mkdir examples/mean/build
export TARGET=examples/mean/build
export CAPE_HOST=<WSS_URL>
```

###  Step 1: Install Serdio to build target
```sh
pip install ./serdio --target $TARGET
```
Depending on your OS and Python version, you may have to run this in a manylinux-compliant Docker image with Python 3.9 (e.g. `python:3.9-slim-bullseye`).
```sh
docker run -v `pwd`:/build -w /build --rm -it python:3.9-slim-bullseye pip install serdio --target /build/$TARGET
```

### Step 2: Add application code to build target
```sh
cp examples/mean/app.py $TARGET
```

### Step 3: Deploy function with dependencies
```sh
pushd examples/mean && cape deploy build --url $CAPE_HOST && popd
```

### Step 4: Use PyCape client to run the function in a Cape enclave
Finally, run the function with the PyCape client:
```sh
export CAPE_FUNCTION=<FUNCTION_ID returned from cape deploy>
python examples/run_mean.py
```
