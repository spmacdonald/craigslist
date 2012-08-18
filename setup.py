import craigslist
import os

from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='craigslist',
    description='A Python API for searching Craigslist.',
    long_description=read('README'),
    author='Andrew Brookins',
    author_email='a@andrewbrookins.com',
    url='https://github.com/abrookins/craigslist',
    version='0.07',
    packages=['craigslist'],
    install_requires=[
        'BeautifulSoup==3.2.0',
        'requests==0.10.1'
    ]
)
