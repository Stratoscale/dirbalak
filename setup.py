import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="dirbalak",
    version="1.0",
    author="Shlomo Matichin",
    author_email="shlomi@stratoscale.com",
    description=(
        "Dirbalak is a CI build system"),
    keywords="git repos repositories python scm continuous integration CI",
    url="http://packages.python.org/dirbalak",
    packages=['dirbalak'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
    ],
    install_requires=[
        "upseto",
        "solvent",
    ],
)
