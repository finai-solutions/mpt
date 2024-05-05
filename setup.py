import os

from setuptools import setup

cwd = os.path.dirname(os.path.realpath(__file__))
file = os.path.join(cwd, 'requirements.txt')
with open(file) as f:
    dependencies = list(map(lambda x: x.replace("\n", ""), f.readlines()))

with open("README.md", 'r') as f:
    long_description = f.read()

setup(name='mpt',
      version='0.1.0',
      description='modern portfolio theory in crypto',
      long_description=long_description,
      author='mohab metwaly',
      author_email='mohab-metwally@riseup.net'
      license='GPL-3.0'
      url='https://github.com/finai-solutions/mpt',
      install_requires=dependencies,
      packages=['mpt'])
