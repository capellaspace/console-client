# 🛰️ capella-console-client 🐐

[![Version](https://img.shields.io/pypi/v/capella-console-client.svg)](https://pypi.org/project/capella-console-client/)
[![License](https://img.shields.io/pypi/l/capella-console-client.svg)](#)
[![CI](https://github.com/capellaspace/console-client/workflows/CI/badge.svg)](#)
[![Coverage](https://coveralls.io/repos/github/capellaspace/console-client/badge.svg?branch=main)](https://coveralls.io/github/capellaspace/console-client)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/capella-console-client.svg)](https://pypi.org/project/capella-console-client/)
[![Documentation](https://readthedocs.org/projects/capella-console-client/badge/?version=main)](https://capella-console-client.readthedocs.io)

Python SDK for api.capellaspace.com (search, order, download)


## Installation

```bash
pip install capella-console-client
```

## Requirements

* python >= 3.6
* `capella-console-client` requires an active account on [console.capellaspace.com](https://console.capellaspace.com/). Sign up for an account at [https://www.capellaspace.com/community/](https://www.capellaspace.com/community/).


## Usage

![Quickstart](docs/images/quickstart.gif)

```python
from capella_console_client import CapellaConsoleClient

# you will be prompted for console user (user@email.com)/ password before authenticating
client = CapellaConsoleClient(
    verbose=True
)

# search for 2 open-data products
stac_items = client.search(
    instrument_mode="spotlight",
    product_type__in=["SLC", "GEO"],
    collections=["capella-open-data"],
    limit=2
)

# order
order_id = client.submit_order(items=stac_items, omit_search=True)

# download
product_paths = client.download_products(
    order_id=order_id, 
    local_dir='/tmp',
    show_progress=True
)
```


## Documentation

The documentation for `capella-console-client` can be found [here](https://capella-console-client.readthedocs.io).

## 🧙‍ capella-console-wizard 🧙‍♂️
starting with `capella-console-client>=0.8.0` the SDK ships with an interactive wizard-like CLI: `capella-console-wizard` 

### Installation
```
pip install capella-console-client[wizard]
```

### Usage
```
capella-console-wizard --help
```

see 


## Support

Please [open an issue](https://github.com/capellaspace/console-client/issues/new)
with enough information for us to reproduce your problem.
A [minimal, reproducible example](https://stackoverflow.com/help/minimal-reproducible-example)
would be very helpful.

## Contributing

Contributions are very much welcomed and appreciated. See [how to contribute](https://capella-console-client.readthedocs.io/en/main/pages/contributors.html) for more information.


## License
• Licensed under the [MIT License](https://github.com/capellaspace/console-client/blob/master/LICENSE) • Copyright 2021 • Capella Space •
