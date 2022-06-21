## Examples

Before running a function with the Cape SDK, you can find example of functions and how to deploy them in the [functions repo](https://github.com/capeprivacy/functions).

The default function id in these examples run the [echo function](https://github.com/capeprivacy/functions/tree/main/echo). You can find your access token with `cat ~/.config/cape/auth` (TODO improve user experience).

To run a function once, you can run the following example:
```
export CAPE_TOKEN=<your token>
export CAPE_HOST=wss://cape.run
export CAPE_FUNCTION=<function id returned from cape deploy>
python run.py
```

To run a function repeatedly, you can run the following example:
```
export CAPE_TOKEN=<your token>
export CAPE_HOST=wss://cape.run
export CAPE_FUNCTION=<function id returned from cape deploy>
python invoke.py
```


