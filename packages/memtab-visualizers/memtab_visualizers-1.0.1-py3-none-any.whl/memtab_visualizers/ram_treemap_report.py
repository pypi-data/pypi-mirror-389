# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""RAM Treemap Report class for memtab visualizers."""

from .treemap_report import TreemapReport


class RAMTreemapReport(TreemapReport):
    """RAM Treemap Report.

    This class extends :class:`TreemapReport` to provide a RAM-specific treemap
    visualization, focusing on RAM memory usage by category, subcategory, and filename.

    The report shows RAM memory usage organized by memory region categories,
    helping users understand how RAM is allocated across different types of regions.

    See Also
    --------
    :class:`TreemapReport` : Base class that provides treemap reporting functionality.
    """

    report_name = "ramtreemap"

    def __init__(self) -> None:
        super().__init__()
        self.ram_based = True  # override
