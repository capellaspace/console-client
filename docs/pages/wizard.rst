.. _wizard:

**********************
capella-console-wizard 
**********************

Starting with ``capella-console-client>=0.8.0`` this package ships with an interactive wizard


Installation
============

.. code:: console

    $ pip install capella-console-client[wizard]


.. code:: 

    capella-console-wizard --help

Configure
=========

.. code:: console

    $ capella-console-wizard configure
    2021-10-07 15:01:22,936 - 🛰️  Capella Space 🐐 - INFO - let's get you all setup using capella-console-wizard:
    2021-10-07 15:01:22,936 - 🛰️  Capella Space 🐐 - INFO - 		Press Ctrl + C anytime to quit

    ? User on console.capellaspace.com (user@email.com): thomas.beyer@capellaspace.com
    updated user for Capella Console
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

``capella-console-wizard`` allows to perform common interactive workflows (search, order, download). The following sections describe a subset of those


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
   ● datetime
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
 » ● product_category
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