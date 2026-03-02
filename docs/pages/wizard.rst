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
    2021-10-07 15:01:22,936 - 🛰️  Capella 🐐 - INFO - let's get you all setup using capella-console-wizard:
    2021-10-07 15:01:22,936 - 🛰️  Capella 🐐 - INFO - 		Press Ctrl + C anytime to quit

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

``capella-console-wizard`` exposes common interactive workflows (search, order, download, cancel tasking requests).


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
    2021-11-17 14:00:53,144 - 🛰️  Capella 🐐 - INFO - searching catalog with payload {'query': {'capella:collect_id': {'in': ['<collect_id>']}, 'sar:product_type': {'in': ['GEO', 'GEC']}}}
    2021-11-17 14:00:53,145 - 🛰️  Capella 🐐 - INFO - 	page 1 (0 - 500)
    2021-11-17 14:00:53,477 - 🛰️  Capella 🐐 - INFO - found 2 STAC items
    2021-11-17 14:00:54,461 - 🛰️  Capella 🐐 - INFO - reviewing order for <stac_id_1>, <stac_id_2>
    2021-11-17 14:00:56,197 - 🛰️  Capella 🐐 - INFO - submitting order for <stac_id_1>, <stac_id_2>
    2021-11-17 14:00:58,106 - 🛰️  Capella 🐐 - INFO - successfully submitted order <order_id>
    2021-11-17 14:00:58,106 - 🛰️  Capella 🐐 - INFO - getting presigned assets for order <order_id>
    2021-11-17 14:00:59,541 - 🛰️  Capella 🐐 - INFO - downloading 2 products
    2021-11-17 14:00:59,541 - 🛰️  Capella 🐐 - INFO - filtering by product_types: GEO, GEC
    2021-11-17 14:00:59,542 - 🛰️  Capella 🐐 - INFO - downloading product <stac_id_1> to /Users/thomas.beyer/data/new_stuff/<stac_id_1>
    2021-11-17 14:00:59,542 - 🛰️  Capella 🐐 - INFO - Only including assets HH, VV
    2021-11-17 14:00:59,543 - 🛰️  Capella 🐐 - INFO - downloading product <stac_id_2> to /Users/thomas.beyer/data/new_stuff/<stac_id_2>
    2021-11-17 14:00:59,543 - 🛰️  Capella 🐐 - INFO - Only including assets HH, VV
    ...

    ? Want to open any product directories? Yes
    ? select which product directories you want to open done (2 selections)


New search

.. code:: console

    ? What would you like to do? new search
    ? Select your search filters: done (2 selections)
    ? collections [=]: capella-open-data
    ? limit [=]: 1
    2021-11-17 14:10:53,289 - 🛰️  Capella 🐐 - INFO - searching catalog with payload {'collections': ['capella-open-data'], 'limit': 1, 'query': {'constellation': {'eq': 'capella'}}}
    2021-11-17 14:10:53,289 - 🛰️  Capella 🐐 - INFO - 	page 1 (0 - 1)
    2021-11-17 14:10:53,473 - 🛰️  Capella 🐐 - INFO - Using https://0r1mdcwa5c.execute-api.us-west-2.amazonaws.com/prod/search for searches
    2021-11-17 14:10:53,637 - 🛰️  Capella 🐐 - INFO - found 1 STAC item
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
    2021-11-17 14:11:05,597 - 🛰️  Capella 🐐 - INFO - searching catalog with payload {'collections': ['capella-open-data'], 'limit': 2, 'query': {'constellation': {'eq': 'capella'}}}
    2021-11-17 14:11:05,597 - 🛰️  Capella 🐐 - INFO - 	page 1 (0 - 2)
    2021-11-17 14:11:05,759 - 🛰️  Capella 🐐 - INFO - found 2 STAC items
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
    2021-11-17 14:11:12,876 - 🛰️  Capella 🐐 - INFO - reviewing order for CAPELLA_C05_SP_SLC_HH_20211020065916_20211020065918, CAPELLA_C05_SP_GEC_HH_20211020065906_20211020065928
    2021-11-17 14:11:14,565 - 🛰️  Capella 🐐 - INFO - submitting order for CAPELLA_C05_SP_SLC_HH_20211020065916_20211020065918, CAPELLA_C05_SP_GEC_HH_20211020065906_20211020065928
    2021-11-17 14:11:16,409 - 🛰️  Capella 🐐 - INFO - successfully submitted order 48128100-47f3-11ec-8308-5bb8546cd9f5
    2021-11-17 14:11:16,409 - 🛰️  Capella 🐐 - INFO - getting presigned assets for order 48128100-47f3-11ec-8308-5bb8546cd9f5
    2021-11-17 14:11:17,845 - 🛰️  Capella 🐐 - INFO - downloading 2 products
    2021-11-17 14:11:17,846 - 🛰️  Capella 🐐 - INFO - downloading product CAPELLA_C05_SP_SLC_HH_20211020065916_20211020065918 to /Users/thomas.beyer/data/new_stuff/CAPELLA_C05_SP_SLC_HH_20211020065916_20211020065918
    2021-11-17 14:11:17,846 - 🛰️  Capella 🐐 - INFO - Only including assets thumbnail
    2021-11-17 14:11:17,847 - 🛰️  Capella 🐐 - INFO - downloading product CAPELLA_C05_SP_GEC_HH_20211020065906_20211020065928 to /Users/thomas.beyer/data/new_stuff/CAPELLA_C05_SP_GEC_HH_20211020065906_20211020065928
    2021-11-17 14:11:17,847 - 🛰️  Capella 🐐 - INFO - Only including assets thumbnail
    2021-11-17 14:11:18,125 - 🛰️  Capella 🐐 - INFO - downloading to /Users/thomas.beyer/data/new_stuff/CAPELLA_C05_SP_SLC_HH_20211020065916_20211020065918/CAPELLA_C05_SP_GEO_HH_20211020065906_20211020065928_thumb.png (382.4 KiB)
    2021-11-17 14:11:18,175 - 🛰️  Capella 🐐 - INFO - downloading to /Users/thomas.beyer/data/new_stuff/CAPELLA_C05_SP_GEC_HH_20211020065906_20211020065928/CAPELLA_C05_SP_GEO_HH_20211020065906_20211020065928_thumb.png (382.4 KiB)
    2021-11-17 14:11:18,365 - 🛰️  Capella 🐐 - INFO - successfully downloaded to /Users/thomas.beyer/data/new_stuff/CAPELLA_C05_SP_GEC_HH_20211020065906_20211020065928/CAPELLA_C05_SP_GEO_HH_20211020065906_20211020065928_thumb.png
    2021-11-17 14:11:18,365 - 🛰️  Capella 🐐 - INFO - successfully downloaded to /Users/thomas.beyer/data/new_stuff/CAPELLA_C05_SP_SLC_HH_20211020065916_20211020065918/CAPELLA_C05_SP_GEO_HH_20211020065906_20211020065928_thumb.png

    ? Do you want to open any product directories? No


