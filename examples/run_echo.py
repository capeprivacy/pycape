import pathlib

from pycape import Cape

token_file = pathlib.Path(__file__).parent.absolute() / "capedocs.token"

cape = Cape()
fref = cape.function("capedocs/echo")
token = cape.token(token_file)

if __name__ == "__main__":
    input_msg = "Welcome to Cape".encode()
    result = cape.run(fref, token, input_msg)
    print(f"The result is: {result.decode()}")
