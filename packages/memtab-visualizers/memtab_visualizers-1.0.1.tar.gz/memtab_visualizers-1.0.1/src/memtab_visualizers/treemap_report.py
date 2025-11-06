# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""
Treemap Report for Memory Table Visualizers
===========================================

This module generates an interactive treemap visualization of Flash memory usage.

The treemap organizes memory items hierarchically:
- Top level: Categories (major code divisions)
- Middle level: Subcategories (logical groupings within categories)
- Lower levels: Files and individual symbols

Memory size calculation:
- Flash usage is calculated at every level of the hierarchy
- Category totals are sums of all contained subcategories
- Subcategory totals are sums of all contained files
- File totals are sums of all contained symbols within that category/subcategory context

Important: File sizes are calculated within their category/subcategory context.
If a file contains symbols that span multiple categories, the file size shown
within each category reflects only the symbols from that specific category,
not the total file size across all categories.

.. note:: If the ``assigned_size`` is less than or equal to the ``size``, the ``assigned_size`` parameter is used.
  Otherwise, the ``size`` parameter is used.

The visualization specifically targets Flash memory regions only, excluding RAM
and other memory types. Size values are displayed in bytes at each level of the
hierarchy to provide immediate insight into memory consumption patterns.

The output is an interactive HTML file that allows drilling down into memory
usage details.
"""

import os

from memtab import hookimpl as impl
from memtab.memtab import Memtab


class TreemapReport:
    """A Treemap Report"""

    report_name = "treemap"

    def __init__(self) -> None:
        self.ram_based = False

    @impl
    def generate_report(self, memtab: Memtab, filename: str) -> None:
        """This function generates a treemap visualization of the RAM/ROM items by category, subcategory, and filename.
        It uses the Plotly library to create the treemap and saves it as an HTML file.
        The treemap provides a visual representation of the memory usage by different categories and subcategories.
        The function first filters the data to include only items with "region": "ROM" or "RAM" based on self.ram_based.
        It then groups the data by category, subcategory, and filename or symbol, and calculates the size of each item.

        Args:
            memtab (Memtab): the Memtab instance containing memory items
            filename (str): the filename to save the report to
        """

        symbols_df = memtab.symbols

        # Filter the data to include only items with "region": "ROM"
        if self.ram_based:
            symbols = symbols_df[symbols_df["region"] == "RAM"]
        else:
            symbols = symbols_df[symbols_df["region"] == "Flash"]

        # Group the data by category, subcategory, and filename or symbol
        grouped_data = []
        category_sizes = {}
        subcategory_sizes = {}
        file_sizes = {}

        for _, item in symbols.iterrows():
            category = item.categories["0"]
            try:
                subcategory = item.categories["1"]
            except KeyError:
                subcategory = "None"
            filename = os.path.basename(item["file"]) if item["file"] else item["symbol"]
            if item["assigned_size"] <= item["size"]:
                size = item["assigned_size"]
            else:
                size = item["size"]

            if category not in category_sizes:
                category_sizes[category] = 0
            category_sizes[category] += size

            if (category, subcategory) not in subcategory_sizes:
                subcategory_sizes[(category, subcategory)] = 0
            subcategory_sizes[(category, subcategory)] += size

            # Use a tuple of (category, subcategory, filename) to track file sizes within context
            file_key = (category, subcategory, filename)
            if file_key not in file_sizes:
                file_sizes[file_key] = 0
            file_sizes[file_key] += size

            grouped_data.append(
                {
                    "category": category,
                    "subcategory": subcategory,
                    "filename": filename,
                    "symbol": item.symbol,
                    "size": size,
                }
            )

        if not grouped_data:
            print("No Flash memory items found for treemap report.")
            return

        # Update category and subcategory labels with sizes
        for gd_item in grouped_data:
            gd_category: str = str(gd_item["category"])
            gd_subcategory: str = str(gd_item["subcategory"])
            gd_filename: str = str(gd_item["filename"])
            file_key = (gd_category, gd_subcategory, gd_filename)
            gd_item["category"] = f"{gd_category} ({category_sizes[gd_category]} bytes)"
            gd_item["subcategory"] = f"{gd_subcategory} ({subcategory_sizes[(gd_category, gd_subcategory)]} bytes)"
            gd_item["filename"] = f"{gd_filename} ({file_sizes[file_key]} bytes)"

        # region report
        import plotly.express as px

        fig = px.treemap(
            grouped_data,
            path=["category", "subcategory", "filename", "symbol"],
            values="size",
            title=f"{'RAM' if self.ram_based else 'Flash'} Items by Category, Subcategory, Filename, and Symbol",
        )
        filename = str(memtab.elf_metadata["filename"]).replace(".elf", f"_{self.report_name}.html")
        # Get just the base filename without the path
        base_filename = os.path.basename(filename)
        # Prepend the current working directory
        filename = os.path.join(os.getcwd(), base_filename)
        fig.write_html(filename)
        # endregion report
