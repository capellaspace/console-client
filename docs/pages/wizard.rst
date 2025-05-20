.. _wizard:

**********************
capella-console-wizard
**********************

Starting with ``capella-console-client>=0.8.0`` this package ships with an interactive wizard-like CLI


Installation
============

.. code:: console

    $ pip install capella-console-client[wizard]

Note: For ZSH shells the brackets need to be escaped or full package name quoted:

.. code:: console

    $ pip install "capella-console-client[wizard]" or pip install capella-console-client\[wizard\]


.. code::

    capella-console-wizard --help

Configure
=========

.. code:: console

    $ capella-console-wizard configure
    2021-10-07 15:01:22,936 - 🛰️  Capella Space 🐐 - INFO - let's get you all setup using capella-console-wizard:
    2021-10-07 15:01:22,936 - 🛰️  Capella Space 🐐 - INFO - 		Press Ctrl + C anytime to quit

    ? Console API key: ****************************************************************
    updated API key for Capella Console
    ? Specify the default location for downloads and .json STAC exports: (press <tab>) /data/stuff/things/here/
    updated default output path for .json STAC exports
    ? Specify the order of search filters to be used in searches: console UI filters on top
    updated order of search filters to be used in searches
    ? Which STAC item fields would you like to display in the search results table? done (9 selections)
    updated fields that to will be displayed in search results table
    ? Speciy default limit to be used in searches (can be overridden at search time): 100
    updated default search limit to 100


Workflows
=========

``capella-console-wizard`` exposes common interactive workflows (search, order, download).


The following sections describe a subset of those


Interactive search
==================

Interactively search through Capella Console's STAC (Spatio Temporal Asset Catalog)

.. code:: console

    $ capella-console-wizard workflows search

you will be prompted for search 1 to many search filter (e.g. ``datetime`` , ``bbox``, ``product_type``)

.. code:: console

    ? What are you looking for today? (Use arrow keys to move, <space> to select, <a> to toggle, <i> to invert)
   ● bbox
   ○ billable_area
   ○ center_frequency
   ○ collect_id
   ○ collections
   ○ constellation
»  ● datetime
   ○ frequency_band
   ○ ids
   ○ incidence_angle
   ○ instrument_mode
   ○ instruments
   ○ limit
   ○ look_angle
   ○ looks_azimuth
   ○ looks_equivalent_number
   ○ looks_range
   ○ observation_direction
   ○ orbit_state
   ○ orbital_plane
   ○ pixel_spacing_azimuth
   ○ pixel_spacing_range
   ○ platform
   ○ polarizations
   ○ product_type
   ○ resolution_azimuth
   ○ resolution_ground_range
   ○ resolution_range
   ○ squint_angle


Checkout
========

Interactively search, order and download products.

.. code:: console

    $ capella-console-wizard workflows checkout
    ? What would you like to do? (Use arrow keys)
    new search
      use previously saved search results
    » provide a collect id
      provide a taskingrequest id
      select existing order

Given collect id

