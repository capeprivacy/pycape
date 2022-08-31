<!-- markdownlint-disable -->

# API Overview

## Modules

- [`serdio`](./serdio.md#module-serdio)
- [`serdio.io_lifter`](./serdio.io_lifter.md#module-serdioio_lifter): Tools for lifting normal Python functions into Cape handlers.
- [`serdio.io_lifter_test`](./serdio.io_lifter_test.md#module-serdioio_lifter_test)
- [`serdio.serde`](./serdio.serde.md#module-serdioserde)
- [`serdio.serde_test`](./serdio.serde_test.md#module-serdioserde_test)

## Classes

- [`io_lifter.IOLifter`](./serdio.io_lifter.md#class-iolifter)
- [`io_lifter_test.TestIoLifter`](./serdio.io_lifter_test.md#class-testiolifter)
- [`serde.SerdeHookBundle`](./serdio.serde.md#class-serdehookbundle): SerdeHookBundle(encoder_hook: Callable, decoder_hook: Callable)
- [`serde_test.SerializeTest`](./serdio.serde_test.md#class-serializetest)

## Functions

- [`io_lifter.lift_io`](./serdio.io_lifter.md#function-lift_io): Lift a function into a callable that abstracts input-output (de-)serialization.


---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
