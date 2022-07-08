import os

from pycape import Cape

if __name__ == "__main__":
    token = os.environ.get("CAPE_TOKEN", None)
    url = os.environ.get("CAPE_HOST", "wss://cape.run")
    function_id = os.environ.get(
        "CAPE_FUNCTION", "e4c2a674-9c7f-42d3-8ade-63791c16c3c7"
    )

    cape = Cape(url=url, access_token=token)
    input = "Welcome to Cape".encode()
    result = cape.run(function_id, input)

    print(f"The result is: {result.decode()}")
