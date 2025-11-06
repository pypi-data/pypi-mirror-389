# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Memtab Visualizers feature tests."""

import logging
import os
from functools import partial
from glob import glob
from pathlib import Path
from typing import Generator, List

import pandas as pd
from click.testing import Result
from pytest import CaptureFixture, FixtureRequest, fixture
from pytest_bdd import given, parsers, scenario, then, when
from typer import Typer
from typer.testing import CliRunner

####################
# boilerplate to shorten the scenario names
####################
feature_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../features")
scenario = partial(scenario, os.path.join(feature_dir, "Memtab Visualizers.feature"))

root_dir = os.path.dirname(os.path.abspath(__file__))


################################
# Generic Test Fixtures
################################
@fixture(scope="module", autouse=True, params=glob(os.path.join(root_dir, "inputs", "*.elf")))
def uut(request: FixtureRequest) -> Generator[str, None, None]:
    """Fixture to provide all ELF files for this test module.
    Since this fixture has a "params" list, per pytest
    (https://docs.pytest.org/en/6.2.x/fixture.html#parametrizing-fixtures)
    this creates a unique test case for each ELF file found in the tests/ directory."""
    yield request.param


def check_file_contents_for_accuracy(file_pattern: str) -> None:
    """Helper function to check file contents for accuracy."""
    files = list(Path.cwd().glob(file_pattern))
    assert files, f"No files matching pattern '{file_pattern}' were found in the current working directory"
    for file in files:
        if "xlsx" in file.name:
            # Reading all sheets into a dictionary of DataFrames
            excel_data = pd.read_excel(file, sheet_name=None)

            # Basic validation that the Excel file has data
            assert excel_data, f"{file} has no sheets"

            # Check that at least one sheet has data
            has_data = False
            for sheet_name, df in excel_data.items():
                if not df.empty:
                    has_data = True
                    break

            assert has_data, f"{file} has no data in any sheet"

        else:
            with open(file, "r") as f:
                content = f.read()
                assert content, f"{file} is empty"
                # Placeholder for actual content validation logic
                logging.debug(f"Checked contents of {file} for accuracy.")


def check_stdout_for_accuracy(stdout: str) -> None:
    """Helper function to check stdout for accuracy."""
    assert stdout, "The command output is empty"
    # Placeholder for actual content validation logic
    logging.debug("Checked stdout for accuracy.")


################################
# BDD Scenarios
################################
@scenario("Memtab Visualizers")
def test_memtab_visualizers() -> None:
    """Memtab Visualizers."""


################################
# BDD Given Statements
################################
@given("the memtab utility", target_fixture="command")
def _() -> Generator[Typer, None, None]:
    """the memtab utility."""
    from memtab.cli import app

    yield app


@given("valid ELF files", target_fixture="elf")
def _(uut: str) -> Generator[str, None, None]:
    """valid ELF files.

    This BDD fixture leverages a second pytest fixture 'uut'.
    It was done this way because vanilla pytest fixtures can be parameterized, to create test multiplicity, but BDD fixtures cannot.
    This technique lets us avoid listing out each elf file manually in the feature file."""
    yield uut


################################
# BDD When Statements
################################
@when(parsers.re("a (?P<report>[a-zA-Z-]+) is requested"), target_fixture="report_output")
def _(command: Typer, report: str, elf: str, capsys: CaptureFixture) -> Generator[Result, None, None]:
    """a report is requested."""
    yml = elf.replace(".elf", ".yml")
    yml = yml.replace("inputs", "configs")
    runner = CliRunner()
    args: List[str] = [
        "--cache",
        "--elf",
        elf,
        "--config",
        yml,
        "--report",
        report,
    ]
    with capsys.disabled():  # this is needed so stdout/logging can be captured by the runner, instead of pytest.
        yield runner.invoke(command, args, catch_exceptions=False, color=True)

    # Clean up memtab.json file that gets created during test runs
    memtab_json = Path.cwd() / "memtab.json"
    if memtab_json.exists():
        os.remove(str(memtab_json))
        logging.debug(f"Cleaned up {memtab_json}")

    # clean up the generated report files
    file_type_lookup = {
        "excel": "*.xlsx",
        "memoryprofiler": None,
        "treemap": "*_treemap.html",
        "ramtreemap": "*_ramtreemap.html",
        "categorymemmap": "*_category_memmap.html",
        "memmap": "*_memmap.html",
        "summary": None,
    }
    file_pattern = file_type_lookup.get(report)
    if file_pattern:
        files = list(Path.cwd().glob(file_pattern))
        for file in files:
            os.remove(str(file))
            logging.debug(f"Cleaned up {file}")


################################
# BDD Then Statements
################################
@then(parsers.re("a (?P<report>[a-zA-Z-]+) shall be produced"))
def _(report_output: Result, report: str) -> None:
    """a report shall be produced."""

    def check_report_files(file_pattern: str) -> None:
        """Helper function to check report files."""
        files = list(Path.cwd().glob(file_pattern))
        assert files, f"No files matching pattern '{file_pattern}' were found in the current working directory"
        for file in files:
            assert file.is_file(), f"{file} is not a file"
            assert file.stat().st_size > 0, f"{file} is empty"

    def check_stdout(stdout: str) -> None:
        """Helper function to check stdout."""
        assert stdout, "The command output is empty"
        assert stdout.strip(), "The command output is only whitespace"

    # Define report validation strategies
    file_pattern_reports = {
        "excel": "*.xlsx",
        "treemap": "*_treemap.html",
        "ramtreemap": "*_ramtreemap.html",
        "categorymemmap": "*_category_memmap.html",
        "memmap": "*_memmap.html",
    }

    stdout_reports = {"memoryprofiler", "summary"}

    if report in file_pattern_reports:
        check_report_files(file_pattern_reports[report])
    elif report in stdout_reports:
        check_stdout(report_output.stdout)
    else:
        raise NotImplementedError(f"Report type '{report}' is not implemented in the test suite.")


@then(parsers.re("the (?P<report>[a-zA-Z-]+) shall contain accurate information"))
def _(report_output: Result, report: str) -> None:
    """the report shall contain accurate information."""

    if report == "excel":
        check_file_contents_for_accuracy("*.xlsx")
    elif report == "memoryprofiler":
        check_stdout_for_accuracy(report_output.stdout)
    elif report == "treemap":
        check_file_contents_for_accuracy("*_treemap.html")
    elif report == "ramtreemap":
        check_file_contents_for_accuracy("*_ramtreemap.html")
    elif report == "categorymemmap":
        check_file_contents_for_accuracy("*_category_memmap.html")
    elif report == "memmap":
        check_file_contents_for_accuracy("*_memmap.html")
    elif report == "summary":
        check_stdout_for_accuracy(report_output.stdout)
    else:
        raise NotImplementedError(f"Report type '{report}' is not implemented in the test suite.")
