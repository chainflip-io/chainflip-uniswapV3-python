import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="uniswapV3Python",
    version="1.0.0",
    author="Chainflip Labs",
    author_email="albert@chainflip.io",
    description="Pythonized Uniswap V3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chainflip-io/python-uniswap-v3",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=[
        "uniswapV3Python",
        "uniswapV3Python.src",
        "uniswapV3Python.src.libraries",
        "uniswapV3Python.tests",
    ],
    python_requires=">=3.7",
)
