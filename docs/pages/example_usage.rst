.. _example_usage:

**************
Example Usage
**************

.. code:: python3

    from capella_console_client import CapellaConsoleClient

authenticate
############

interactive prompt
******************

.. code:: python3

    # you will be prompted for console user (user@email.com)/ password before authenticating
    client = CapellaConsoleClient()

    # chatty client
    client = CapellaConsoleClient(verbose=True)


provide user credentials
************************

.. code:: python3

    from getpass import getpass

    # user credentials on api.capellaspace.com
    email = input("your email on api.capellaspace.com:").strip()
    pw = getpass("your password on api.capellaspace.com:").strip()

    # authenticate with user and password
    client = CapellaConsoleClient(email=email, password=pw)


JWT
***

.. code:: python3

    # already have a valid JWT token? no problem
    token_client = CapellaConsoleClient(token="<token>", verbose=True)

    # don't want to validate the token (saves an API call)
    bold_token_client = CapellaConsoleClient(token="<token>", no_token_check=True)


token refresh with auto retry
*****************************

.. code:: python3

    # issued access tokens have an expiration of 1h
    client = CapellaConsoleClient(email=email, password=pw, verbose=True)

    # DON'T RUN THIS ;)
    import time
    time.sleep(60 * 60)
    # token expired in the interim

    # capella-console-client will refresh your access token and retry the failed request
    me = client.whoami()
    assert me is not None
    print("All good")


Output

.. code:: sh

    2021-10-07 11:00:24,590 - 🛰️  Capella Space 🐐 - INFO - successfully authenticated as user@capellaspace.com
    2021-10-07 11:00:24,690 - root - ERROR - Request: GET https://api.capellaspace.com/user - Status 401 - Response: {'error': {'message': 'Invalid token.', 'code': 'INVALID_TOKEN'}}
    2021-10-07 11:00:24,690 - 🛰️  Capella Space 🐐 - INFO - refreshing access token
    All good


search
######

searches are run against Capella Space's Catalog and a List of `STAC items <https://stacspec.org/>`_ matching the search criteria is returned.

.. code:: python3

    # random
    random_product = client.search(constellation="capella", limit=1)[0]

    # intersecting same bounding box
    stack_by_bbox = client.search(
        bbox=random_product["bbox"]
    )

    # spotlight
    capella_spotlight = client.search(
        constellation="capella",
        instrument_mode="spotlight",
        limit=1
    )[0]

    # capella spotlight GEO over Olympic National Park, Washington State
    olympic_NP_bbox = [-122.4, 46.9, -124.9, 48.5]

    capella_spotlight_olympic_NP_geo = client.search(
        constellation="capella",
        instrument_mode="spotlight",
        bbox=olympic_NP_bbox,
        product_type="GEO"
    )


By default **up to 500** STAC items are returned. This can be increased by providing a custom ``limit``:

.. code:: python3

    many_products = client.search(constellation="capella", limit=1000)


Expensive searches (time is $$)  can be sped up by providing `threaded=True`:

.. code:: python3

    many_products = client.search(constellation="capella", limit=9999, threaded=True)



search fields
*************

