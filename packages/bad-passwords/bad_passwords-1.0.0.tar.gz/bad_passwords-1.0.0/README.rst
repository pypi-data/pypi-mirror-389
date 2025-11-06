Bad passswords
==============

.. image:: https://img.shields.io/pypi/v/bad-passwords.svg
    :target: https://pypi.org/project/bad-passwords
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/bad-passwords.svg
    :target: https://pypi.org/project/bad-passwords
    :alt: Python versions

.. image:: https://github.com/seantis/bad-passwords/actions/workflows/python-tox.yaml/badge.svg
    :target: https://github.com/seantis/bad-passwords/actions
    :alt: Tests

.. image:: https://codecov.io/gh/seantis/bad-passwords/branch/main/graph/badge.svg?token=gMGL85OASa
    :target: https://codecov.io/gh/seantis/bad-passwords
    :alt: Codecov.io

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit

Tiny library containing a single function to check against the most common passwords.

Currently this list is fine-tuned for our purposes. It only contains passwords that are at
least 10 characters long. We source our passwords from https://github.com/danielmiessler/SecLists/tree/master/Passwords/Common-Credentials

Run the Tests
-------------

Install tox and run it::

    pip install tox tox-uv
    tox

Limit the tests to a specific python version::

    tox -e py311

Conventions
-----------

Sedate follows PEP8 as close as possible. To test for it run::

    tox -e lint

Bad passwords uses `Semantic Versioning <http://semver.org/>`_


Development
-----------

Setup your local development environment::

    python3 -m venv venv
    source venv/bin/activate
    pip install -e .[dev]
    pre-commit install

License
-------
Bad passwords is released under MIT
