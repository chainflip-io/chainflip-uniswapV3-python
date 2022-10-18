## Pythonized Uniswap V3
This repository contains a pythonized version of the popular Uniswap V3 AMM. 

The goal of this model is not to optimize the original design but rather to mirror the code and allow for easy debugging and further development. Therefore, only a few abstractions have been made for a more comprehensible and simplified model - e.g. using Python dictionary features instead of the BitMap library in Solidity.

This implementation achieves a very high-accuracy model of the original Solidity code and it also includes the full testset.


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
To be able to easily use this code outside the repository itself, it has been included in a Python package that can be easily installed via any Python package manager.

Via Pip:

`pip install -i https://test.pypi.org/simple/ uniswapV3Python`

Via Poetry:

`poetry add uniswapV3Python`