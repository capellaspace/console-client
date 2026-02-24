.. _example_usage:

**************
Example Usage
**************

This page provides reusable snippets to :ref:`authenticate <example-auth>`, :ref:`search the catalog <example-catalog-search>`, :ref:`order <example-order>`, :ref:`task <example-task>`, :ref:`search tasking requests <example-search-trs>`, :ref:`consume imagery and metadata <example-consume>` and more.


.. code:: python3

    from capella_console_client import CapellaConsoleClient


.. _example-auth:

authenticate
############

with API key
************

.. code:: python3

    client = CapellaConsoleClient(api_key="<api-key>", verbose=True)

    # don't want to validate the api-key (saves an API call)
    client = CapellaConsoleClient(api_key="<api-key>", no_token_check=True)

    # prompts for API key
    client = CapellaConsoleClient()

    # reads API key from CAPELLA_API_KEY env
    os.environ["CAPELLA_API_KEY"] = "<api-key>"   # NOTE: provide valid API Key
    client = CapellaConsoleClient()


with access token
*****************

.. code:: python3

    # already have a valid access token (JWT)? no problem
    client = CapellaConsoleClient(token="<token>", verbose=True)

    # don't want to validate the token (saves an API call)
    client = CapellaConsoleClient(token="<token>", no_token_check=True)


.. _example-catalog-search:

catalog
#######

simple search
*************

Searches are run against Capella's Catalog and `STAC items <https://stacspec.org/>`_ matching the search criteria is returned.

A multitude of :ref:`query fields <stac-query-fields>` and :ref:`query operators <query-ops>` are supported.

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


By default **up to 500** STAC items are returned. This can be increased by providing a custom ``limit`` (up to 9999):

.. code:: python3

    many_products = client.search(constellation="capella", limit=1000)


Expensive searches (time is $$)  can be sped up by providing `threaded=True`:

.. code:: python3

    many_products = client.search(constellation="capella", limit=9999, threaded=True)


advanced search
***************

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

    # use ownership filters

    owned_geo_items = client.search(
        product_type="GEO",
        ownership="ownedByOrganization"
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



group search results
********************

.. code:: python3

    results = client.search(
        instrument_mode="spotlight",
        product_type="GEO",
        sortby="-datetime"
    )

    by_stac_id = results.groupby(field="id")

    by_collect_id = results.groupby(field="collect_id")

    by_stac_collection = results.groupby(field="collection")

    by_instrument_mode = results.groupby(field="instrument_mode")

    by_instrument = res.groupby(field="instruments").keys()


search results
**************

visualize search results

.. code:: python3

    from pathlib import Path
    import json

    results = client.search(
        instrument_mode="spotlight",
        product_type="GEO",
        sortby="-datetime"
    )
    # store stac items in geojson FeatureCollection
    feature_collection = results.to_feature_collection()

    # write to disk
    feature_collection_path = Path('CAPELLA_SP_GEOs.geojson')
    feature_collection_path.write_text(json.dumps(feature_collection))

    # open e.g. in QGIS



.. _example-order:

order
#####

Issue the following snippets to submit a (purchasing) order by providing STAC items or STAC ids.

order items
***********

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


download assets
***************

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

    2021-06-21 20:28:16,734 - 🛰️  Capella 🐐 - INFO - downloading product CAPELLA_C03_SP_SLC_HH_20210621202423_20210621202425 to /tmp/CAPELLA_C03_SP_SLC_HH_20210621202423_20210621202425
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

single asset
^^^^^^^^^^^^

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


order filters
*************

by product type
^^^^^^^^^^^^^^^

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


by asset type
^^^^^^^^^^^^^

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

items of tasking request
^^^^^^^^^^^^^^^^^^^^^^^^

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


items of collect
^^^^^^^^^^^^^^^^

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
************

If you would like to review the cost of an order before you submission, issue:

.. code:: python3

    order_details = client.review_order(items=capella_spotlight_olympic_NP_geo)
    print(order_details['orderDetails']['summary'])

.. _presigned items:

presign assets
**************

In order to directly load assets (imagery or other) into memory you need to request signed S3 URLs first.

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


list orders
***********

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

.. _example-task:

create
******

NOTE: `geometry` and `name` are the only required properties to create a tasking request.

.. code:: python3

    # create point tasking request
    client.create_tasking_request(
        geometry=geojson.Point([11.148216220469152, 49.59672249842626]),
        name="point tasking request #127"
    )

    # area tasking request
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
        name="area tasking request #127",
        collection_type="stripmap_100",
    )

    # tasking request customization
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
        name="highly customizable #127",
        description="too many knobs",
        collection_tier="urgent",
        collection_type="spotlight_ultra",
        local_time="day",
        off_nadir_min=5,
        off_nadir_max=50,
        orbitalPlanes=[45, 53],
        asc_dsc="ascending",
        look_direction="right",
        polarization="HH",
        archive_holdback="30 day",
        custom_attribute_1="correlation #1",
        custom_attribute_2="correlation #2",
        pre_approval=True,
        azimuth_angle_min=340,
        azimuth_angle_max=20,
        squint="enabled",
        max_squint_angle=25,
    )


    # same as above but leveraging enums defined in `enumerations.py` (client-side validation)
    from capella_console_client.enumerations import (
        CollectionTier,
        CollectionType,
        LocalTimeOption,
        OrbitalPlane,
        OrbitState,
        Polarization,
        ObservationDirection,
        ArchiveHoldback,
        SquintMode,
    )

    client.create_tasking_request(
        geometry=geojson.Point([11.148216220469152, 49.59672249842626]),
        name="highly customizable #127",
        description="too many knobs",
        collection_tier=CollectionTier.urgent,
        collection_type=CollectionType.SPOTLIGHT_ULTRA,
        local_time=LocalTimeOption.day,
        off_nadir_min=5,
        off_nadir_max=50,
        orbital_planes=[OrbitalPlane.fortyfive, OrbitalPlane.fiftythree],
        asc_dsc=OrbitState.ascending,
        look_direction=ObservationDirection.right,
        polarization=Polarization.HH,
        archive_holdback=ArchiveHoldback.thirty_day,
        custom_attribute_1="correlation #1",
        custom_attribute_2="correlation #2",
        pre_approval=True,
        azimuth_angle_min=340,
        azimuth_angle_max=20,
        squint=SquintMode.ENABLED,
        max_squint_angle=30,
    )

