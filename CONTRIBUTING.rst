Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

Types of Contributions
----------------------

Report issues / contacting developers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Report bugs on our issue tracker_.

If you want to submit a bug, improvement or feature suggestions feel free to open a
corresponding issue on GitHub.

If you are reporting a bug, please help us to speed up the diagnosing a problem
by providing us with as much as information as possible.
Ideally, that would include a step by step process on how to reproduce the bug.

.. _tracker: https://github.com/SwissDataScienceCenter/calamus/issues

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for proposal discussions or epics and feel free to
express your proposal on the topic. Once topic has been flushed out and we have
decided how feature should be implemented, we can start implementing them.


Improvement requests
~~~~~~~~~~~~~~~~~~~~

If you see room for improvement, please open an issue with a suggestion.
Please motivate your suggestion by illustrating a problem it solves.

Write Documentation
~~~~~~~~~~~~~~~~~~~

calamus could always use more documentation, whether as part of the
official calamus docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at
https://github.com/SwissDataScienceCenter/calamus/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `calamus` for local development.

1. Fork the `SwissDataScienceCenter/calamus` repo on GitHub.
2. Clone your fork locally:

   .. code-block:: console

      $ git clone git@github.com:your_name_here/calamus.git

3. Ensure you have your development environment set up. For this we
encourage usage of `poetry`:

   .. code-block:: console

      $ poetry install
      $ poetry shell

4. Create a branch for local development:

   .. code-block:: console

      $ git checkout -b <issue_number>_<short_description>

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass tests:

   .. code-block:: console

      $ poetry run pytest

   Before you submit a pull request, please reformat the code using black_.

   .. code-block:: console

      $ black

   You may want to set up yapf_ styling as a pre-commit hook to do this
   automatically:

   .. code-block:: console

      $ poetry run pre-commit install

   .. _yapf: https://github.com/psf/black

6. Commit your changes and push your branch to GitHub:

   .. code-block:: console

      $ git add .
      $ git commit -s
          -m "type(scope): title without verbs"
          -m "* NEW Adds your new feature."
          -m "* FIX Fixes an existing issue."
          -m "* BETTER Improves and existing feature."
          -m "* Changes something that should not be visible in release notes."
      $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.


Commit message guidelines
-------------------------

This project is using conventional_ commits style for generation of changelog upon
each release. Therefore, it's important that our commit messages convey what they
do correctly. Commit message should always follow this pattern:

.. _conventional: https://www.conventionalcommits.org/en/v1.0.0/

   $ %{type}: %{description}

**Type's used for describing commit's which will end up in changelog are** :code:`fix:` & :code:`feat:`.

Please note that the :code:`fix` type here is only for user-facing bug fixes and not fixes on tests or CI.
For those, please use: :code:`ci:` or :code:`test:`

Full list of types which are in use:
  * :code:`feat:` - Used for new user-facing features.
  * :code:`fix:` - Used for fixing user-facing bugs.
  * :code:`chore:` - Used for changes which are not user-facing.
  * :code:`tests:` - Used for fixing existing or adding new tests.
  * :code:`docs:` - Used for adding more documentation.
  * :code:`refactor` - Used for changing the code structure.


Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

* Make sure you agree with the license and follow the legal_ matter.
* The pull request should include tests and must not decrease test coverage.
* If the pull request adds functionality, the docs should be updated. Put your new functionality into a function with a docstring.
* The pull request should work for Python 3.6, 3.7 and 3.8. Check GitHub action builds and make sure that the tests pass for all supported Python versions.

.. _legal: (https://github.com/SwissDataScienceCenter/documentation/wiki/Legal-matter)
