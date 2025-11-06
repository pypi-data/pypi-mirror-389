# murmur

A simple Python library for access to a YAML formatted password file.
It's a Python port of the go-murmur Go library.

## Installation
```bash
pip install pymurmur
```

## How to use it

```
$ cat ~/.murmur.yaml
fooapp: topsecret
barapp: hunter3

$ cat murmur.py
from murmur import Murmur
m = Murmur()
print(m.Lookup("barapp"))

$ ./murmur.py
val=hunter3
```

## Author

Mike Schilli, m@perlmeister.com 2025

## License

Released under the [Apache 2.0](LICENSE)
