.. _quickstart:

**********
Quickstart
**********

Execute the following snippet to authenticate with Capella's Console API and **search, order and download** 2 free **open-data** products.

.. code:: python3

  from capella_console_client import CapellaConsoleClient

  # prompts for api key before authenticating
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


**Interested?** Check out the many examples in :ref:`example_usage` and the :ref:`api-reference`.
