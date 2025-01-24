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


``capella-console-client`` uses `Poetry <https://python-poetry.org/>`_ for packaging and
dependency management. If you want to build ``capella-console-client`` from source, you
need to install Poetry first:

.. code-block:: console

  $ curl -sSL https://install.python-poetry.org | python3 -

There are several other ways to install Poetry, as seen in
`the official guide <https://python-poetry.org/docs/#installation>`_.

To install ``capella-console-client`` and its dependencies in editable mode, execute

.. code-block:: console

  $ make install
