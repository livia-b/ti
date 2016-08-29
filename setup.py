#!/usr/bin/env python
import io
import sys

from setuptools import find_packages, setup
import ti


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

testing = bool({'pytest', 'test'}.intersection(sys.argv))

setup(
    name="ti",
    version=ti.__version__,
    author="Shrikant Sharat",
    author_email="shrikantsharat.k@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    scripts=[],
    url="http://ti.sharats.me/",
    description="A silly simple time tracker",
    long_description=read('README.rst', 'CHANGES.rst'),
    entry_points={
        'console_scripts': [
            'ti = ti.time_tracking:main',
        ]
    },
    install_requires=[
        "colorama",
        "PyYAML",
        "tabulate"
    ],
    setup_requires=["pytest-runner"] if testing else [],
    tests_require=["pytest", "cram", "pytest-cram"],
    extras_require={
        'docs': ["ghp-import", "pygreen"],
    }
)