.. list-table:: supported fields for search
    :widths: 30 40 20 20
    :header-rows: 1

    * - field name
      - description
      - type
      - example
    * - ``bbox``
      - bounding box
      - ``List[float, float, float, float]``
      - ``[12.35, 41.78, 12.61, 42]``
    * - ``billable_area``
      - billable Area (m^2)
      - ``int``
      - ``100000000``
    * - ``center_frequency``
      - center Frequency (GHz)
      - ``Union[int, float]``
      - ``9.65``
    * - ``collections``
      - STAC collections
      - ``List[str]``
      - ``["capella-open-data"]``
    * - ``collect_id``
      - capella internal collect-uuid
      - ``str``
      - ``"78616ccc-0436-4dc2-adc8-b0a1e316b095"``
    * - ``constellation``
      - constellation identifier
      - ``str``
      - ``"capella"``
    * - ``datetime``
      - mid time of collect in Zulu format
      - ``str``
      - ``"2020-02-12T00:00:00Z"``
    * - ``epsg``
      - EPSG code of the datasource
      - ``int``
      - ``32648``
    * - ``frequency_band``
      - frequency band
      - ``str``
      - ``"X"``
    * - ``ids``
      - STAC identifiers (unique product identifiers)
      - ``List[str]``
      - ``["CAPELLA_C02_SP_GEO_HH_20201109060434_20201109060437"]``
    * - ``intersects``
      - geometry component of GeoJSON
      - ``geometryGeoJSON``
      - ``{'type': 'Point', 'coordinates': [-113.1, 51.1]}``
    * - ``incidence_angle``
      - center incidence angle, between 0 and 90
      - ``Union[int, float]``
      - ``31``
    * - ``instruments``
      - leveraged instruments
      - ``List[str]``
      - ``["capella-radar-5"]``
    * - ``instrument_mode``
      - | instrument mode, one of
        | ``"spotlight"``, ``"stripmap"``, ``"sliding_spotlight"``
      - ``str``
      - ``"spotlight"``
    * - ``local_datetime``
      - local datetime
      - ``str``
      - ``2022-12-12TT07:37:42.324551+0800``
    * - ``local_time``
      - local time
      - ``str``
      - ``07:37:42.324551``
    * - ``local_timezone``
      - time zone
      - ``str``
      - ``Asia/Shanghai``
    * - ``look_angle``
      - look angle
      - ``Union[int, float]``
      - ``28.4``
    * - ``looks_azimuth``
      - looks in azimuth
      - ``int``
      - ``7``
    * - ``looks_equivalent_number``
      - equivalent number of looks (ENL)
      - ``int``
      - ``7``
    * - ``looks_range``
      - looks in range
      - ``int``
      - ``1``
    * - ``observation_direction``
      - | antenna pointing direction, one of
        | ``"right"``, ``"left"``
      - ``str``
      - ``"left"``
    * - ``orbit_state``
      - orbit State, one of "ascending", "descending"
      - ``str``
      - ``"ascending"``
    * - ``orbital_plane``
      - | Orbital Plane, inclination angle of orbit, one of
        | ``45``, ``53``, ``97``
      - ``int``
      - ``45``
    * - ``pixel_spacing_azimuth``
      - pixel spacing azimuth (m)
      - ``Union[int, float]``
      - ``5``
    * - ``pixel_spacing_range``
      - pixel spacing range (m)
      - ``Union[int, float]``
      - ``5``
    * - ``platform``
      - platform identifier
      - ``str``
      - ``"capella-6"``
    * - ``polarizations``
      - polarization, one of "HH", "VV"
      - ``List[str]``
      - ``["HH"]``
    * - ``product_category``
      - | product category, one of
        | ``"standard"``, ``"custom"``, ``"extended"``
      - ``str``
      - ``"standard"``
    * - ``product_type``
      - | product type str, one of
        | ``"SLC"``, ``"GEO"``, ``"GEC"``, ``"SICD"``, ``"SIDD"``, ``"CPHD"``
        | ``"VS"``, ``"ACD"```
      - ``str``
      - ``"SLC"``
    * - ``resolution_azimuth``
      - resolution azimuth (m)
      - ``float``
      - ``0.5``
    * - ``resolution_ground_range``
      - resolution ground range (m)
      - ``float``
      - ``0.5``
    * - ``resolution_range``
      - resolution range (m)
      - ``float``
      - ``0.5``
    * - ``squint_angle``
      - squint angle
      - ``float``
      - ``30.1``


advanced search
###############

.. code:: python3

    # sorted descending by datetime, collected on capella-5 with HH polarization
    capella_5 = client.search(
        polarizations="HH",
        platform="capella-5",
        sortby="-datetime"
    )

    # sorted desc by datetime and 2nd ascending by STAC id, collected on capella-2 with VV polarization
    vvs = client.search(
        polarizations="VV",
        platform="capella-2",
        sortby=["-datetime", "+id"]
    )

    # get up to 10 SLC stripmap collected in 06/2021
    capella_sm_01_2021 = client.search(
        instrument_mode="stripmap",
        datetime__gt="2021-06-01T00:00:00Z",
        datetime__lt="2021-07-01T00:00:00Z",
        product_type="SLC",
        limit=10,
    )

    # get up to 10 GEO stripmap OR spotlight
    capella_sm_or_sp = client.search(
        instrument_mode=["stripmap", "spotlight"],
        product_type="GEO",
        limit=10,
    )

    # get up to 10 items with azimuth resolution <= 0.5 AND range resolution between 0.3 and 0.5
    capella_sm_or_sp_hq = client.search(
        resolution_azimuth__lte=0.5,
        resolution_range__gte=0.3,
        resolution_range__lte=0.5,
        limit=10,
    )

    # get up to 10 GEO sliding spotlight with look angle > 35
    plus35_lookangle_sliding_spotlight = client.search(
        look_angle__gt=35,
        product_type="GEO",
        instrument_mode="sliding_spotlight",
        limit=10
    )

    # get items derived from particular collect
    collect_id = "27a71826-7819-48cc-b8f2-0ad10bee0f97"  # NOTE: provide valid collect_id
    collect_id_items = client.search(
        collect_id=collect_id
    )

    # get GEO items by local time window within certain EPSG
    night_items = client.search(
        product_type="GEO",
        local_time__gte="03:00:00",
        local_time__lte="04:00:00",
        epsg=32648,
    )


    # take it to the max - get GEO spotlight items over SF downtown with many filters sorted by datetime

    sanfran_dt_bbox = [-122.4, 37.8, -122.3, 37.7]
    hefty_query_SF_sorted = client.search(
        bbox=sanfran_dt_bbox,
        datetime__gt="2021-05-01T00:00:00Z",
        datetime__lt="2021-07-01T00:00:00Z",
        local_time__gte="09:00:00",
        local_time__lte="18:00:00",
        instrument_mode="spotlight",
        product_type="GEO",
        look_angle__gt=25,
        look_angle__lt=35,
        looks_equivalent_number=9,
        polarizations=["HH"],
        resolution_azimuth__lte=1,
        resolution_range__lte=1,
        orbit_state="descending",
        orbital_plane=45,
        observation_direction="right",
        squint_angle__gt=-0.5,
        squint_angle__lt=0.5,
        sortby="-datetime",
        collections=["capella-geo"]
    )



``capella-console-client`` supports the following search operators:

.. list-table:: supported search operators
   :widths: 20 20 60
   :header-rows: 1

   * - operator
     - description
     - example
   * - ``eq``
     - equals
     - .. code:: python3

         product_type__eq="GEO" (== product_type="GEO")
   * - ``in``
     - contains
     - .. code:: python3

         product_type__in=["SLC", "GEO", "GEC"] ( == product_type=["SLC", "GEO", "GEC"])
   * - ``gt``
     - greater than
     - .. code:: python3

         datetime__gt="2021-01-01T00:00:00Z"
   * - ``lt``
     - lower than
     - .. code:: python3

         datetime__lt="2021-02-01T00:00:00Z"
   * - ``gte``
     - greater than equal
     - .. code:: python3

         resolution_range__gte=0.3
   * - ``lte``
     - lower than equal
     - .. code:: python3

         resolution_azimuth__lte=0.5

The API for advanced filtering operations was inspired by `Django's ORM <https://docs.djangoproject.com/en/3.2/topics/db/queries/#chaining-filters>`_


