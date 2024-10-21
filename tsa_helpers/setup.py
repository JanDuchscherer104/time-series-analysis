from importlib.resources import read_text

from setuptools import find_packages, setup

setup(
    name="tsa_helpers",
    version="0.1.0",
    author="Jan Duchscherer",
    author_email="duchsche@hm.edu",
    description="A package for time series analysis functionalities",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
