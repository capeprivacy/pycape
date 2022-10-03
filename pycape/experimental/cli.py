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
    deploy_path: Union[str, os.PathLike],
    url: Optional[str] = None,
    token_expiry: Optional[str] = None,
) -> fref.FunctionRef:
    """Deploy a directory or a zip file containing a Cape function declared in
    an app.py script.

    This method calls `cape deploy` and `cape token` from the Cape CLI to deploy
    a Cape function then returns a `~.function_ref.FunctionRef` representing
    the deployed function. This `~.function_ref.FunctionRef` will hold a function ID,
    a function token and a function checksum. Note that the ``deploy_path`` has to
    point to a directory or a zip file containing a Cape function declared in an app.py
    file and the size of its content  is currently limited to 1GB.

    Args:
        deploy_path: A path pointing to a directory or a zip file containing
            a Cape function declared in an app.py script.
        url: The Cape platform's websocket URL, which is responsible for forwarding
            client requests to the proper enclave instances. If None, tries to load
            value from the ``CAPE_ENCLAVE_HOST`` environment variable. If no such
            variable value is supplied, defaults to ``"wss://enclave.capeprivacy.com"``.
        token_expriry: Amount of time in seconds until the function token expires.

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
    out_deploy, err_deploy = _call_cape_cli(cmd_deploy)
    err_deploy = err_deploy.decode()
    out_deploy = out_deploy.decode()

    err_deploy = err_deploy.split("\n")
    error_output = None

    # Parse err_token to get potential errors
    for msg in err_deploy:
        if "Error" in msg:
            error_output = msg
            error_msg = error_output.partition("Error:")[2]
            raise RuntimeError(f"Cape deploy error - {error_msg}")

    # Parse out_deploy to get function ID and function checksum
    out_deploy = json.loads(out_deploy.split("\n")[0])
    function_id = out_deploy.get("function_id")
    function_checksum = out_deploy.get("function_checksum")

    if function_id is None:
        raise RuntimeError(
            f"Function ID not found in 'cape.deploy' response: \n{err_deploy}"
        )

    function_reference = await token(
        function_id, expiry=token_expiry, function_checksum=function_checksum
    )

    return function_reference


async def token(
    function_id,
    expiry=Optional[None],
    function_checksum: Optional[str] = None,
) -> fref.FunctionRef:
    """Generate a function token (JSON Web Token) based on a function ID.

    This method calls `cape token` from the Cape CLI to generate a function token
    based on a function ID. Tokens can be created statically (long expiration and
    bundled with your application) or created dynamically (short-lived) and have
    an owner specified expiration. This function token is required in addition
    to the function ID when calling a Cape function.

    Args:
        function_id: A function ID string representing a deployed Cape function.
        expiry: Amount of time in seconds until the function token expires.

    Returns:
        A :class:`~.function_ref.FunctionRef` representing the deployed Cape
        function.

        Raises:
        RuntimeError: if the Cape CLI cannot be found on the device.
    """
    if expiry:
        cmd_token = (
            f"cape token {function_id} --function-checksum {function_checksum} "
            f"--expiry {expiry} -o json"
        )
    else:
        cmd_token = (
            f"cape token {function_id} --function-checksum {function_checksum} -o json"
        )

    out_token, err_token = _call_cape_cli(cmd_token)
    err_token = err_token.decode()
    out_token = out_token.decode()

    err_deploy = err_token.split("\n")
    error_output = None
    # Parse err_token to get potential errors
    for i in err_deploy:
        if "Error" in i:
            error_output = i
            error_msg = error_output.partition("Error:")[2]
            raise RuntimeError(f"Cape token error - {error_msg}")

    # Parse out_token to get function token
    function_token = json.loads(out_token.split("\n")[0]).get("function_token")

    if function_token is None:
        raise RuntimeError(
            f"Function token not found in 'cape.token' response: \n{err_deploy}"
        )

    return fref.FunctionRef(function_id, function_token, function_checksum)


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
