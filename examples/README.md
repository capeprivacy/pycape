## Examples

Before running a function, you need to first get an access token (`<AUTH_TOKEN>`) with the [Cape CLI](https://github.com/capeprivacy/cli) by running `cape login`. Once logged into Cape, you can find the access token in your `~/.config` directory as follows: `cat ~/.config/cape/auth`. Then you'll obtain a function id ('<FUNCTION_ID>') once you have deployed your function with `cape deploy`.

### Without automatic serialization

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

### With automatic serialization

To facilate serialization and deserialization of the input and output, PyCape offers the option to automatically handle serialization for native python types with [MessagePack](https://msgpack.org/index.html) by setting `msgpack_serialize=True` in `cape.run` or `cape.invoke` and decorating the `cape_handler` with `@io_serialize`.

As an example, we will compute the mean of a list of numbers. First, deploy the function as follow:
```
cape deploy mean/
```

Then run the function:
```
export CAPE_TOKEN=<AUTH_TOKEN>
export CAPE_HOST=<WSS_URL>
export CAPE_FUNCTION=<FUNCTION_ID returned from cape deploy>
python run_mean.py
```






