.. _example_usage:

**************
Example Usage
**************

authenticate
############

.. code:: python3

    from getpass import getpass
    from capella_console_client import CapellaConsoleClient

    email = input("your email on console.capellaspace.com:").strip()
    pw = getpass("your password on console.capellaspace.com:").strip()

    # authenticate with api.capellaspace.com
    client = CapellaConsoleClient(email=email, password=pw)

    # chatty client
    client = CapellaConsoleClient(email=email, password=pw, verbose=True)


    # already have a valid JWT token? no problem
    token_client = CapellaConsoleClient(token='<MOCK_TOKEN>', verbose=True)

    # don't want to validate the token (saves an API call)
    bold_token_client = CapellaConsoleClient(token='<MOCK_TOKEN>', no_token_check=True)


search
######

.. code:: python3

    # random capella product
    random_product = client.search(constellation="capella", limit=1)[0]

    # stack of same bounding box
    stack_by_bbox = client.search(bbox=random_product['bbox'])

    # capella spotlight
    capella_spotlight = client.search(
        constellation="capella", 
        instrument_mode="spotlight", 
        limit=1)[0]

    # capella spotlight roma
    roma_bbox = [12.35, 41.78, 12.61, 42]

    capella_spotlight_roma = client.search(
        constellation="capella",
        instrument_mode="spotlight", 
        bbox=roma_bbox
    )
    print(f"Found {len(capella_spotlight_roma)} spotlight products over roma")

    # capella spotlight roma GEO product
    capella_spotlight_roma_geo = client.search(
        constellation="capella",
        instrument_mode="spotlight", 
        bbox=roma_bbox,
        product_type="GEO"
    )
    print(f"Found {len(capella_spotlight_roma_geo)} spotlight GEO products over roma")


advanced search
###############

The API for advanced filtering operations was inspired by `Django's ORM <https://docs.djangoproject.com/en/3.2/topics/db/queries/#chaining-filters>`_

.. code:: python3

    # sorted search desc by datetime
    vvs = client.search(
        polarizations='VV',
        platform='capella-2',
        sortby='-datetime'
    )

    # sorted search desc by datetime and 2nd ascending by id
    vvs = client.search(
        polarizations='VV',
        platform='capella-2',
        sortby=['-datetime', '+id']
    ) 

    # get 10 SLC stripmap products collected in 01/2021 
    capella_sm_01_2021 = client.search(
        instrument_mode="stripmap",
        datetime__lt="2021-02-01T00:00:00Z",
        datetime__gt="2021-01-01T00:00:00Z",
        product_type="SLC",
        limit=10, 
    )

    # get 10 SLC stripmap or spotlight products with 
    capella_sm_or_sp = client.search(
        instrument_mode__in=["stripmap", "spotlight"],
        product_type="SLC",
        limit=10, 
    )

    # get 10 products with azimuth resolution <= 0.5 AND range resolution between 0.3 and 0.5
    capella_sm_or_sp_hq = client.search(
        resolution_azimuth__lte=0.5,
        resolution_range__gte=0.3,
        resolution_range__lte=0.5,
        limit=10, 
    )

    # get 10 GEO sliding spotlight products with look angle > 35
    plus35_lookangle_sliding_spotlight = client.search(
        look_angle__gt=35,
        product_type="GEO",
        instrument_mode="sliding_spotlight",
        limit=10
    )

find all supported filters in the docstring of `client.search`


order
#####

.. code:: python3

    capella_spotlight_roma_geo_stac_ids = [feat['id'] for feat in capella_spotlight_roma_geo]

    # submit_order
    order_id = client.submit_order(stac_ids=capella_spotlight_roma_geo_stac_ids)
    print(f'order id: {order_id}')

    # get pressigned asset urls of that order
    assets_presigned = client.get_presigned_assets(order_id)

    # alternatively presigned assets can also be filtered - e.g. give me the presigned assets of 3 stac items within the order
    assets_presigned = client.get_presigned_assets(order_id,
                                                stac_ids=capella_spotlight_roma_geo_stac_ids[:3])

    # list all active orders
    all_orders = client.list_orders(is_active=True)

    # list specific order(s) by order id 
    specific_order_id = all_orders[0]['orderId']
    specific_orders = client.list_orders(order_ids=[specific_order_id])

    # alternatively check prior to ordering if order already exists
    order_id = client.submit_order(stac_ids=capella_spotlight_roma_geo_stac_ids,
                                check_active_orders=True)