.. code:: console

    ? provide a collect id: <collect_id>
    ? product type(s): (Use arrow keys to move, <space> to select, <a> to toggle, <i> to invert)
      ○ SLC
      ● GEO
      ○ SICD
    » ● GEC
      ○ SIDD
      ○ CPHD
    ? asset type: (Use arrow keys to move, <space> to select, <a> to toggle, <i> to invert)
    » ○ all
      ● raster
      ○ metadata
      ○ thumbnail
    ? download location: /Users/thomas.beyer/data/new_stuff
    2021-11-17 14:00:53,144 - 🛰️  Capella Space 🐐 - INFO - searching catalog with payload {'query': {'capella:collect_id': {'in': ['<collect_id>']}, 'sar:product_type': {'in': ['GEO', 'GEC']}}}
    2021-11-17 14:00:53,145 - 🛰️  Capella Space 🐐 - INFO - 	page 1 (0 - 500)
    2021-11-17 14:00:53,477 - 🛰️  Capella Space 🐐 - INFO - found 2 STAC items
    2021-11-17 14:00:54,461 - 🛰️  Capella Space 🐐 - INFO - reviewing order for <stac_id_1>, <stac_id_2>
    2021-11-17 14:00:56,197 - 🛰️  Capella Space 🐐 - INFO - submitting order for <stac_id_1>, <stac_id_2>
    2021-11-17 14:00:58,106 - 🛰️  Capella Space 🐐 - INFO - successfully submitted order <order_id>
    2021-11-17 14:00:58,106 - 🛰️  Capella Space 🐐 - INFO - getting presigned assets for order <order_id>
    2021-11-17 14:00:59,541 - 🛰️  Capella Space 🐐 - INFO - downloading 2 products
    2021-11-17 14:00:59,541 - 🛰️  Capella Space 🐐 - INFO - filtering by product_types: GEO, GEC
    2021-11-17 14:00:59,542 - 🛰️  Capella Space 🐐 - INFO - downloading product <stac_id_1> to /Users/thomas.beyer/data/new_stuff/<stac_id_1>
    2021-11-17 14:00:59,542 - 🛰️  Capella Space 🐐 - INFO - Only including assets HH, VV
    2021-11-17 14:00:59,543 - 🛰️  Capella Space 🐐 - INFO - downloading product <stac_id_2> to /Users/thomas.beyer/data/new_stuff/<stac_id_2>
    2021-11-17 14:00:59,543 - 🛰️  Capella Space 🐐 - INFO - Only including assets HH, VV
    ...

    ? Want to open any product directories? Yes
    ? select which product directories you want to open done (2 selections)


New search