cancel
******

Find more information `here <https://docs.capellaspace.com/constellation-tasking/cancel-task>`_.
For Cancellation fees please refer to `Capella's Tasking Cancellation Policy Overview <https://support.capellaspace.com/what-is-the-tasking-cancellation-policy>`_.


.. code:: python3

    # provide 1..N valid tasking request ids to be cancelled
    cancel_result_by_id = sit_client.cancel_tasking_requests(
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "cccccccc-cccc-cccc-cccc-cccccccccccc"
    )

    print(cancel_result_by_id)


.. _example-search-trs:


search
******


A multitude of :ref:`query fields <tr-query-fields>` and :ref:`query operators <query-ops>` are supported.


.. code:: python3

    tasking_request_id = "27a71826-7819-48cc-b8f2-0ad10bee0f97"  # provide valid taskingrequest_id

    # get task info
    task = client.get_task(tasking_request_id)

    # was it completed?
    client.is_task_completed(task)

advanced tasking request search

.. code:: python3

    # get ALL completed tasking requests of user
    user_completed_trs_result = client.search_tasking_requests(status="completed")

    # get all COMPLETED tasking requests of ORG (requires org manager/ admin role)
    org_completed_trs_result = client.search_tasking_requests(
        for_org=True,
        status="completed"
    )

    # get all completed tasking requests of org SUBMITTED AFTER 2022-12-01 (UTC)
    org_completed_trs_submitted_dec_22_result = client.search_tasking_requests(
        for_org=True,
        status="completed",
        submission_time__gt=datetime.datetime(2022, 12, 1)
    )

    # subset of supported filters
    completed_sp_prio_trs_result = client.search_tasking_requests(
        status="completed",
        window_open__gt=datetime.datetime(2025, 12, 1),
        window_open__lt=datetime.datetime(2026, 12, 1),
        collection_type=["spotlight", "spotlight_ultra"],
        collection_tier="priority",
    )

    # searches are paginated + parallelized by default

    client.search_tasking_requests(
        status="completed",
        for_org=True,
    )

    2026-02-24 13:25:31,479 - 🛰️  Capella 🐐 - INFO - searching tasking requests with payload ...
    2026-02-24 13:25:41,340 - 🛰️  Capella 🐐 - INFO - page 1 out of 4: 250 SearchEntity.TASKING_REQUEST
    2026-02-24 13:25:41,695 - 🛰️  Capella 🐐 - INFO - page 4 out of 4: 250 SearchEntity.TASKING_REQUEST
    2026-02-24 13:25:42,311 - 🛰️  Capella 🐐 - INFO - page 3 out of 4: 250 SearchEntity.TASKING_REQUEST
    2026-02-24 13:25:42,997 - 🛰️  Capella 🐐 - INFO - page 2 out of 4: 200 SearchEntity.TASKING_REQUEST
    2026-02-24 13:25:49,254 - 🛰️  Capella 🐐 - INFO - found 1200 tasking requests matching search query

    # parallel search requests can be disabled by setting `threaded=False` in order to fetch the product assets serially
    client.search_tasking_requests(
        status="completed",
        for_org=True,
        threaded=False
    )

    2026-02-24 13:33:10,764 - 🛰️  Capella 🐐 - INFO - searching tasking requests with payload ...
    2026-02-24 13:33:15,306 - 🛰️  Capella 🐐 - INFO - page 1 out of 4: 250 SearchEntity.TASKING_REQUEST
    2026-02-24 13:33:17,626 - 🛰️  Capella 🐐 - INFO - page 2 out of 4: 250 SearchEntity.TASKING_REQUEST
    2026-02-24 13:33:19,950 - 🛰️  Capella 🐐 - INFO - page 3 out of 4: 250 SearchEntity.TASKING_REQUEST
    2026-02-24 13:33:22,086 - 🛰️  Capella 🐐 - INFO - page 4 out of 4: 200 SearchEntity.TASKING_REQUEST
    2026-02-24 13:33:29,135 - 🛰️  Capella 🐐 - INFO - found 1200 tasking requests matching search query



