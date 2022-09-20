import json
import os
import pathlib
import subprocess
from typing import Optional
from typing import Union

from pycape import _config as cape_config
from pycape import function_ref as fref
from pycape.cape import _synchronizer


@_synchronizer
async def deploy(
    deploy_path: Union[str, os.PathLike], url: Optional[str] = None
) -> fref.FunctionRef:
    """Deploy a directory or a zip file containing a Cape function declared in
    an app.py script.

    This method calls `cape deploy` from the Cape CLI to deploy a Cape function
    then returns a `~.function_ref.FunctionRef` representingthe the deployed
    function.  Note that the ``deploy_path`` has to point to a directory or a
    zip file containing a Cape function declared in an app.py file and the size
    of its content  is currently limited to 1GB.

    Args:
        deploy_path: A path pointing to a directory or a zip file containing
            a Cape function declared in an app.py script.
        url: The Cape platform's websocket URL, which is responsible for forwarding
            client requests to the proper enclave instances. If None, tries to load
            value from the ``CAPE_ENCLAVE_HOST`` environment variable. If no such
            variable value is supplied, defaults to ``"wss://enclave.capeprivacy.com"``.

    Returns:
        A :class:`~.function_ref.FunctionRef` representing the deployed Cape
        function.

    Raises:
        RuntimeError: if the websocket response or the enclave attestation doc is
            malformed, or if the function path is not pointing to a directory
            or a zip file or if folder size exceeds 1GB, or if the Cape CLI cannot
            be found on the device.
    """
    url = url or cape_config.ENCLAVE_HOST
    deploy_path = pathlib.Path(deploy_path)

    cmd_deploy = f"cape deploy {deploy_path} -u {url} -o json"
    _, err_deploy = _call_cape_cli(cmd_deploy)
    err_deploy = err_deploy.decode()

    err_deploy = err_deploy.split("\n")
    error_output = function_id = function_checksum = None

    for msg in err_deploy:
        if "Error" in msg:
            error_output = msg
            error_msg = error_output.partition("Error:")[2]
            raise RuntimeError(f"Cape deploy error - {error_msg}")
        else:
            msg = json.loads(msg)
            function_id = msg.get("function_id")
            function_checksum = msg.get("function_checksum")

            if function_id and function_checksum:
                break

    if function_id is None:
        raise RuntimeError(
            f"Function ID not found in 'cape.deploy' response: \n{err_deploy}"
        )

    # TODO the function token should be set automatically with `self._token`.
    # However we set it to None for now because if the input is encrypted
    # with cape.encryp and the function is called with function token until
    # this issue is completed: https://capeprivacy.atlassian.net/browse/CAPE-1004.
    function_token = None
    # function_token = await token(function_id)

    return fref.FunctionRef(function_id, function_checksum, function_token)


async def token(function_id, expires=None, url: Optional[str] = None):
    """Generate a function token (JSON Web Token) based on a function ID.

    This method calls `cape token` from the Cape CLI to generate a function token
    based on a function ID. Tokens can be created statically (long expiration and
    bundled with your application) or created dynamically (short-lived) and have
    an owner specified expiration. This function token is required in addition
    to the function ID when calling a Cape function.

    Args:
        function_id: A function ID string representing a deployed Cape function.
        exprires: Amount of time in seconds until the the function token expires.
    url: The Cape platform's websocket URL, which is responsible for forwarding
            client requests to the proper enclave instances. If None, tries to load
            value from the ``CAPE_ENCLAVE_HOST`` environment variable. If no such
            variable value is supplied, defaults to ``"wss://enclave.capeprivacy.com"``.

    Returns:
        A function token (JSON Web Token) as a string.

        Raises:
        RuntimeError: if the Cape CLI cannot be found on the device.
    """
    url = url or cape_config.ENCLAVE_HOST

    if expires:
        cmd_token = f"cape token {function_id} --expires {expires} -u {url}"
    else:
        cmd_token = f"cape token {function_id} -u {url}"

    out_token, err_token = _call_cape_cli(cmd_token)
    err_token = err_token.decode()
    out_token = out_token.decode()

    # Parse out_token to get function token
    function_token = out_token.split("\n")[0]
    err_deploy = err_token.split("\n")
    error_output = None

    # Parse err_token to get potential errors
    for i in err_deploy:
        if "Error" in i:
            error_output = i
            error_msg = error_output.partition("Error:")[2]
            raise RuntimeError(f"Cape token error - {error_msg}")

    if function_token is None:
        raise RuntimeError(
            f"Function token not found in 'cape.token' response: \n{err_deploy}"
        )

    return function_token


def _check_if_cape_cli_available():
    exitcode, output = subprocess.getstatusoutput("cape")
    if exitcode != 0:
        raise RuntimeError(
            f"Please make sure Cape CLI is installed on your device: {output}"
        )


def _call_cape_cli(cape_cmd):
    _check_if_cape_cli_available()
    proc = subprocess.Popen(
        cape_cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = proc.communicate()
    return out, err
