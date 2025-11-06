# -*- coding: utf-8 -*-
import os
from io import open
from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), "r", encoding="utf-8") as fobj:
    long_description = fobj.read()

with open(os.path.join(here, "requirements.txt"), "r", encoding="utf-8") as fobj:
    requires = fobj.readlines()
requires = [x.strip() for x in requires if x.strip()]


setup(
    name="django-simple-tags",
    version="0.6.2",
    description="Collection of simple django tags and filters.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="rRR0VrFP",
    maintainer="rRR0VrFP",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords=["django admin extentions", "django simple tags"],
    install_requires=requires,
    packages=find_packages(
        ".",
        exclude=[
            "django_simple_tags_example",
            "django_simple_tags_example.migrations",
            "django_simple_tags_demo",
        ],
    ),
    py_modules=["django_simple_tags"],
    zip_safe=False,
    include_package_data=True,
)
