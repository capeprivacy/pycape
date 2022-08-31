<!-- markdownlint-disable -->

# API Overview

## Modules

- [`attestation`](./attestation.md#module-attestation)
- [`attestation_test`](./attestation_test.md#module-attestation_test)
- [`cape`](./cape.md#module-cape): The Cape Python client.
- [`cape_test`](./cape_test.md#module-cape_test)
- [`enclave_encrypt`](./enclave_encrypt.md#module-enclave_encrypt)
- [`enclave_encrypt_test`](./enclave_encrypt_test.md#module-enclave_encrypt_test)
- [`function_ref`](./function_ref.md#module-function_ref): A structured representation of a deployed Cape function.

## Classes

- [`attestation_test.TestAttestation`](./attestation_test.md#class-testattestation)
- [`cape.Cape`](./cape.md#class-cape): A websocket client for interacting with enclaves hosting Cape functions.
- [`cape_test.TestCape`](./cape_test.md#class-testcape)
- [`enclave_encrypt_test.TestEnclaveEncryption`](./enclave_encrypt_test.md#class-testenclaveencryption)
- [`function_ref.FunctionAuthType`](./function_ref.md#class-functionauthtype): Enum representing the auth type for a function.
- [`function_ref.FunctionRef`](./function_ref.md#class-functionref): A structured reference to a Cape function.

## Functions

- [`attestation.download_root_cert`](./attestation.md#function-download_root_cert)
- [`attestation.parse_attestation`](./attestation.md#function-parse_attestation)
- [`attestation.verify_attestation_signature`](./attestation.md#function-verify_attestation_signature)
- [`attestation.verify_cert_chain`](./attestation.md#function-verify_cert_chain)
- [`attestation_test.create_attestation_doc`](./attestation_test.md#function-create_attestation_doc)
- [`attestation_test.create_certs`](./attestation_test.md#function-create_certs)
- [`attestation_test.create_cose_1_sign_msg`](./attestation_test.md#function-create_cose_1_sign_msg)
- [`enclave_encrypt.encrypt`](./enclave_encrypt.md#function-encrypt)


---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
