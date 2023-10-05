import os

from pycape.llms import Cape

url = os.getenv("CAPE_URL", "https://api.capeprivacy.com")
c = Cape(url=url)

token = c.token(os.getenv("CAPE_TOKEN", ""))

for msg in c.chat_completions(
    [
        {
            "role": "user",
            "content": "What is the Capital of France?",
        },
        {"role": "system", "content": "you are a happy helpful assistant"},
    ],
    token,
    max_tokens=1000,
    temperature=0.8,
):
    print(msg)


for msg in c.completions(
    "<|im_start|>system\nYou are a helpful Assistant.<|im_end|>\n<|im_start|>user\nWhat is the Capital of France?<|im_end|>\n<|im_start|>assistant",
    token,
    max_tokens=16,
    temperature=0.8,
):
    print(msg)
