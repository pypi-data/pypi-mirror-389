#!/usr/bin/env python
# -*- coding: utf8 -*-
import os
from io import open
from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), "r", encoding="utf-8") as fobj:
    long_description = fobj.read()

requires = []
with open(os.path.join(here, "requirements.txt"), "r", encoding="utf-8") as fobj:
    requires += [x.strip() for x in fobj.readlines() if x.strip()]

setup(
    name="globallock",
    version="0.1.4",
    description="Distributed lock manager, support many types of backend, e.g. redis, django-redis, etcd, zookeeper...",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="rRR0VrFP",
    maintainer="rRR0VrFP",
    python_requires=">=3.6",
    license="MIT",
    license_files=("LICENSE",),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords=[
        "global lock",
        "distributed lock",
        "redis lock",
        "django redis lock",
        "zookeeper lock",
        "etcd lock",
    ],
    install_requires=requires,
    packages=find_packages(
        ".",
        exclude=[
            "tests",
            "django_redis_global_lock_demo",
            "django_redis_global_lock_example",
            "django_redis_global_lock_example.migrations",
        ],
    ),
    zip_safe=False,
    include_package_data=True,
)
