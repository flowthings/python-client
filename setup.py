from setuptools import setup

setup(name='flow-things',
      version='0.1.2',
      description='API client for the flow-things.io platform',
      author='flow-things.io',
      author_email='dev@flow.net',
      test_suite='tests',
      package_dir={'flow_things':'flow'},
      packages=['flow_things'],
      install_requires=['requests', 'websocket-client'])
