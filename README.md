# 🛰️ capella-console-client 🐐

[![Version](https://img.shields.io/pypi/v/capella-console-client.svg)](https://pypi.org/project/capella-console-client/)
[![License](https://img.shields.io/pypi/l/capella-console-client.svg)](#)
[![CI](https://github.com/capellaspace/console-client/workflows/ci.yml/badge.svg)](#)
[![Coverage](https://coveralls.io/repos/github/capellaspace/console-client/badge.svg?branch=main)](https://coveralls.io/repos/github/capellaspace/console-client/badge.svg?branch=main)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/capella-console-client.svg)](https://pypi.org/project/capella-console-client/)
[![Documentation](https://readthedocs.org/projects/capella-console-client/badge/?version=latest)](https://capella-console-client.readthedocs.io/en/latest/?badge=latest)

Python SDK for api.capellaspace.com (search, order, download)


## installation

```bash
pip install capella-console-client
```

## Usage


```python
from capella_console_client import CapellaConsoleClient
from getpass import getpass

# user credentials on console.capellaspace.com
email = input('console user (user@email.com): ').strip() 
pw = getpass('console password: ').strip()  

# authenticate
client = CapellaConsoleClient(
    email=email, 
    password=pw,
    verbose=True
)

# search 
stac_items = client.search(
    instrument_mode="spotlight",
    product_type__in=["SLC", "GEO"],
    limit=2
)

# order
order_id = client.submit_order(items=stac_items)

# download
product_paths = client.download_products(
    order_id=order_id, 
    local_dir='/tmp',
    include=['thumbnail', 'raster', 'metadata'],
    override=True,
    threaded=True,
    show_progress=True
)
```



## Documentation

The documentation for `capella_console_client` can be found [here](https://capella-console-client.readthedocs.io/en/latest/?badge=latest).

## Support

Please [open an issue](https://github.com/capellaspace/console-client/issues/new)
with enough information for us to reproduce your problem.
A [minimal, reproducible example](https://stackoverflow.com/help/minimal-reproducible-example)
would be very helpful.

## Contributing

Contributions are very much welcomed and appreciated. See [how to contribute](https://capella-console-client.readthedocs.io/en/stable/pages/contributors.html) for more information.


## License
Licensed under the [MIT License](https://github.com/capellaspace/console-client/blob/master/LICENSE)

• Copyright 2021 • Capella Space •


## TODO

* token refresh