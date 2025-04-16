****************************
🛰️ Capella Console Client 🐐
****************************

.. image:: https://img.shields.io/pypi/v/capella-console-client.svg
  :target: https://pypi.org/project/capella-console-client/
  :alt: Version

.. image:: https://img.shields.io/pypi/l/capella-console-client.svg
  :target: #
  :alt: License

.. image:: https://img.shields.io/pypi/pyversions/capella-console-client.svg
  :target: https://pypi.python.org/pypi/capella-console-client
  :alt: Supported Python Versions


**capella-console-client** is the Python SDK for `api.capellaspace.com <https://api.capellaspace.com>`_ (task, search, order, download - `see API docs <https://docs.capellaspace.com/api/data-access>`_)

Installation
============

.. code-block:: console

  $ pip install capella-console-client

for more detail see the :ref:`installation` page

Requirements
============

* ``python >= 3.9 < 4.0``
* ``capella-console-client`` requires an active account on `console.capellaspace.com <https://console.capellaspace.com>`_. Sign up for an account on `the community page <https://www.capellaspace.com/community/>`_.


Usage
=====

.. image:: images/quickstart.gif

Check out the :ref:`quickstart`, the many examples in :ref:`example_usage` and the :ref:`api-reference`.

🧙‍capella-console-wizard 🧙‍♂️
===============================
starting with `capella-console-client>=0.8.0` the SDK ships with an interactive wizard-like CLI: ``capella-console-wizard``

.. code-block:: console

    $ pip install capella-console-client[wizard]
    $ capella-console-wizard --help


For more detail see :ref:`wizard`


License
=======
• Licensed under the `MIT License <https://github.com/capellaspace/console-client/blob/master/LICENSE>`_ • 2025 • Capella Space •

.. toctree::
   :hidden:

   pages/installation
   pages/quickstart
   pages/example_usage
   pages/wizard
   pages/api_reference
   pages/support

.. toctree::
   :hidden:

   pages/contributors

.. toctree::
   :hidden:

   pages/changelog
