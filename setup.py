from setuptools import setup, find_packages
import sys, os

README = open('README.rst').read()

setup(name='piescraper',
    version='0.1',
    description='',
    long_description=README,
    long_description_content_type='text/markdown',
    classifiers=[],
    keywords='',
    author='',
    author_email='',
    url='E:\CPs\Projects\version-control\Ongoing',
    license='MIT',
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[]
)