visualize search results
########################

.. code:: python3

    from pathlib import Path
    import json

    results = client.search(
        instrument_mode="spotligh",
        product_type="GEO",
        sortby="-datetime"
    )
    # store stac items in geojson FeatureCollection
    feature_collection = results.to_feature_collection()

    # write to disk
    feature_collection_path = Path('CAPELLA_SP_GEOs.geojson')
    feature_collection_path.write_text(json.dumps(feature_collection))

    # open e.g. in QGIS


order products
##############

Issue the following snippets to submit a (purchasing) order by providing STAC items or STAC ids.

.. code:: python3

    # submit order with stac items
    order_id = client.submit_order(items=capella_spotlight_olympic_NP_geo)

    # alternatively order by STAC ids
    first_two_ids = [item["id"] for item in capella_spotlight_olympic_NP_geo[:2]]
    order_id = client.submit_order(stac_ids=first_two_ids)

    # since orders expire you can alternatively check prior if an active order already exists
    # instead of creating a new order - charges won't be applied twice anyways
    order_id = client.submit_order(items=capella_spotlight_olympic_NP_geo,
                                   check_active_orders=True)


download
########

Download assets of previously ordered products to local disk.

.. code:: python3

    # download all products of an order to /tmp
    product_paths = client.download_products(
        order_id=order_id,
        local_dir="/tmp",
    )

    # 🕒 don't like parallel downloads? 🕒 - set threaded = False in order to fetch the product assets serially
    product_paths = client.download_products(
        order_id=order_id,
        local_dir="/tmp",
        threaded=False
    )

    # ⌛ like to watch progress bars? ⌛ - set show_progress = True in order to get feedback on download status (time remaining, transfer stats, ...)
    product_paths = client.download_products(
        order_id=order_id,
        local_dir="/tmp",
        show_progress=True,
    )

    # the client is respectful of your local files and does not override them by default
    # but can be instructed to do so
    local_thumb_path = client.download_products(
        order_id=order_id,
        local_dir="/tmp",
        show_progress=True,
        override=True
    )


