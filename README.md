flowthings-python-client
==================

```sh
pip install flowthings
```

```py
from flowthings import API, Token, mem

creds = Token(ACCOUNT, TOKEN)
api = API(creds)
flows = api.flow.find(mem.path == '/hello', limit=10)
```
