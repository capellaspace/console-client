.. _quickstart:

**********
Quickstart
**********

Execute this snippet to authenticate with Capella's Console API and **search, order and download** 2 **open-data** products.

.. code:: python3

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
      collections=["capella-open-data"],
      limit=2
  )

  # order
  order_id = client.submit_order(items=stac_items, omit_search=True)

  # download
  product_paths = client.download_products(
      order_id=order_id, 
      local_dir='/tmp',
      include=['thumbnail', 'raster', 'metadata'],
      override=True,
      threaded=True,
      show_progress=True
  )


**Does this look useful**? Check out the many examples in :ref:`example_usage` and the :ref:`api-reference`.