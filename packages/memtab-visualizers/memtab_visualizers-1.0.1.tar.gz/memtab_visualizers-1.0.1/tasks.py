# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Disparate tasks to support development and testing."""

from invoke import context, task


@task
def get_version(c: context) -> None:
    import toml

    with open("pyproject.toml", "r") as f:
        data = toml.load(f)
        print(data["project"]["version"])