.. code:: console

    ? What would you like to do? new search
    ? Select your search filters: done (2 selections)
    ? collections [=]: capella-open-data
    ? limit [=]: 1
    2021-11-17 14:10:53,289 - 🛰️  Capella Space 🐐 - INFO - searching catalog with payload {'collections': ['capella-open-data'], 'limit': 1, 'query': {'constellation': {'eq': 'capella'}}}
    2021-11-17 14:10:53,289 - 🛰️  Capella Space 🐐 - INFO - 	page 1 (0 - 1)
    2021-11-17 14:10:53,473 - 🛰️  Capella Space 🐐 - INFO - Using https://0r1mdcwa5c.execute-api.us-west-2.amazonaws.com/prod/search for searches
    2021-11-17 14:10:53,637 - 🛰️  Capella Space 🐐 - INFO - found 1 STAC item
    ╒═════╤═════════════════════════════════════════════════════╤═══════════════════╤════════════════╤════════════════════════════╤═══════════════════╤═════════════════╕
    │   # │ id                                                  │ instrument_mode   │ product_type   │ datetime                   │   incidence_angle │ polarizations   │
    ╞═════╪═════════════════════════════════════════════════════╪═══════════════════╪════════════════╪════════════════════════════╪═══════════════════╪═════════════════╡
    │   1 │ CAPELLA_C05_SP_SLC_HH_20211020065916_20211020065918 │ spotlight         │ SLC            │ 2021-10-20T06:59:17.374865 │              27.3 │ ['HH']          │
    ╘═════╧═════════════════════════════════════════════════════╧═══════════════════╧════════════════╧════════════════════════════╧═══════════════════╧═════════════════╛


    ? Anything you'd like to do now? refine search
    Refining
        {"collections": [["=", ["capella-open-data"]]], "limit": [["=", 1]]}
    ? Select your search filters: done (2 selections)
    ? collections [=]: ['capella-open-data']
    ? limit [=]: 2
    2021-11-17 14:11:05,597 - 🛰️  Capella Space 🐐 - INFO - searching catalog with payload {'collections': ['capella-open-data'], 'limit': 2, 'query': {'constellation': {'eq': 'capella'}}}
    2021-11-17 14:11:05,597 - 🛰️  Capella Space 🐐 - INFO - 	page 1 (0 - 2)
    2021-11-17 14:11:05,759 - 🛰️  Capella Space 🐐 - INFO - found 2 STAC items
    ╒═════╤═════════════════════════════════════════════════════╤═══════════════════╤════════════════╤════════════════════════════╤════════════════════╤═════════════════╕
    │   # │ id                                                  │ instrument_mode   │ product_type   │ datetime                   │   incidence_angle  │ polarizations   │
    ╞═════╪═════════════════════════════════════════════════════╪═══════════════════╪════════════════╪════════════════════════════╪════════════════════╪═════════════════╡
    │   1 │ CAPELLA_C05_SP_SLC_HH_20211020065916_20211020065918 │ spotlight         │ SLC            │ 2021-10-20T06:59:17.374865 │              27.3  │ ['HH']          │
    ├─────┼─────────────────────────────────────────────────────┼───────────────────┼────────────────┼────────────────────────────┼────────────────────┼─────────────────┤
    │   2 │ CAPELLA_C05_SP_GEC_HH_20211020065906_20211020065928 │ spotlight         │ GEC            │ 2021-10-20T06:59:17.374849 │              27.3  │ ['HH']          │
    ╘═════╧═════════════════════════════════════════════════════╧═══════════════════╧════════════════╧════════════════════════════╧════════════════════╧═════════════════╛


    ? Anything you'd like to do now? continue
    ? asset type: [thumbnail]
    ? download location: /Users/thomas.beyer/data/new_stuff
    2021-11-17 14:11:12,876 - 🛰️  Capella Space 🐐 - INFO - reviewing order for CAPELLA_C05_SP_SLC_HH_20211020065916_20211020065918, CAPELLA_C05_SP_GEC_HH_20211020065906_20211020065928
    2021-11-17 14:11:14,565 - 🛰️  Capella Space 🐐 - INFO - submitting order for CAPELLA_C05_SP_SLC_HH_20211020065916_20211020065918, CAPELLA_C05_SP_GEC_HH_20211020065906_20211020065928
    2021-11-17 14:11:16,409 - 🛰️  Capella Space 🐐 - INFO - successfully submitted order 48128100-47f3-11ec-8308-5bb8546cd9f5
    2021-11-17 14:11:16,409 - 🛰️  Capella Space 🐐 - INFO - getting presigned assets for order 48128100-47f3-11ec-8308-5bb8546cd9f5
    2021-11-17 14:11:17,845 - 🛰️  Capella Space 🐐 - INFO - downloading 2 products
    2021-11-17 14:11:17,846 - 🛰️  Capella Space 🐐 - INFO - downloading product CAPELLA_C05_SP_SLC_HH_20211020065916_20211020065918 to /Users/thomas.beyer/data/new_stuff/CAPELLA_C05_SP_SLC_HH_20211020065916_20211020065918
    2021-11-17 14:11:17,846 - 🛰️  Capella Space 🐐 - INFO - Only including assets thumbnail
    2021-11-17 14:11:17,847 - 🛰️  Capella Space 🐐 - INFO - downloading product CAPELLA_C05_SP_GEC_HH_20211020065906_20211020065928 to /Users/thomas.beyer/data/new_stuff/CAPELLA_C05_SP_GEC_HH_20211020065906_20211020065928
    2021-11-17 14:11:17,847 - 🛰️  Capella Space 🐐 - INFO - Only including assets thumbnail
    2021-11-17 14:11:18,125 - 🛰️  Capella Space 🐐 - INFO - downloading to /Users/thomas.beyer/data/new_stuff/CAPELLA_C05_SP_SLC_HH_20211020065916_20211020065918/CAPELLA_C05_SP_GEO_HH_20211020065906_20211020065928_thumb.png (382.4 KiB)
    2021-11-17 14:11:18,175 - 🛰️  Capella Space 🐐 - INFO - downloading to /Users/thomas.beyer/data/new_stuff/CAPELLA_C05_SP_GEC_HH_20211020065906_20211020065928/CAPELLA_C05_SP_GEO_HH_20211020065906_20211020065928_thumb.png (382.4 KiB)
    2021-11-17 14:11:18,365 - 🛰️  Capella Space 🐐 - INFO - successfully downloaded to /Users/thomas.beyer/data/new_stuff/CAPELLA_C05_SP_GEC_HH_20211020065906_20211020065928/CAPELLA_C05_SP_GEO_HH_20211020065906_20211020065928_thumb.png
    2021-11-17 14:11:18,365 - 🛰️  Capella Space 🐐 - INFO - successfully downloaded to /Users/thomas.beyer/data/new_stuff/CAPELLA_C05_SP_SLC_HH_20211020065916_20211020065918/CAPELLA_C05_SP_GEO_HH_20211020065906_20211020065928_thumb.png

    ? Do you want to open any product directories? No
