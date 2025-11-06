#########################################
Memtab Visualizers
#########################################

Welcome!

----

Documentation: https://etn-corp.github.io/memtab-visualizers/

Source Code: https://github.com/etn-corp/memtab-visualizers

----



`memtab-visualizers` is a Python-based project that provides both a command line interface (CLI) and a Python library.
## Features


- Command Line Interface (CLI)

- Python library

**************
Installation
**************

To install `memtab-visualizers`, you can use `pip`:

.. code-block:: sh

   pip install git+https://github.com/etn-corp/memtab-visualizers


**************
Usage
**************

Command Line Interface
=======================

To get these new reports, add the appropriate `--report` argument to `memtab` after installing this package:

.. code-block:: sh

   memtab --elf xyz.elf --config xyz.yml --report [treemap|categorymemmap|excel|memmap|markdown|memoryprofiler|summary]

Python Library
==============

To use the Python library:

.. code-block:: python

   import memtab_visualizers

***********
Developing
***********

This project is managed using `uv`. For more information, refer to `Astral's page on uv <https://astral.sh/uv/>`.

Common Commands
================

- `uv sync`: Sync your development environment with the project dependencies.
- `uv run <command>`: Run a command within the project's virtual environment.
- `uv build`: generate a pip installable wheel or sdist file in the `dist/` directory.

Running Tests
=============

To run tests, use `uv` with coverage:

.. code-block:: sh

   uv run coverage run -m pytest

Staying synced up to memtab
===========================

If the `memtab` package has updated, run the following to update uv:

.. code-block:: sh

   uv sync --reinstall-package memtab --upgrade

Pre-commit Hooks
=================

We use `pre-commit` to ensure code quality and consistency. After cloning the project, install the pre-commit hooks by running:

.. code-block:: sh

   pre-commit install

For more information on `pre-commit`, visit the `pre-commit website <https://pre-commit.com/>`.

We also have a GitHub Action that runs `pre-commit` checks on every push and pull request, so you can rely on that if you prefer not to install `pre-commit` locally.


Contribution Guidelines
=======================

We welcome contributions! Please follow these guidelines:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -am 'Add new feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Create a new Pull Request.

******************
Reporting Issues
******************

If you encounter any issues, please report them on the `GitHub Issues <https://github.com/yourusername/memtab-visualizers/issues>`_ page.


************************
Generating Documentation
************************

To generate documentation, use `Sphinx`:

.. code-block:: sh

   cd docs/
   sphinx-apidoc -o . ../src/memtab-visualizers/


Now hand-edit the generated files to fix the paths (adding `memtab-visualizers.`), and then run:

.. code-block:: sh

   make html


****************
License
****************

This project is licensed under the MIT License. See the `LICENSE file <https://github.com/etn-corp/memtab-visualizers/blob/main/LICENSE>`_ for more information.
