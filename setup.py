"""Setup."""

from setuptools import setup, find_packages

setup(
    name="aggregate",
    version="0.1",
    packages=find_packages(),
    package_dir={'': '.'},

    install_requires=['dbus-python', 'PyGObject', 'python-jsonrpc'],

    author="Bruno Morais",
    author_email="brunosmmm@gmail.com",
    description="Aggregate network services concentrator",
    scripts=['aggsrv'],
    )
