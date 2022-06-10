import asyncio
import base64
import json
import pathlib

import websockets


def add(x):
    return x + 1


async def enclave_run(websocket):
    request = await websocket.recv()
    request = json.loads(request)
    token = request["auth_token"]
    nonce = request["nonce"]
    print(f"Authenticate with token {token} and nonce {nonce}")

    fixture_dir = pathlib.Path(__file__).parent.parent / "pycape/fixture/"
    with open(fixture_dir / "attestation_example.bin", "rb") as f:
        attestation = f.read()

    await websocket.send(attestation)
    print("Attestation sent")

    input = await websocket.recv()
    input = 1
    print(f"Input received: {input}")

    input = int(input)

    output = add(input)
    print(f"Computed result: {output}")
    result = {}
    result["results"] = {
        "data": base64.b64encode(input.to_bytes(2, "big")).decode("utf-8"),
        "stderr": base64.b64encode("yo".encode()).decode("utf-8"),
    }

    await websocket.send(json.dumps(result))
    print("Result sent")


async def main():
    async with websockets.serve(enclave_run, "localhost", 8765):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
