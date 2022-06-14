from pycape.cape import Cape
import asyncio
import os

async def run():

    token = os.environ["CAPE_TOKEN"]
    url = os.environ.get("CAPE_HOST", "wss://cape.run")

    cape = Cape(url=url, token=token)

    await cape.connect("e4c2a674-9c7f-42d3-8ade-63791c16c3c7")

    result = await cape.invoke('Hello Cape')
    print(f"The result is: {result}")

    result = await cape.invoke('Hello Gavin')
    print(f"The result is: {result}")

    result = await cape.invoke('Hello Hello')
    print(f"The result is: {result}")

    await cape.close()

if __name__ == "__main__":
    asyncio.run(run())
