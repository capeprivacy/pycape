# Examples

To run a function, you need to first deploy a function and generate a [function token](https://docs.capeprivacy.com/tutorials/tokens). You can deploy a function with the [Cape CLI](https://github.com/capeprivacy/cli) by running `cape deploy`. `cape deploy` will return a function ID and a checksum. Then this function ID will be used to generate a function token with `cape token`. When generating the function token, we recommend to include the function checksum, so Cape can perform additional validation that the function you are calling corresponds to the function you have deployed.   

## Echo: running functions on raw bytes

By default, Cape functions expect bytes as input and return bytes as output. For this first example, we run an echo function which expects bytes and return bytes as output.

To automatically deploy and run an example function that performs `echo`, run:
```
python3 deploy_run_echo.py
```

Alternatively, you can use the Cape CLI directly via `cape deploy` and `cape token` as follows. 
You can deploy the echo function as follow:
```
$ cape deploy echo

Deploying function to Cape ...
Success! Deployed function to Cape.
Function ID ➜  <FUNCTION_ID>
Function Checksum ➜  <FUNCTION_CHECKSUM>
```

Then generate a function token by running:
```
cape token <FUNCTION_ID> --function-checksum <FUNCTION_CHECKSUM> -o json > echo_token.json
```
The `echo_token.json` json file will contain your function ID, function token and function checksum. This file will be later used to instantiate a `FunctionRef` object referencing your deployed function. Using a json file avoids you having to copy paste function ID, function token and function checksum from your terminal to the python script calling the function.

After deploying the function, to run a function once, you can run the following example:
```
export CAPE_HOST=<WSS_URL>
export CAPE_TOKEN_FILE=echo_token.json
python run_echo.py
```

To run a function repeatedly, you can run the following example:
```
export CAPE_HOST=<WSS_URL>
export CAPE_TOKEN_FILE=echo_token.json
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

Deploying function to Cape ...
Success! Deployed function to Cape.
Function ID ➜  <FUNCTION_ID>
Function Checksum ➜  <FUNCTION_CHECKSUM>
```

### Step 4: Generate a function token
```
cape token <FUNCTION_ID> --function-checksum <FUNCTION_CHECKSUM> -o json > mean_token.json
```

### Step 5: Use PyCape client to run the function in a Cape enclave
Finally, run the function with the PyCape client:
```sh
export CAPE_TOKEN_FILE=mean_token.json
python examples/run_mean.py
```
