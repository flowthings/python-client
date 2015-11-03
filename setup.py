from setuptools import setup

setup(name='flowthings',
      version='1.0.5',
      description='API client for the flowthings.io platform',
      author='flowthings',
      author_email='dev@flowthings.io',
      url='https://github.com/flowthings/python-client',
      test_suite='tests',
      packages=['flowthings'],
      install_requires=['requests', 'websocket-client', 'six'])
