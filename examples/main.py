import os

from pycape import Cape

if __name__ == "__main__":
    token = os.environ["CAPE_TOKEN"]
    url = os.environ.get("CAPE_HOST", "wss://cape.run")
    function_id = os.environ.get(
        "CAPE_FUNCTION", "9f1f7e5b-6a84-4196-a70c-c86024d088c8"
    )

    cape = Cape(url=url, token=token)
    input = 20
    result = cape.run(function_id, input)

    print(f"The result is: {result}")
