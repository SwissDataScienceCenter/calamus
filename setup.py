# -*- coding: utf-8 -*-

# DO NOT EDIT THIS FILE!
# This file has been autogenerated by dephell <3
# https://github.com/dephell/dephell

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import os.path

readme = ""
here = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(here, "README.rst")
if os.path.exists(readme_path):
    with open(readme_path, "rb") as stream:
        readme = stream.read().decode("utf8")

setup(
    long_description=readme,
    name="calamus",
    version="0.3.4",
    description="calamus is a library built on top of marshmallow to allow (de-)Serialization of Python classes to JSON-LD.",
    python_requires="==3.*,>=3.6.1",
    project_urls={
        "homepage": "https://github.com/SwissDataScienceCenter/calamus/",
        "repository": "https://github.com/SwissDataScienceCenter/calamus/",
    },
    author="Swiss Data Science Center",
    author_email="contact@datascience.ch",
    license="Apache-2.0",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Development Status :: 4 - Beta",
    ],
    packages=["calamus", "calamus.backends"],
    package_dir={"": "."},
    package_data={},
    install_requires=["lazy-object-proxy==1.*,>=1.4.3", "marshmallow==3.*,>=3.5.1", "pyld==2.*,>=2.0.2"],
    extras_require={
        "dev": [
            "black==19.*,>=19.10.0.b0",
            "flake8==3.*,>=3.7.9",
            "pre-commit==2.*,>=2.3.0",
            "pytest==5.*,>=5.2.0",
            "pytest-black==0.*,>=0.3.9",
        ],
        "docs": ["sphinx==3.*,>=3.0.3", "sphinx-rtd-theme==0.*,>=0.4.3", "sphinxcontrib-spelling==5.*,>=5.0.0"],
        "neo4j": ["py2neo[neo4j]==2020.*,>=2020.0.0", "requests[neo4j]==2.*,>=2.24.0"],
    },
)
