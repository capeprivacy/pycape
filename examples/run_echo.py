import os
import pathlib

from pycape import Cape
from pycape import FunctionRef

if __name__ == "__main__":
    url = os.environ.get("CAPE_HOST", "wss://enclave.capeprivacy.com")
    token_file = os.environ.get("TOKEN_FILE", "echo_token.json")
    token_file = pathlib.Path(__file__).parent.absolute() / token_file

    function_ref = FunctionRef.from_json(token_file)
    cape = Cape(url=url)
    input = "Welcome to Cape".encode()
    result = cape.run(function_ref, input)

    print(f"The result is: {result.decode()}")
