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
    cape.connect(function_ref)
    result = cape.invoke("Hello Cape".encode())
    print(f"The result is: {result.decode()}")
    result = cape.invoke("Hello Gavin".encode())
    print(f"The result is: {result.decode()}")
    result = cape.invoke("Hello Hello".encode())
    print(f"The result is: {result.decode()}")
    cape.close()

    # Note that instead you can use the connection_context
    # context manager which will automatically close the
    # connection and reset websocket connection's states.
    with cape.function_context(function_ref):
        result = cape.invoke("Hello Cape".encode())
        print(f"The result is: {result.decode()}")
        result = cape.invoke("Hello Gavin".encode())
        print(f"The result is: {result.decode()}")
        result = cape.invoke("Hello Hello".encode())
        print(f"The result is: {result.decode()}")
