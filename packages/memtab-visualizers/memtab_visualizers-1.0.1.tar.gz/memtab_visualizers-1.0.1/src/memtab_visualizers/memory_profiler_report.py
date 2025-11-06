# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Memory Profiler Report class for memtab visualizers."""

from memtab import hookimpl as impl
from memtab.memtab import Memtab
from pandas import DataFrame
from typing_extensions import Dict


class MemoryProfilerReport:
    """A memory profiler report class for memtab visualizers."""

    report_name = "memoryprofiler"

    @impl
    def generate_report(self, memtab: Memtab, filename: str) -> None:
        """Generate a text based memory profile, showing overall RAM and ROM,
        and then the different categories as a total in KB, and then % of RAM/ROM total

        """

        symbols_df = memtab.symbols

        # Calculate total ROM and RAM
        rom_symbols = symbols_df[symbols_df["region"] == "Flash"]
        ram_symbols = symbols_df[symbols_df["region"] == "RAM"]

        # Use the same assigned_size vs. size logic from treemap
        # If assigned_size <= size, use assigned_size, otherwise use size
        rom_effective_sizes = rom_symbols["assigned_size"].where(rom_symbols["assigned_size"] <= rom_symbols["size"], rom_symbols["size"])
        ram_effective_sizes = ram_symbols["assigned_size"].where(ram_symbols["assigned_size"] <= ram_symbols["size"], ram_symbols["size"])

        total_rom = rom_effective_sizes.sum() / 1024  # Convert to KB
        total_ram = ram_effective_sizes.sum() / 1024  # Convert to KB

        def __build_cat_data_dict(symbols_df: DataFrame) -> Dict[str, Dict[str, int]]:
            """Group by categories and calculate ROM and RAM usage"""
            data: Dict[str, Dict[str, int]] = {}
            for _, item in symbols_df.iterrows():
                category = item.categories["0"]

                # Use the same assigned_size vs. size logic from treemap
                if item["assigned_size"] <= item["size"]:
                    size_to_use = item["assigned_size"]
                else:
                    size_to_use = item["size"]

                rom_size = size_to_use / 1024 if item["region"] == "Flash" else 0
                ram_size = size_to_use / 1024 if item["region"] == "RAM" else 0

                if category in data:
                    data[category]["rom"] += rom_size
                    data[category]["ram"] += ram_size
                else:
                    data[category] = {"rom": rom_size, "ram": ram_size}
            return data

        category_data = __build_cat_data_dict(symbols_df)

        # region report
        print("+" * 90)
        print("+")
        print(f"+    Project   :   {memtab.elf_metadata['filename']}")
        print("+")
        print("+" * 90)
        print("\nAll Memory profiling readings are mentioned in Kilobytes (KB)\n")
        print("_" * 90)
        print(f"ROM (KB)            {total_rom:.2f}")
        print("_" * 90)
        print(f"RAM (KB)            {total_ram:.2f}")
        print("_" * 90)
        print("HEAP (KB)           0")
        print("_" * 90)
        print("CSTACK (KB)         0.05")
        print("_" * 90)
        print(f"{'Module':<20}{'ROM Profile (KB)':<20}{'ROM Profile(%)':<20}{'RAM Profile (KB)':<20}{'RAM Profile(%)':<20}")
        print("_" * 90)

        for category, entry in category_data.items():
            rom_percentage = (entry["rom"] / total_rom) if total_rom > 0 else 0
            ram_percentage = (entry["ram"] / total_ram) if total_ram > 0 else 0
            print(f"{category:<20}{entry['rom']:<20.2f}{rom_percentage:<20.1%}{entry['ram']:<20.2f}{ram_percentage:<20.1%}")
            print("_" * 90)
        # endregion report
