import asyncio
import os

from pycape.cape import Cape

if __name__ == "__main__":
    token = os.environ["CAPE_TOKEN"]
    url = os.environ.get("CAPE_HOST", "wss://cape.run")
    cape = Cape(url=url, token=token)
    cape.connect("e4c2a674-9c7f-42d3-8ade-63791c16c3c7")
    result = cape.invoke("Hello Cape")
    print(f"The result is: {result}")
    result = cape.invoke("Hello Gavin")
    print(f"The result is: {result}")
    cape.close()
