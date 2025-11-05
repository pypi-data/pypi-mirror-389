import os
from setuptools import setup, find_packages

ver_key = 'SMARTREMOTE_VERSION'
ver_value = '0.1.0'

if ver_key in os.environ:
    ver_value = os.environ[ver_key]

setup(
    name             = 'smartremote',
    version          = ver_value,
    description      = 'Park Systems Python library for SPM',
    author           = 'Park Systems',
    author_email     = 'rsw@parksystems.com',
    url              = 'https://github.com/ParkSystems-RSW/SmartRemote',
    download_url     = '',
    install_requires = [ ],
    packages         = find_packages(),
    keywords         = ['park', 'systems', 'spm', 'afm'],
    python_requires  = '>=3',
    package_data     = { },
    zip_safe         = False,
    classifiers      = []
)
    