from os import path
from setuptools import setup, find_packages

local = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(local, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='miniwdl_viz',
    version='0.0.1',
    description='Tools to translate a WDL file into a mermaid graph',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Chan Zuckerberg Initiative',
    author_email='help@czid.org',
    py_modules=['miniwdl_viz'],
    python_requires='>=3.6',
    install_requires=[
        'requests',
        'miniwdl',
    ],
    entry_points={
        'console_scripts': [
        ],
    },
    packages=["miniwdl_viz"],
)