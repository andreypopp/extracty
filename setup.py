from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
    name='extracty',
    version=version,
    description='various utilities to extract metadata for HTML documents',
    author='Andrey Popp',
    author_email='8mayday@gmail.com',
    license='BSD',
    py_modules=['extracty'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'lxml',
    ],
    entry_points="""
    # -*- Entry points: -*-
    """)
