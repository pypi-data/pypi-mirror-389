# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Category Memory Map Report class for memtab visualizers."""

from .memmap_report import MemmapReport


class CategoryMemmapReport(MemmapReport):
    """Category Memory Map Report.

    This class extends :class:`MemmapReport` to provide a category-based memory
    map visualization, where memory regions are grouped by category.

    The report shows memory usage organized by memory region categories, helping
    users understand how memory is allocated across different types of regions.

    See Also
    --------
    :class:`MemmapReport` : Base class that provides memory map reporting functionality.
    """

    """"""

    report_name = "categorymemmap"

    def __init__(self) -> None:
        super().__init__()
        self.category_based = True  # override
