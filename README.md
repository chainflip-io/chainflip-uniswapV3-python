## Pythonized Uniswap V3
This repository contains a pythonized version of the popular Uniswap V3 AMM. It aims to provide a python model of the AMM with a high-level of accuracy.
It intends to mimicks the Solidity implementation with no further optimizations. This is because the goal is not to make an optimized model but rather to mirror the original code to allow for easy debugging and further development. Therefore, only a few abstractions have been made for a more comprehensible and simplified model - e.g. using Python dictionary features instead of the BitMap library in Solidity.


## Dependencies

- Python >=3.7.3, <3.10
For Ubuntu `sudo apt-get install python3 python-dev python3-dev build-essential`
- [Poetry (Python dependency manager)](https://python-poetry.org/docs/)


## Setup

First, ensure you have [Poetry](https://python-poetry.org) installed.

```bash
git clone git@github.com:chainflip-io/python-uniswap-v3.git
cd python-uniswap-v3
poetry shell
poetry install
```

### Running Tests

Pytest is used to run the tests.

```bash
pytest
pytest <test-name>
```

### Package Installation
This model has been included in a Python package that can be easily installed via any Python package manager.

Via Pip:

`pip install -i https://test.pypi.org/simple/ uniswapV3Python`

Via Poetry:

`poetry add uniswapV3Python`