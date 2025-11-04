from setuptools import setup, find_packages
import pathlib

# The directory containing this file
here = pathlib.Path(__file__).parent.resolve()

# Long description from README.md
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="livestack",  # package name on PyPI
    version="0.5.0",
    description="Live minimal inline stack display for Python scripts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/viljan1/LiveStack-py",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),  # automatically include all packages under 'livestack'
    python_requires=">=3.7",
    include_package_data=True,  # include files specified in MANIFEST.in
)