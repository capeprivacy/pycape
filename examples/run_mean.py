import os
import pathlib

from pycape import Cape
from pycape import FunctionRef

if __name__ == "__main__":
    url = os.environ.get("CAPE_HOST", "wss://enclave.capeprivacy.com")
    function_json = os.environ.get("FUNCTION_JSON", "mean_token.json")
    function_json = pathlib.Path(__file__).parent.absolute() / function_json

    function_ref = FunctionRef.from_json(function_json)
    cape = Cape(url=url)

    x = [1, 2, 3, 4]
    result = cape.run(function_ref, x, use_serdio=True)

    print(f"The mean of x is: {result}")
