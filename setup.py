from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
    name='extracty',
    version=version,
    description='various utilities to extract metadata from HTML documents',
    author='Andrey Popp',
    author_email='8mayday@gmail.com',
    license='BSD',
    py_modules=['extracty'],
    packages=['justext'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'lxml',
    ],
    package_data={'justext': ['stoplists/*.txt']},
    entry_points="""
    # -*- Entry points: -*-
    [console_scripts]
    extracty-author = extracty:extract_author_command
    """)