repeat requests
###############

create
******

NOTE: `geometry` and `name` are the only required properties to create a repeat request.

.. code:: python3

    # create above tasking request as repeat series
    from capella_console_client.enumerations import (
        RepeatCollectionTier,
        CollectionType,
        LocalTimeOption,
        OrbitalPlane,
        OrbitState,
        Polarization,
        ObservationDirection,
        ArchiveHoldback,
        SquintMode,
    )

    client.create_repeat_request(
        geometry=geojson.Point([11.148216220469152, 49.59672249842626]),
        name="highly customizable repeat request #127",
        description="too many knobs",
        collection_tier=RepeatCollectionTier.flexible,
        collection_type=CollectionType.SPOTLIGHT_ULTRA,
        local_time=LocalTimeOption.day,
        off_nadir_min=5,
        off_nadir_max=50,
        orbital_planes=[OrbitalPlane.fortyfive, OrbitalPlane.fiftythree],
        asc_dsc=OrbitState.ascending,
        look_direction=ObservationDirection.right,
        polarization=Polarization.HH,
        archive_holdback=ArchiveHoldback.thirty_day,
        custom_attribute_1="correlation #1",
        custom_attribute_2="correlation #2",
        azimuth_angle_min=340,
        azimuth_angle_max=20,
        squint=SquintMode.ENABLED,
        max_squint_angle=30,
    )


repeat requests repeat cadence can be configured in multiple ways

.. code:: python3

    # A) until cancelled, e.g. weekly starting now (defaults)
    client.create_repeat_request(
        geometry=geojson.Point([11.148216220469152, 49.59672249842626]),
        name="daily repeat",
    )

    # B) start + end datetime + frequency , e.g. daily for 27 days
    from datetime import datetime, timezone, timedelta
    from capella_console_client.enumerations import RepeatCycle

    repeat_start = datetime.now(tz=timezone.utc)
    repeat_end = repeat_start + timedelta(days=27)

    client.create_repeat_request(
        geometry=geojson.Point([11.148216220469152, 49.59672249842626]),
        name="daily repeat",
        description="daily repeat",
        repeat_start=repeat_start,
        repeat_end=repeat_end,
        repetition_interval=RepeatCycle.DAILY,
    )

    # C) number of collects + frequency, e.g. 5 collects weekly starting from now
    client.create_repeat_request(
        geometry=geojson.Point([11.148216220469152, 49.59672249842626]),
        name="repeat five weeks",
        description="repeat five weeks",
        repeat_start=repeat_start,
        repetition_count=5,
        repetition_interval=RepeatCycle.WEEKLY,
    )


cancel
******

Find more information `here <https://docs.capellaspace.com/constellation-tasking/cancel-task>`_.
For Cancellation fees please refer to `Capella's Tasking Cancellation Policy Overview <https://support.capellaspace.com/what-is-the-tasking-cancellation-policy>`_.


.. code:: python3

    # provide 1..N valid repeat request ids to be cancelled
    cancel_result_by_id = sit_client.cancel_repeat_requests(
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "cccccccc-cccc-cccc-cccc-cccccccccccc"
    )

    print(cancel_result_by_id)


search
******


A multitude of :ref:`query fields <rr-query-fields>` and :ref:`query operators <query-ops>` are supported.


.. code:: python3

    repeat_request_id = "37a71826-7819-48cc-b8f2-0ad10bee0f97"  # provide valid repeat_request_id

    # get repeat request by id
    rr = client.search_repeat_request(repeat_request_id=repeat_request_id)

    rr[0]

advanced repeat request search

.. code:: python3

    # get ALL completed repeat requests of user
    user_completed_rrs_result = client.search_repeat_request(status="completed")

    # get all COMPLETED tasking requests of ORG (requires org manager/ admin role)
    org_completed_trs_result = client.search_repeat_request(
        for_org=True,
        status="completed"
    )

    # get all completed tasking requests of org SUBMITTED AFTER 2022-12-01 (UTC)
    org_completed_rrs_submitted_dec_22_result = client.search_repeat_request(
        for_org=True,
        status="completed",
        submission_time__gt="2022-12-1"
    )

    # subset of supported filters
    active_sp_routine_rrs_result = client.search_repeat_request(
        status="active",
        repeat_start__lt="2025-10-01",
        repeat_start__gt="2025-06-01",
        collection_type=["spotlight", "spotlight_ultra"],
        collection_tier="routine"
    )


.. _example-consume:

consume
#######

.. _read imagery:

read imagery
************

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
*************

.. code:: python3

  import httpx

  # read extended metadata .json
  metadata_presigned_href = assets_presigned[0]["metadata"]["href"]
  metadata = httpx.get(metadata_presigned_href).json()
