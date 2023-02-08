import pathlib

from pycape import Cape

token_file = pathlib.Path(__file__).parent.absolute() / "user.token"

cape = Cape()
function_ref = cape.function("pycape-dev/echo")
token = cape.token(token_file)

if __name__ == "__main__":
    input_msg = "Welcome to Cape".encode()
    result = cape.run(function_ref, token, input_msg)
    print(f"The result is: {result.decode()}")
