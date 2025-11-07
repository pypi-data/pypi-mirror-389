import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="x23408359",  # must be unique on PyPI
    version="0.0.1",
    author="Aftab Khan",
    author_email="aftabkhan41.ak92@gmail.com",  # fixed email typo
    description="A Python library for CO2 calculation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AftabKhan41/co2_calculator",  # update to your repo
    packages=setuptools.find_packages(),
    install_requires=[],  # should be a list, not ['']
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
