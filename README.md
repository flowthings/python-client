flowthings-python-client
==================

A client libary for [flowthings.io](http://flowthings.io) written in Python.

## Install

```sh
pip install flowthings
```

## Docs

* [Latest](https://flowthings-python-client.readthedocs.org/en/latest/)
* [Stable](https://flowthings-python-client.readthedocs.org/en/stable/)

## Other Resources
* See the [10 Minute Chat Example](https://github.com/flowthings/python-chat-example) project on GitHub
* View the main [Developer Docs](https://flowthings.io/docs/index) for details on the core platform
* See below for example calls:


## Example API Usage:
```py
from flowthings import API, Token, mem

creds = Token(ACCOUNT, TOKEN)
api = API(creds)
flows = api.flow.find(mem.path == '/hello', limit=10)
```