download multiple products
##########################

.. code:: python3

    product_paths = client.download_products(assets_presigned, local_dir='/tmp', threaded=True)


download single product
#######################


.. code:: python3

    assets_presigned = client.get_presigned_assets(order_id)

    # you can also download a specific product with download_product (SINGULAR)
    product_paths = client.download_product(assets_presigned[0], local_dir='/tmp', override=True)

    # 🕒 don't like waiting? 🕒 - set threaded = True in order to fetch the product assets in parallel
    product_paths = client.download_product(assets_presigned, local_dir='/tmp', override=True, threaded=True)

    # ⌛ like to watch progress bars? ⌛ - set show_progress = True in order to get feedback on download status (time remaining, transfer stats, ...)
    product_paths = client.download_product(assets_presigned, local_dir='/tmp', override=True, threaded=True, show_progress=True)


Output
.. code:: bash

    2021-06-21 20:28:16,734 - 🛰️  Capella Space 🐐 - INFO - downloading product CAPELLA_C03_SP_SLC_HH_20210621202423_20210621202425 to /tmp
    CAPELLA_C03_SP_SLC_HH_20210621202423_20210621202425.tif             ━━━━━━━━━━━━━━╸━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 18.7%  • 68.3/366.1 MB  • 8.4 MB/s  • 0:00:38
    CAPELLA_C03_SP_GEO_HH_20210621202413_20210621202435_preview.tif     ━━━━━━━━━━━━━━━━━━━━━━━━━━━╺━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 34.4%  • 49.1/142.7 MB  • 8.7 MB/s  • 0:00:12
    


download single asset
#####################

.. code:: python3
    
    # download thumbnail
    thumb_presigned_href = assets_presigned[0]['thumbnail']['href']
    dest_path = '/tmp/thumb.png'
    local_thumb_path = client.download_asset(thumb_presigned_href, local_path=dest_path)

    # assets are saved into OS specific temp directory if `local_path` not provided
    raster_presigned_href = assets_presigned[0]['HH']['href']
    local_raster_path = client.download_asset(raster_presigned_href)
    print(local_raster_path)
    from pathlib import Path
    assert local_thumb_path == Path(dest_path)

    # the client is respectful of your local files and does not override them by default ...
    local_thumb_path = client.download_asset(thumb_presigned_href, local_path=dest_path)

    # ... but can be instructed to do so
    local_thumb_path = client.download_asset(thumb_presigned_href, local_path=dest_path, override=True)



download with asset type filter
###############################

.. code:: python3

    # download only thumbnails
    product_paths = client.download_products(assets_presigned, include=["thumbnail"], local_dir='/tmp', threaded=True)

    # can also be a string if only one provided
    product_paths = client.download_products(assets_presigned, include="thumbnail", local_dir='/tmp', threaded=True)

    # download only raster (VV or HH)
    product_paths = client.download_products(assets_presigned, include=["raster"], local_dir='/tmp', threaded=True)

    # download all assets except HH
    product_paths = client.download_products(assets_presigned, exclude=["HH"], local_dir='/tmp', threaded=True)

    # explicit DENY overrides explicit ALLOW --> the following would only fetch all thumbnails
    product_paths = client.download_products(assets_presigned, include=["HH", "thumbnail"], exclude=["HH"], local_dir='/tmp', threaded=True)


tasking requests
################

.. code:: python3

    task_request_id = '27a71826-7819-48cc-b8f2-0ad10bee0f97'  # provide valid tasking_request_id

    # get task info
    task = client.get_task(task_request_id)

    # was it completed ?
    client.is_task_completed(task)

    # given that task request id, download all associated products
    client.download_products_for_task(task_request_id, local_dir='/tmp', threaded=True)


read imagery
############

requires rasterio (not part of this package)

.. code:: python3

    import rasterio

    # read metadata
    raster_presigned_href = assets_presigned[0]['HH']['href']
    with rasterio.open(raster_presigned_href) as ds:
        print(ds.profile)

    # read chunk of full raster
    with rasterio.open(raster_presigned_href) as ds:
        chunk = ds.read(1, window=rasterio.windows.Window(2000, 2000, 7000, 7000)) 
    print(chunk.shape)
        
    # read thumbnail
    thumb_presigned_href = assets_presigned[0]['thumbnail']['href']
    with rasterio.open(thumb_presigned_href) as ds:
        thumb = ds.read(1)
    print(thumb.shape)
