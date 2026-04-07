.. _installation:

************
Installation
************

Use a Published Release
#######################

To install ``capella-console-client``, simply run this command in your terminal of
choice:

.. code-block:: console

  $ pip install capella-console-client

Build from Source
#################

.. code-block:: console

  $ git clone git@github.com:capellaspace/console-client.git

Or, via tarball:

.. code-block:: console

  $ curl -OL https://github.com/capellaspace/console-client/tarball/main

.. note::
  If you are using windows, you can also download a zip instead:

  .. code-block:: console

    $ curl -OL https://github.com/capellaspace/console-client/zipball/main


``capella-console-client`` uses `uv <https://docs.astral.sh/uv/>`_ for packaging and
dependency management. If you want to build ``capella-console-client`` from source, you
need to install uv first:

.. code-block:: console

  $ curl -LsSf https://astral.sh/uv/install.sh | sh

There are several other ways to install uv, as seen in
`the official guide <https://docs.astral.sh/uv/getting-started/installation/>`_.

To install ``capella-console-client`` and its dependencies in editable mode, execute

.. code-block:: console

  $ make install
