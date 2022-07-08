import os

from pycape.cape import Cape

if __name__ == "__main__":
    token = os.environ.get("CAPE_TOKEN", None)
    url = os.environ.get("CAPE_HOST", "wss://cape.run")
    cape = Cape(url=url, access_token=token)
    function_id = os.environ.get(
        "CAPE_FUNCTION", "e4c2a674-9c7f-42d3-8ade-63791c16c3c7"
    )
    cape.connect(function_id)

    result = cape.invoke("Hello Cape".encode())
    print(f"The result is: {result.decode()}")

    result = cape.invoke("Hello Gavin".encode())
    print(f"The result is: {result.decode()}")

    result = cape.invoke("Hello Hello".encode())
    print(f"The result is: {result.decode()}")

    cape.close()
