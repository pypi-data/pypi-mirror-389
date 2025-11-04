from setuptools import setup
from setuptools import find_packages


VERSION = '2.0.3'

setup(
    name='larry_utils',  # package name
    version=VERSION,  # package version
    description='larry produced utils for projects',  # package description
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    package_data={'': ['map.pkl']},
)