Output

.. code:: sh

    2021-06-21 20:28:16,734 - 🛰️  Capella Space 🐐 - INFO - downloading product CAPELLA_C03_SP_SLC_HH_20210621202423_20210621202425 to /tmp/CAPELLA_C03_SP_SLC_HH_20210621202423_20210621202425
    CAPELLA_C03_SP_GEO_HH_20210603175705_20210603175729_thumb.png       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 211.3/211.3 KB   • 499.7 kB/s  • 0:00:00
    CAPELLA_C03_SP_GEO_HH_20210619045726_20210619045747_thumb.png       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 307.1/307.1 KB   • 1.4 MB/s    • 0:00:00
    CAPELLA_C03_SP_GEO_HH_20210619180117_20210619180140_thumb.png       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 271.6/271.6 KB   • 1.1 MB/s    • 0:00:00
    CAPELLA_C03_SP_GEO_HH_20210627180259_20210627180321_extended.json   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0.0%   • 20,426/-1 bytes  • 200.2 kB/s  • 0:00:00
    CAPELLA_C03_SP_GEO_HH_20210603175705_20210603175729_extended.json   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0.0%   • 21,536/-1 bytes  • 293.8 kB/s  • 0:00:00
    CAPELLA_C03_SP_GEO_HH_20210619180117_20210619180140_extended.json   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0.0%   • 20,650/-1 bytes  • 122.0 kB/s  • 0:00:00
    CAPELLA_C03_SP_GEO_HH_20210627180259_20210627180321_thumb.png       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 316.7/316.7 KB   • 1.3 MB/s    • 0:00:00
    CAPELLA_C03_SP_GEO_HH_20210603175705_20210603175729.tif             ━╸━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 5.6%   • 13.2/237.4 MB    • 2.2 MB/s    • 0:01:42
    CAPELLA_C03_SP_GEO_HH_20210619045726_20210619045747_extended.json   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0.0%   • 22,002/-1 bytes  • 196.9 kB/s  • 0:00:00
    CAPELLA_C03_SP_GEO_HH_20210627180259_20210627180321.tif             ━╺━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3.0%   • 11.0/360.9 MB    • 1.9 MB/s    • 0:03:04
    CAPELLA_C03_SP_GEO_HH_20210619045726_20210619045747.tif             ╸━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.7%   • 9.8/359.0 MB     • 1.8 MB/s    • 0:03:18

By default the respective product assets are saved into separate product directories, i.e.

.. code:: sh

  /tmp/<stac_id_1>/<stac_id_1>.tif
  /tmp/<stac_id_1>/<stac_id_1>_thumb.png
  /tmp/<stac_id_1>/<stac_id_1>_extended.json
  /tmp/<stac_id_2>/<stac_id_2>.tif
  ...

If you prefer a flat hierarchy set ``separate_dirs`` to ``False``:

.. code:: python3

    product_paths = client.download_products(
        order_id=order_id,
        separate_dirs=False,
    )


download products filtered by product type
##########################################

.. code:: python3

    # download only GEO product
    product_paths = client.download_products(
       order_id=order_id,
       product_types=["GEO"]
    )

    # download only SLC and GEO product
    product_paths = client.download_products(
       order_id=order_id,
       product_types=["SLC", "GEO"]
    )


download products filtered by asset type
########################################

