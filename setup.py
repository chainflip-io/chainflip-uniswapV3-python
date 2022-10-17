import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pythonUniswapV3",
    version="0.0.1",
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
        "pythonUniswapV3",
        "pythonUniswapV3.src",
        "pythonUniswapV3.src.libraries",
        "pythonUniswapV3.tests",
    ],
    python_requires=">=3.7",
)
