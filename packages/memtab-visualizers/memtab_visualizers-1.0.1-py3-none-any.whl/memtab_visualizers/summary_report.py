# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Summary Report class for memtab visualizers."""

from memtab import hookimpl as impl
from memtab.memtab import Memtab
from tabulate import tabulate


class SummaryReport:
    """A command line summary"""

    report_name = "summary"

    @impl
    def generate_report(self, memtab: Memtab, filename: str) -> None:
        """Write a simple, couple-line summary out to stdout.
        This should be similar to the gnu binutils size command.

        Args:
            memtab (Any): the memory table to summarize
        """
        symbols_df = memtab.symbols

        code_symbols = symbols_df[symbols_df["memory_type"] != "bss"]
        ram_symbols = symbols_df[symbols_df["memory_type"] == "data"]
        bss_symbols = symbols_df[(symbols_df["elf_section"] == "bss") | (symbols_df["elf_section"] == "noinit")]
        text = code_symbols["assigned_size"].sum()
        data = ram_symbols["assigned_size"].sum()
        bss = bss_symbols["assigned_size"].sum()
        dec = text + data + bss
        hex_str = f"{dec:x}"
        table = [
            ["text", "data", "bss", "dec", "hex", "filename"],
            [text, data, bss, dec, hex_str, memtab.elf_metadata["filename"]],
        ]

        print(tabulate(table, headers="firstrow", tablefmt="plain"))  # this gets it acceptably close to the `size` command output
