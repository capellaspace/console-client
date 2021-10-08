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
    ? Specify the default location for your downloads and .json STAC exports: (press <tab>) /Users/thomas.beyer
    updated default output path for .json STAC exports
    ? Which STAC item fields would you like to display in the search results table? done (9 selections)
    updated fields that to will be displayed in search results table
    ? Speciy default limit to be used in searches (can be overridden at search time): 100
    updated default search limit to 100


Interactive search
==================

.. code:: console

    $ capella-console-wizard search interactive