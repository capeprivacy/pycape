import os

from pycape import Cape

if __name__ == "__main__":
    token = os.environ.get("CAPE_TOKEN", None)
    url = os.environ.get("CAPE_HOST", "wss://hackathon.capeprivacy.com")
    function_id = os.environ.get(
        "CAPE_FUNCTION", "e4c2a674-9c7f-42d3-8ade-63791c16c3c7"
    )

    cape = Cape(url=url, access_token=token)
    input = "Welcome to Cape".encode()
    input2 = "Welcome to Yann".encode()

    result = cape.run(function_id, input, input2, use_serdio=True)

    print(f"The result is: {result[0].decode()}, {result[1].decode()}")
