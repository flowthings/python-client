from setuptools import setup

setup(name='flowthings',
      version='0.1.3',
      description='API client for the flowthings.io platform',
      author='flowthings.io',
      author_email='dev@flowthings.io',
      test_suite='tests',
      packages=['flowthings'],
      install_requires=['requests', 'websocket-client'])
