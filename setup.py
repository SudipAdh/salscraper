from setuptools import setup, find_packages
import sys, os

README = open('README.md').read()

setup(
    name                            = 'salscraper'                              ,
    version                         = '0.0.2'                                   ,
    description                     = 'A scarping tool'                         ,
    long_description                = README                                    ,
    long_description_content_type   = 'text/markdown'                           ,
    classifiers                     = [
          'Development Status :: 3 - Alpha'                                     ,
          'Intended Audience :: Developers'                                     ,
          'License :: OSI Approved :: MIT License'                              ,
          'Operating System :: Microsoft :: Windows'                            ,
          'Programming Language :: Python'                                      ,
          'Topic :: Software Development :: Libraries :: Python Modules'        ],
    keywords                        = 'scrape crawl'                            ,
    author                          = 'saledddar'                               ,
    author_email                    = 'saledddar@gmail.com'                     ,
    url                             = 'https://github.com/Saledddar/salscraper' ,
    license                         = 'MIT'                                     ,
    include_package_data            = True                                      ,
    zip_safe                        = False                                     ,
    packages                        = ['salscraper']                            ,
    package_dir                     = {'': 'src'}                               ,
    install_requires                = ['saltools']                              )
