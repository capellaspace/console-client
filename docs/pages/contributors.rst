*******************
Contributor's Guide
*******************

Steps for Submitting Code
#########################
Contributions are very much welcomed and appreciated. Every little bit of help
counts, so please do not hesitate!

1. Check for open issues, or open a new issue to start some discussion around
   a feature idea or bug.

2. Fork `the repository <https://github.com/capellaspace/console-client>`_ on GitHub to
   start making your changes.

3. Write tests that show the bug is fixed or that the feature works as
   expected.

4. Ensure your code passes the style checks by running

  .. code-block:: console

    $ black capella_console_client

5. Check all of the unit tests pass by running

  .. code-block:: console

    $ pytest --cov capella_console_client --cov-report=html -sv

6. Check the type checks pass by running

  .. code-block:: console

    $ mypy capella_console_client

7. Send a pull request and bug the maintainer until it gets merged and
   published 🙂


Bug Reports
###########

Bug reports should be made to the
`issue tracker <https://github.com/capellaspace/console-client/issues>`_.
Please include enough information to reproduce the issue you are having.
A `minimal, reproducible example <https://stackoverflow.com/help/minimal-reproducible-example>`_
would be very helpful.

Feature Requests
################

Feature requests should be made to the
`issue tracker <https://github.com/capellaspace/console-client/issues>`_.