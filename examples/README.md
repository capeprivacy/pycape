## Examples

Before running a function, you need to first get an access token (`<AUTH_TOKEN>`) with the [Cape CLI](https://github.com/capeprivacy/cli) by running `cape login`. Once logged into Cape, you can find the access token in your `~/.config` directory as follows: `cat ~/.config/cape/auth`. Then you'll obtain a function id ('<FUNCTION_ID>') once you have deployed your function with `cape deploy`.

The default function id in these examples run the [echo function](https://github.com/capeprivacy/functions/tree/main/echo) from the [functions](https://github.com/capeprivacy/functions) repository. 

To run a function once, you can run the following example:
```
export CAPE_TOKEN=<AUTH_TOKEN>
export CAPE_HOST=wss://cape.run
export CAPE_FUNCTION=<FUNCTION_ID returned from cape deploy>
python run.py
```

To run a function repeatedly, you can run the following example:
```
export CAPE_TOKEN=<AUTH_TOKEN>
export CAPE_HOST=wss://cape.run
export CAPE_FUNCTION=<FUNCTION_ID returned from cape deploy>
python invoke.py
```


