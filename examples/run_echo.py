import os
import pathlib

from pycape import Cape
from pycape import FunctionRef

if __name__ == "__main__":
    url = os.environ.get("CAPE_HOST", "wss://enclave.capeprivacy.com")
    function_json = os.environ.get("FUNCTION_JSON", "echo_token.json")
    function_json = pathlib.Path(__file__).parent.absolute() / function_json

    function_ref = FunctionRef.from_json(function_json)
    cape = Cape(url=url)
    input = "Welcome to Cape".encode()
    result = cape.run(function_ref, input)

    print(f"The result is: {result.decode()}")
