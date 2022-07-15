# PyCape Contribution Guide

This document outlines how to install and set up the `pycape` library for local development.

## Style Guide
We use [Black](https://github.com/psf/black) to avoid thinking about most code style choices.
For all other style questions, we follow
[Google's styleguide for Python](https://google.github.io/styleguide/pyguide.html).

## Local development

This section describes how to set up your local environment so you can develop and test `pycape`.

### Prerequisites

* Python 3.8+
* [pip](https://pip.pypa.io/en/stable/installing/)

### Install and set up

Clone the repo:

```sh
git clone https://github.com/capeprivacy/pycape.git
```

Next install the library and all of its dependencies:

```sh
make install
```

### Testing

We use the [`pytest`](https://docs.pytest.org/en/7.1.x/) framework to run unittests in `pycape`.

To run the test suite invoke `pytest` with:

```sh
make test
```


### Developing

To ensure your changes will pass our CI, it's wise to run the following commands before committing:

```sh
make ci-ready

# or, more verbosely:

make fmt
make lint
make test-ci
```