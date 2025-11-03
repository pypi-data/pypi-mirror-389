from setuptools import setup, find_packages

setup(
    name="linear_regression_ayoub_lab3",     # must be unique on PyPI
    version="1.0.0",
    author="Ayoub Aziba",
    author_email="ma.aziba@esi-sba.dz",
    description="Simple Linear Regression from scratch",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=["numpy"],
    url="https://pypi.org/project/linear-regression-ayoub/",
)
