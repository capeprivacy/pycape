# Examples

Before running a function, you need to first get an access token (`<AUTH_TOKEN>`) with the [Cape CLI](https://github.com/capeprivacy/cli) by running `cape login`. Once logged into Cape, you can find the access token in your `~/.config` directory as follows: `cat ~/.config/cape/auth`. Then you'll obtain a function id ('<FUNCTION_ID>') once you have deployed your function with `cape deploy`.

## Echo: running functions on raw bytes

By default, Cape functions expect bytes as input and return bytes as output. For this first example, we run an echo function which expects bytes and return bytes as output.

Once you have logged into Cape with `cape login` deploy the echo functions as follow:
```
cape deploy echo/
```

After deploying the function, to run a function once, you can run the following example:
```
export CAPE_TOKEN=<AUTH_TOKEN>
export CAPE_HOST=<WSS_URL>
export CAPE_FUNCTION=<FUNCTION_ID returned from cape deploy>
python run_echo.py
```

To run a function repeatedly, you can run the following example:
```
export CAPE_TOKEN=<AUTH_TOKEN>
export CAPE_HOST=<WSS_URL>
export CAPE_FUNCTION=<FUNCTION_ID returned from cape deploy>
python invoke_echo.py
```

## Mean: running functions on Python types

To facilate serialization and deserialization of the input and output, PyCape offers the option to automatically handle serialization for native python types with [MessagePack](https://msgpack.org/index.html) by decorating the cape handler function with `@lift_io` and setting `msgpack_serialize=True` in `cape.run` or `cape.invoke`. See `examples/mean/app.py` for instructions on decorating.

As an example, we will compute the mean of a list of numbers. First, deploy the function as follows:

### Step 0: Define target for dependencies build
```sh
mkdir examples/mean/build
export TARGET=examples/mean/build
```

###  Step 1: Install PyCape dependencies to build target
The wheel file in the last line might have a slightly different name, depending on your platform-specifics. Depending on your OS, you may have to run this in a manylinux-compliant Docker image.
```sh
pip install -r requirements.txt --target $TARGET
pushd hpke_spec && maturin build && popd  # take note of the wheel name in this line's output
pip install hpke_spec/target/wheels/hpke_spec-0.1.0-cp39-cp39-manylinux_2_31_x86_64.whl --target $TARGET
```

### Step 2: Install PyCape to build target
```sh
pip install . --target $TARGET
```

### Step 3: Add application code to build target
```sh
cp examples/mean/app.py $TARGET
```

### Step 4: Deploy function with dependencies
```sh
cape deploy examples/mean/
```

### Step 5: Run the function with the pycape.Cape client
Then run the function:
```sh
export CAPE_TOKEN=<AUTH_TOKEN>
export CAPE_HOST=<WSS_URL>
export CAPE_FUNCTION=<FUNCTION_ID returned from cape deploy>
python run_mean.py
```
