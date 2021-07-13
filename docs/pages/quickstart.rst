.. _quickstart:

**********
Quickstart
**********

Execute this snippet to authenticate with Capella's Console API and search, order and download a random product.


.. code:: python3

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
      override=True,
      threaded=True,
      show_progress=True
  )


Intrigued? 

Check out the many examples in :ref:`example_usage` and the :ref:`api-reference`.