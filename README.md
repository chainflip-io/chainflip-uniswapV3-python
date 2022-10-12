## Python-uniswap-v3
Pythonized Uniswap v3

## Dependencies

- Python >=3.7.3, <3.10
For Ubuntu `sudo apt-get install python3 python-dev python3-dev build-essential`
- [Poetry (Python dependency manager)](https://python-poetry.org/docs/)


## Setup

First, ensure you have [Poetry](https://python-poetry.org) installed

```bash
git clone git@github.com:chainflip-io/python-uniswap-v3.git
cd python-uniswap-v3
poetry shell
poetry install
```

### Running Tests

We use pytest to run the tests.

```bash
pytest
pytest <test-name>
```
