import importlib

import setuptools

PACKAGE = "pyoseo"
NAME = "pyoseo"
DESCRIPTION = "A Django project that provides an OGC OSEO server"
AUTHOR = "Ricardo Garcia Silva"
AUTHOR_EMAIL = "ricardo.garcia.silva@gmail.com"
URL = "https://github.com/pyoseo/pyoseo"
VERSION = "0.5"

setuptools.setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=open("README.rst").read(),
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license="Apache",
    url=URL,
    package_dir = {"": "pyoseo"},
    packages=setuptools.find_packages("pyoseo"),
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Framework :: Django",
        ],
    install_requires=[
        "django",
        "django-grappelli",
        "django-mail-queue",
        "django-sendfile",
        "pathlib2",
    ],
    zip_safe=False,
)