.. code:: python3

    # download only thumbnails
    product_paths = client.download_products(
       order_id=order_id,
       include=["thumbnail"]
    )

    # 'include' / 'exclude' can also be a string if only one provided
    product_paths = client.download_products(
       order_id=order_id,
       include="thumbnail"
    )

    # download only raster (VV or HH)
    product_paths = client.download_products(
       order_id=order_id,
       include="raster"
    )

    # download all assets except raster
    product_paths = client.download_products(
       order_id=order_id,
       exclude="raster"
    )

    # explicit DENY overrides explicit ALLOW --> the following would only fetch thumbnails
    product_paths = client.download_products(
       order_id=order_id,
       include=["raster", "thumbnail"]
       exclude="raster"
    )


order and download products of a tasking request
################################################

Requirement: you have previously issued a tasking request that is in 'completed' state

.. code:: python3

    tasking_request_id = "27a71826-7819-48cc-b8f2-0ad10bee0f97"  # NOTE: provide valid tasking_request_id

    # download ALL products
    product_paths = client.download_products(
        tasking_request_id=tasking_request_id,
    )

    # download only GEO product
    product_paths = client.download_products(
        tasking_request_id=tasking_request_id,
        product_types=["GEO"]
    )


order and download products of a collect
########################################

.. code:: python3

    collect_id = "27a71826-7819-48cc-b8f2-0ad10bee0f97"  # NOTE: provide valid collect_id

    # download ALL products
    product_paths = client.download_products(
        collect_id=collect_id,
    )

    # download only GEC product
    product_paths = client.download_products(
        collect_id=collect_id,
        product_types=["GEC"],
    )


review order
############

If you would like to review the cost of an order before you submission, issue:

.. code:: python3

    order_details = client.review_order(items=capella_spotlight_olympic_NP_geo)
    print(order_details['orderDetails']['summary'])

.. _presigned items:

presigned items
###############

In order to directly load assets (imagery or metadata) into memory you need to request signed S3 URLs first.

.. code:: python3

    items_presigned = client.get_presigned_items(order_id)

    # alternatively presigned assets can also be filtered - e.g. give me the presigned assets of 2 specific STAC ids
    first_two_ids = [item["id"] for item in capella_spotlight_olympic_NP_geo[:2]]
    items_presigned = client.get_presigned_items(order_id,
                                                   stac_ids=first_two_ids)

    # sort presigned assets by list of stac ids
    sorted_stac_ids = sorted([s['id'] for s in capella_spotlight_olympic_NP_geo])
    items_presigned_sorted = client.get_presigned_items(order_id,
                                                        sort_by=sorted_stac_ids)

See `read imagery`_  or `read metadata`_ for more information.


download single product
#######################

.. code:: python3

    # download a specific product with download_product (SINGULAR)
    product_paths = client.download_product(assets_presigned[0], local_dir="/tmp", override=True)



download single asset
#####################

single assets can be downloaded to gven paths

.. code:: python3

    # download thumbnail
    thumb_presigned_href = assets_presigned[0]["thumbnail"]["href"]
    dest_path = "/tmp/thumb.png"
    local_thumb_path = client.download_asset(thumb_presigned_href, local_path=dest_path)

    # assets are saved into OS specific temp directory if `local_path` not provided
    raster_presigned_href = assets_presigned[0]["HH"]["href"]
    local_raster_path = client.download_asset(raster_presigned_href)


    from pathlib import Path
    assert local_thumb_path == Path(dest_path)



list orders
###########

Issue the following snippet to view the ordering history

.. code:: python3

    # list all orders
    all_orders = client.list_orders()

    # list all active orders
    all_active_orders = client.list_orders(is_active=True)

    # list specific order(s) by order id
    specific_order_id = all_orders[0]["orderId"]
    specific_orders = client.list_orders(order_ids=[specific_order_id])


tasking requests
################

search for tasking requests

.. code:: python3

    tasking_request_id = "27a71826-7819-48cc-b8f2-0ad10bee0f97"  # provide valid taskingrequest_id

    # get task info
    task = client.get_task(tasking_request_id)

    # was it completed?
    client.is_task_completed(task)

advanced tasking request search

