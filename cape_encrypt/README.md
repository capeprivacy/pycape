Cape Encrypt
===========

Ease of use utility to allow functions deployed with [Cape](https://docs.capeprivacy.com/getting-started) to leverage enclave only encryption and decryption. These operations are completed using your account level [Cape Key](https://docs.capeprivacy.com/concepts/encrypt).


## Installation 
```sh
pip install cape_encrypt
```


## Usage

```python
def cape_handler(data):
    plaintext = b"encrypt me"
    ciphertext = encrypt(plaintext)

    print(str(ciphertext))
    # cape:aaMrznPDy8ZrZT7CkRwpzTS9+rG+A4FuFPCfjLTrMa/2TyVvYdEx6PtYHnGizZKOZCytQUuo65OZkw5kQCJpNBuZzmd4lPB9lu0sSGLExPSivzMLKOH07rwrlBFFEEgZCvRoKBDebxVfq/Uv2v++Q4xmn4wksBjpPHjlLtGzpPu9mwMofs5eZLTVqp4g6yCuwaNbPkyhq09iRHiLOvWKhWfkf+0++/W2UDr81PLTdNBKI+kdHoTp/Xr8Uh9ooovwAx3V/LX9ESAHFWeW6BHV6JVcIP/tH1aFjuVVfH610I4eNZdaVyWV9DVdmsUF2o7g2tUmR+Eg++ts7MXxbWRz2PDZC8MDz52w6ZiUVluiluVPRh/VB+TmCJwSIfDQ3fiXAobhU/flA8jmzdE1pC3SdSY30vkqxwLBZ5VwGM4J7p2UsDuKzxZXVJ0Tg6ludB8y0NyZswYXZcewUuc0XZ2sOWCTqSP9t/0b/atGuwUxE5qkwEglP6s5AyVET8AZRH4KPoQuxjFUf7h+NJzZMDd/2Zef+yCGAP/8vKjpglDdItmsX3Bintu+Sp/ij6ynbFARpL9N7YZ8yA2Lpx/59Y/EnCuOdAJOpKcif3bnHNhKsGIATlO/lyY5bXRzGUpbejh+UAQC5qAsLmWQa/HZoF2ptGaGVhLpUs8zIdeLWFZ/YIhUXE1koI/BMMAT05kmaPPDvAELOkWJxpC4VYJWmzPZ29Opv7ye
```