Update tasking requests
=======================

.. code:: console

    $ capella-console-wizard workflows manage-trs

users **with elevated permissions** will be prompted to select who they'd like to update tasking requests for

.. code:: console

    ? Update tasking requests of ? (Use arrow keys)
    » TrScopeOptions.user
      TrScopeOptions.org
      TrScopeOptions.admin

* `user`: tasking requests of current user will be searched
* `org`: tasking requests of current user's org will be searched (**requires elevated permissions**)
* `admin`: user_id / org_id will be prompted in previous step and used for search (**requires elevated permissions**)

After selecting scope, matching tasking requests are fetched and presented as a checkbox:

.. code:: console

    ? Update tasking requests of ? current user
    2026-02-16 14:39:42,023 - 🛰️  Capella 🐐 - INFO - searching tasking requests with payload ...
    2026-02-16 14:39:42,813 - 🛰️  Capella 🐐 - INFO - found 5 tasking requests matching search query
    ? Which tasking request? done (2 selections)

Select which fields to update (multi-select):

.. code:: console

    ? Which fields to update? (Use arrow keys to move, <space> to select, <a> to toggle, <i> to invert)
    » ● name
      ○ description
      ○ custom attribute 1
      ○ custom attribute 2
      ○ product types

Each selected field is then prompted individually:

.. code:: console

    ? new name: updated tasking request name

A confirmation prompt summarises the pending changes before any API call is made:

.. code:: console

    ? Apply the following updates:
      name: 'updated tasking request name'

    to 2 tasking request(s):
     - aaaaaaaa-b2ca-4a44-9362-0304025e149f
     - bbbbbbbb-b2ca-4a44-9362-0304025e149f
     Yes

.. code:: console

    ╒══════════════════════════════════════╤══════════╤══════════════════════════════╕
    │ tasking request id                   │ status   │ name                         │
    ╞══════════════════════════════════════╪══════════╪══════════════════════════════╡
    │ aaaaaaaa-b2ca-4a44-9362-0304025e149f │ ✅       │ updated tasking request name │
    ├──────────────────────────────────────┼──────────┼──────────────────────────────┤
    │ bbbbbbbb-b2ca-4a44-9362-0304025e149f │ ✅       │ updated tasking request name │
    ╘══════════════════════════════════════╧══════════╧══════════════════════════════╛


Cancel tasking requests
=======================

.. code:: console

    $ capella-console-wizard workflows manage-trs

users **with elevated permissions** will be prompted to select who they'd like to cancel tasking requests for

.. code:: console

    Cancel tasking requests of ? (Use arrow keys)
    » TrScopeOptions.user
      TrScopeOptions.org
      TrScopeOptions.admin


* `user`: cancelable tasking requests of current user will be searched
* `org`: cancelable tasking requests of current user's org will be searched (**requires elevated permissions**)
* `admin`: user_id / org_id will be prompted in previous step and used for search (**requires elevated permissions**)

.. code:: console

    ? Cancel tasking requests of ? current organization (requires elevated perms)
    2026-02-16 14:39:42,023 - 🛰️  Capella 🐐 - INFO - searching tasking requests with payload {'query': {'includeRepeatingTasks': {'eq': False}, 'organizationIds': ['2d98e85f-8c4b-4089-9faf-781277dd9282'], 'lastStatusCode': ['received', 'review', 'submitted', 'active', 'accepted']}}
    2026-02-16 14:39:42,813 - 🛰️  Capella 🐐 - INFO - found 18 tasking requests matching search query
    ? Which tasking request? done (3 selections)

    ? Please confirm you'd like to cancel the following tasking requests (cancelation charges might apply):

     - aaaaaaaa-b2ca-4a44-9362-0304025e149f
     - bbbbbbbb-b2ca-4a44-9362-0304025e149f
     - cccccccc-b2ca-4a44-9362-0304025e149f
     Yes
    ╒══════════════════════════════════════╤═════════════════╕
    │ tasking request id                   │ cancel status   │
    ╞══════════════════════════════════════╪═════════════════╡
    │ aaaaaaaa-b2ca-4a44-9362-0304025e149f │ ✅              │
    ├──────────────────────────────────────┼─────────────────┤
    │ bbbbbbbb-b2ca-4a44-9362-0304025e149f │ ✅              │
    ├──────────────────────────────────────┼─────────────────┤
    │ cccccccc-b2ca-4a44-9362-0304025e149f │ ✅              │
    ╘══════════════════════════════════════╧═════════════════╛
