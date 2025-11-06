# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Excel Report class for memtab visualizers."""

import os

import pandas as pd
from memtab import hookimpl as impl
from memtab.memtab import Memtab
from pandas import DataFrame


class ExcelReport:
    """An Excel report generator for Memtab data.

    This class creates Excel workbooks from memory table data, with separate
    worksheets for symbols and regions.

    .. note::
        The output Excel file will be named after the input ELF file, with the
        extension changed from `.elf` to `.xlsx`, and will be saved in the
        current working directory.

    Output Format
    -------------
    The generated Excel file contains:

    * A "Symbols" worksheet containing all symbol information from the Memtab
    * A "Regions" worksheet containing all memory region information from the Memtab

    Example
    -------
    >>> report = ExcelReport()
    >>> report.generate_report(memtab, "output.xlsx")
    # Creates an Excel file in the current directory with the Memtab data
    """

    report_name = "excel"

    @impl
    def generate_report(self, memtab: Memtab, filename: str) -> None:
        """creates an excel workbook from the symbols and regions dataframes

        Args:
            memtab (Memtab): the memory table to write to excel
            excel (str): the excel filename
        """
        filename = str(memtab.elf_metadata["filename"]).replace(".elf", ".xlsx")
        # Get just the base filename without the path
        base_filename = os.path.basename(filename)
        # Prepend the current working directory
        filename = os.path.join(os.getcwd(), base_filename)
        writer = pd.ExcelWriter(filename, engine="openpyxl")
        DataFrame().from_dict(memtab.symbols).to_excel(writer, sheet_name="Symbols")
        DataFrame().from_dict(memtab.regions).to_excel(writer, sheet_name="Regions")
        writer.close()
