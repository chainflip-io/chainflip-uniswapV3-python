import setuptools

with open("README.md", "r", encoding = "utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "trialpythonuniswapv3",
    version = "0.0.4",
    author = "Chainflip Labs",
    author_email = "albert@chainflip.io",
    description = "Pythonized Uniswap V3",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/chainflip-io/python-uniswap-v3",
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages = ["trialpythonuniswapv3", "trialpythonuniswapv3.src", "trialpythonuniswapv3.src.libraries", "trialpythonuniswapv3.tests"],
    python_requires = ">=3.7"
)