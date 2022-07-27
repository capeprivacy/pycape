"""Installing with setuptools."""
import setuptools

with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pycape",
    version="0.1.0",
    packages=setuptools.find_packages(),
    python_requires=">=3.7",
    license="Apache License 2.0",
    url="https://github.com/capeprivacy/pycape",
    description="The Cape Privacy Python SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Cape Privacy",
    author_email="contact@capeprivacy.com",
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Development Status :: 3 - Alpha",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
        "Topic :: Security :: Cryptography",
    ],
)
