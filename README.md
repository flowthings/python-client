flowthings-python-client
==================

```sh
pip install flow-things
```

```py
from flow_things import API, Token, mem

creds = Token(ACCOUNT, TOKEN)
api = API(creds)
flows = api.flow.find(mem.path == '/hello', limit=10)
```
