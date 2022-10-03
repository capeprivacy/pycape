import asyncio
import os
import pathlib

import pycape
from pycape.experimental import cli


async def main(cape: pycape.Cape, deploy_path: os.PathLike, echo: str) -> str:
    function_ref = await cli.deploy(deploy_path)
    echo_arg = echo.encode()
    echo_enc = await cape.encrypt(echo_arg, function_ref.token)
    async with cape.function_context(function_ref):
        result = await cape.invoke(echo_enc)
    return result.decode()


if __name__ == "__main__":
    echo_path = pathlib.Path(__file__).parent.absolute() / "echo"

    cape = pycape.Cape()
    echo = asyncio.run(main(cape, echo_path, "Welcome to Cape."))
    print(echo)
