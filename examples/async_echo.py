import asyncio
import pathlib

import pycape

parent_dir = pathlib.Path(__file__).parent.absolute()
echo_func_file = parent_dir / "echo.json"
token_file = parent_dir / "capedocs.token"
function_owner = "capedocs"


async def main(
    cape: pycape.Cape, function: pycape.FunctionRef, token: pycape.Token, echo: str
) -> str:
    echo_arg = echo.encode()
    echo_enc = await cape.encrypt(echo_arg, username=function.user)
    async with cape.function_context(function, token):
        result = await cape.invoke(echo_enc)
    return result.decode()


if __name__ == "__main__":

    cape = pycape.Cape()
    fref = cape.function(echo_func_file)
    token = cape.token(token_file)
    echo = asyncio.run(main(cape, fref, token, "Welcome to Cape."))
    print(echo)
