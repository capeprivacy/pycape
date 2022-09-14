import asyncio
import pathlib
import subprocess

import pycape


def deploy_echo():
    examples_dir = pathlib.Path(__file__).parent.absolute()
    # Cape deploy function
    proc_deploy = subprocess.Popen(
        "cape deploy echo",
        cwd=examples_dir,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, err_deploy = proc_deploy.communicate()
    err_deploy = err_deploy.decode()

    # Parse stderr to get function id & function checksum
    err_deploy = err_deploy.split("\n")
    function_id = function_checksum = None
    for i in err_deploy:
        if "Function ID" in i:
            id_output = i.split(" ")
            function_id = id_output[3]
        elif "Checksum" in i:
            checksum_output = i.split(" ")
            function_checksum = checksum_output[2]

    if function_id is None:
        raise RuntimeError(
            f"Function ID not found in 'deploy' response: \n{err_deploy}"
        )

    return function_id, function_checksum


async def main(cape: pycape.Cape, function_ref: pycape.FunctionRef, echo: str) -> str:
    echo_arg = echo.encode()
    echo_enc = await cape.encrypt(echo_arg)
    async with cape.function_context(function_ref):
        result = await cape.invoke(echo_enc)
    return result.decode()


if __name__ == "__main__":
    cape = pycape.Cape()
    function_id, function_checksum = deploy_echo()
    function_ref = pycape.FunctionRef(function_id, function_checksum)
    echo = asyncio.run(main(cape, function_ref, "Welcome to Cape, Vincent Law."))
    print(echo)
