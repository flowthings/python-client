from setuptools import setup

setup(name='flowthings',
      version='1.0.0',
      description='API client for the flowthings.io platform',
      author='flowthings',
      author_email='dev@flowthings.io',
      url='https://github.com/flowthings/python-client',
      download_url='https://github.com/flowthings/python-client/tarball/1.0.0',
      test_suite='tests',
      packages=['flowthings'],
      install_requires=['requests', 'websocket-client'])
