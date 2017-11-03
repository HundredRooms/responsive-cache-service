#!/usr/bin/env python

from distutils.core import setup


REQUIREMENTS = [
        'apache-libcloud==1.3.0',
        'pycrypto==2.6.1',
]


def echo_requirements():
    for req in REQUIREMENTS:
        print(req)


setup_data = dict(
        name='cache',
        version='1.0',
        description='Predictive cache service',
        author='Hundredrooms',
        author_email='development@hundredrooms.com',
        packages=['cache', 'cache.models'],
        install_requires=REQUIREMENTS,
)


if __name__ == "__main__":
    setup(**setup_data)