.. code:: python3

    # get ALL completed tasking requests of user
    user_completed_trs = client.list_tasking_requests(status="completed")

    # get all COMPLETED tasking requests of ORG (requires org manager/ admin role)
    org+completed_trs = client.list_tasking_requests(
        for_org=True,
        status="completed"
    )

    # get all completed tasking requests of org SUBMITTED AFTER 2022-12-01 (UTC)
    org_completed_trs_submitted_dec_22 = client.list_tasking_requests(
        for_org=True,
        status="completed",
        submission_time__gt=datetime.datetime(2022, 12, 1)
    )



.. _read imagery:


read imagery
############

Given a presigned asset href (see `presigned items`_) load imagery into memory

NOTE: requires `rasterio <https://pypi.org/project/rasterio/>`_ (not part of this package)

.. code:: python3

    import rasterio

    # raster profile
    raster_presigned_href = assets_presigned[0]["HH"]["href"]
    with rasterio.open(raster_presigned_href) as ds:
        print(ds.profile)

    # read chunk of raster
    with rasterio.open(raster_presigned_href) as ds:
        chunk = ds.read(1, window=rasterio.windows.Window(2000, 2000, 7000, 7000))
    print(chunk.shape)

    # read thumbnail
    thumb_presigned_href = assets_presigned[0]["thumbnail"]["href"]
    with rasterio.open(thumb_presigned_href) as ds:
        thumb = ds.read(1)
    print(thumb.shape)


.. _read metadata:

read metadata
#############

.. code:: python3

  import httpx

  # read extended metadata .json
  metadata_presigned_href = assets_presigned[0]["metadata"]["href"]
  metadata = httpx.get(metadata_presigned_href).json()


create tasking request
##############

Create a tasking request with basic parameters

.. code:: python3

    # Create basic tasking request with a geometry (only required parameter)
    client.create_tasking_request(
        geometry=geojson.Polygon(
            [
                [
                    [11.148216220469152, 49.59672249842626],
                    [11.148216220469152, 49.55415435337187],
                    [11.219621049225651, 49.55415435337187],
                    [11.219621049225651, 49.59672249842626],
                    [11.148216220469152, 49.59672249842626],
                ]
            ]
        )
    )

    # Add a couple of parameters to help you track/identify it better
    client.create_tasking_request(
        geometry=geojson.Polygon(
            [
                [
                    [11.148216220469152, 49.59672249842626],
                    [11.148216220469152, 49.55415435337187],
                    [11.219621049225651, 49.55415435337187],
                    [11.219621049225651, 49.59672249842626],
                    [11.148216220469152, 49.59672249842626],
                ]
            ]
        ),
        name="I<3SAR",
        description="My first tasking request"
    )


create repeating tasking request
##############

Create a repeating tasking request with basic parameters

.. code:: python3

    # Create basic repeating tasking request with a geometry (only required parameter)
    client.create_repeat_request(
        geometry=geojson.Polygon(
            [
                [
                    [11.148216220469152, 49.59672249842626],
                    [11.148216220469152, 49.55415435337187],
                    [11.219621049225651, 49.55415435337187],
                    [11.219621049225651, 49.59672249842626],
                    [11.148216220469152, 49.59672249842626],
                ]
            ]
        )
    )

    # Add a couple of parameters to help you track/identify it better
    client.create_repeat_request(
        geometry=geojson.Polygon(
            [
                [
                    [11.148216220469152, 49.59672249842626],
                    [11.148216220469152, 49.55415435337187],
                    [11.219621049225651, 49.55415435337187],
                    [11.219621049225651, 49.59672249842626],
                    [11.148216220469152, 49.59672249842626],
                ]
            ]
        ),
        name="I<3SAR",
        description="My first tasking request"
    )

    # Note that you can only define either repeat_end OR repetition_count, not both. The following request will fail:
    client.create_repeat_request(
        geometry=geojson.Polygon(
            [
                [
                    [11.148216220469152, 49.59672249842626],
                    [11.148216220469152, 49.55415435337187],
                    [11.219621049225651, 49.55415435337187],
                    [11.219621049225651, 49.59672249842626],
                    [11.148216220469152, 49.59672249842626],
                ]
            ]
        ),
        name="I<3SAR",
        description="My first tasking request",
        repeat_start="2023-12-24 3:30 PM"
        repeat_end="2023-12-31 3:30 PM",
        repetition_count=23
    )
