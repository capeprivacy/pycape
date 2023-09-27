import os

from pycape.llms import Cape

c = Cape(url="https://api.capeprivacy.com")

token = c.token(os.getenv("CAPE_TOKEN", ""))

for msg in c.chat_completions(
    [
        {
            "role": "user",
            "content": "<s>[INST] <<SYS>>You are a helpful Assistant.<</SYS>>"
            "\n\nWhat is the Capital of France? [/INST]",
        },
        {"role": "system", "content": "you are a happy helpful assistant"},
    ],
    token,
    max_tokens=16,
    temperature=0.8,
):
    print(msg)
