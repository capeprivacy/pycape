import os
import pathlib

import pycape._config as modself

# the following config vars will be set for this module, unless overridden
# by an identical env variable prefixed w/ "CAPE_*", e.g. CAPE_DEV_DISABLE_SSL=True
_CAPE_ENVVAR_DEFAULTS = {
    "DEV_DISABLE_SSL": False,
    "ENCLAVE_HOST": "wss://enclave.capeprivacy.com",
    "LOCAL_AUTH_FILENAME": "auth",
    "LOCAL_CAPE_KEY_FILENAME": "capekey.pub.der",
    "LOCAL_CONFIG_DIR": str(pathlib.Path.home() / ".config" / "cape"),
}


def _init_config():
    for cfgvar, default in _CAPE_ENVVAR_DEFAULTS.items():
        envname = "_".join(["CAPE", cfgvar])
        envvar = os.environ.get(envname)
        if envvar is None:
            envvar = default
        setattr(modself, cfgvar, envvar)


_init_config()
