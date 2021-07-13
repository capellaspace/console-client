# 🛰️ capella-console-client 🐐
Python SDK for api.capellaspace.com (search, order, download)


## installation

```bash
pip install capella-console-client
```

## Usage


```python
from capella_console_client import CapellaConsoleClient
from getpass import getpass

# user creds
email = input('console user (user@capellaspace.com): ').strip() 
pw = getpass('console password: ').strip()  

# auth
client = CapellaConsoleClient(
    email=email, 
    password=pw,
    verbose=True
)

# search
capella_stac_items = client.search(
    constellation="capella",
    instrument_mode="spotlight",
    product_type__in=["SLC", "GEO"],
    limit=2
)

# order
order_id = client.submit_order(items=capella_stac_items)

# download
assets_presigned = client.get_presigned_assets(order_id)
product_paths = client.download_products(
    assets_presigned, 
    local_dir='/tmp',
    include=['thumbnail', 'raster', 'metadata'],
    override=True,
    threaded=True,
    show_progress=True
)
```



## Documentation

Documentation for `capella_console_client` is available [here](TODO).

## Support

Please [open an issue](https://github.com/capellaspace/console-client/issues/new)
with enough information for us to reproduce your problem.
A [minimal, reproducible example](https://stackoverflow.com/help/minimal-reproducible-example)
would be very helpful.

## Contributing

Contributions are very much welcomed and appreciated. Head over to the documentation on [how to contribute](TODO).


## License
Licensed under the [MIT License](https://github.com/capellaspace/console-client/blob/master/LICENSE)

• Copyright 2021 • Capella Space •


## TODO

* token refresh