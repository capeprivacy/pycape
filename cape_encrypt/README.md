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
    plaintext = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
    ciphertext = encrypt(plaintext)
    decrypted = decrypt(ciphertext)
    if plaintext != decrypted:
        raise Exception('Decrypted payload did not match plaintext')
    return 'Woohoo!'
```
