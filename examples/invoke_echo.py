import pathlib

from pycape import Cape

token_file = pathlib.Path(__file__).parent.absolute() / "user.token"

cape = Cape()
function_ref = cape.function("pycape-dev/echo")
token = cape.token(token_file)


if __name__ == "__main__":
    cape.connect(function_ref, token)
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
    with cape.function_context(function_ref, token):
        result = cape.invoke("Hello Cape".encode())
        print(f"The result is: {result.decode()}")
        result = cape.invoke("Hello Gavin".encode())
        print(f"The result is: {result.decode()}")
        result = cape.invoke("Hello Hello".encode())
        print(f"The result is: {result.decode()}")
