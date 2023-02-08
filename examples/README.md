# Examples

To run a function, you need to first deploy a function and generate a [function token](https://docs.capeprivacy.com/tutorials/tokens). You can deploy a function with the [Cape CLI](https://github.com/capeprivacy/cli) by running `cape deploy`. `cape deploy` will return a function ID and a checksum. Then this function ID will be used to generate a function token with `cape token`. When generating the function token, we recommend to include the function checksum, so Cape can perform additional validation that the function you are calling corresponds to the function you have deployed.   

## Echo: running functions on raw bytes

By default, Cape functions expect bytes as input and return bytes as output. For this first example, we run an echo function which expects bytes and return bytes as output.

To automatically deploy and run an example function that performs `echo`, run:
```console
$ python3 deploy_run_echo.py
```

Alternatively, you can use the Cape CLI directly via `cape deploy` and `cape token` as follows. 

You can deploy the echo function as follow:
```console
$ cape deploy echo --name echo
Deploying function to Cape ...
Success! Deployed function to Cape.
Function ID ➜  <FUNCTION_ID>
Function Checksum ➜  <FUNCTION_CHECKSUM>
```

The function ID will allow you to reference the deployment at runtime, whereas the function checksum will allow you to verify that the function running in the enclave has not been tampered with.

You can also reference this function with your Github username and the function name, e.g. `github_user/echo`.

Next, generate a personal access token for your account by running:

```console
$ cape token create --name echo --expiry 300s
Success! Your token: eyJhtGckO12...(token omitted)
```

Anyone who has a copy of this personal access token will be able to call your function by name or by id.

After deploying the function, to run a function once, you can run the following example:
```
python run_echo.py
```

To run a function repeatedly, you can run the following example:
```
python invoke_echo.py
```

## Mean: running functions on Python types

To facilate serialization and deserialization of the input and output, we use Serdio, which can automatically handle serialization for native python types with [MessagePack](https://msgpack.org/index.html). To use Serdio, we decorate our cape handler function with `@serdio.lift_io` and set `use_serdio=True` when we call `cape.run` or `cape.invoke`. See `examples/mean/app.py` for instructions on decorating.

As an example, we will compute the mean of a list of numbers. All commands should be run from the root directory of the repo.

### Step 0: Define vars for Cape endpoint and deployment folder
```console
$ mkdir -p examples/mean/build
$ export TARGET=examples/mean/build
```

###  Step 1: Install Serdio to build target
```console
$ pip install ./serdio --target $TARGET
```
Depending on your OS and Python version, you may have to run this in a manylinux-compliant Docker image with Python 3.9 (e.g. `python:3.9-slim-bullseye`).
```console
$ docker run -v `pwd`:/build -w /build --rm -it python:3.9-slim-bullseye pip install serdio --target /build/$TARGET
```

### Step 2: Add application code to build target
```console
$ cp examples/mean/app.py $TARGET
```

### Step 3: Deploy function with dependencies
```console
$ pushd examples/mean && cape deploy build --name mean && popd
Deploying function to Cape ...
Success! Deployed function to Cape.
Function ID ➜  <FUNCTION_ID>
Function Checksum ➜  <FUNCTION_CHECKSUM>
$ export FUNCTION_ID = <FUNCTION_ID>
```

### Step 4: Generate a personal access token for your account
This allows PyCape to authenticate run requests for functions you've deployed.
```console
$ cape token create --name mean
Success! Your token: eyJhtGckO12...(token omitted)
$ export TOKEN=<copied from above>
```

### Step 5: Use PyCape client to run the function in a Cape enclave
Finally, run the function with the PyCape client:
```console
$ python examples/run_mean.py
```
