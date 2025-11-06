# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Memory Map Report class for memtab visualizers."""

import os
from typing import List, Tuple

import pandas as pd
import plotly.graph_objects as go
from memtab import hookimpl as impl
from memtab.memtab import Memtab
from plotly.subplots import make_subplots


class MemmapReport:
    """
    MemmapReport
    ===========

    A class that generates memory map visualizations based on analysis results.

    The ``MemmapReport`` class creates interactive memory map visualizations using the Plotly library,
    showing the memory layout of code from a Memtab object. It can display memory maps based on
    either categories or ELF sections.
    """

    report_name = "memmap"

    def __init__(self) -> None:
        self.category_based = False

    @impl
    def generate_report(self, memtab: Memtab, filename: str) -> None:
        """This function generates a memory map visualization based on the analysis results.
        It uses the Plotly library to create the memory map and saves it as an HTML file.
        The memory map provides a visual representation of the memory layout of the code.
        The function first determines whether to use category-based or section-based memory mapping.
        It then iterates through the unique categories or sections and creates scatter plots for each region.
        The scatter plots represent the memory regions, symbols, and extra space between symbols.

        Args:
            response (DataFrame): _description_
            html (str): the html filename.  this gets prepended with `category_memmap_` or `section_memmap_` depending on the category_based flag.
            category_based (bool, optional): _description_. Defaults to False.
            If True, the memory map is based on categories. If False, it is based on sections.
        """
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True)
        response = memtab.symbols
        response_key = "categories" if self.category_based else "elf_section"
        loop_keys = self.__get_region_keys(response, response_key)

        region_x_min, region_x_max = -0.5, 2.5
        region_x_bounds = [region_x_min, region_x_min, region_x_max, region_x_max, region_x_min]
        symbol_x_min, symbol_x_max = 0, 2
        symbol_x_bounds = [symbol_x_min, symbol_x_min, symbol_x_max, symbol_x_max, symbol_x_min]

        for key_idx, key_name in enumerate(loop_keys):
            region_mask = self.__get_region_mask(response, response_key, key_name)
            region_symbols = response.loc[region_mask, "symbol"].to_list()
            region_sizes = response.loc[region_mask, "size"].to_list()
            region_effective_sizes = response.loc[region_mask, "assigned_size"].to_list()
            region_addresses = response.loc[region_mask].index.to_list()

            item, row = self.__get_category_scatter_plot(fig, key_idx, key_name, region_addresses, region_x_bounds, region_x_min, region_x_max)
            fig.add_trace(item, row=row, col=1)

            for idx in range(len(region_sizes)):
                base_addr, symbol_scatter, effective_size_scatter = self.__get_symbol_scatter_plots(
                    fig, key_idx, idx, region_addresses, region_sizes, region_effective_sizes, region_symbols, key_name, symbol_x_bounds
                )
                row = 1 if base_addr >= 50000000 else 2
                fig.add_trace(symbol_scatter, row=row, col=1)
                fig.add_trace(effective_size_scatter, row=row, col=1)

        template = "plotly_dark"
        fig.update_layout(
            template=template,
            xaxis={"range": [-1, 3], "showticklabels": False, "fixedrange": True},
            yaxis={"tickformat": "0xX"},
            xaxis2={"range": [-1, 3], "showticklabels": False, "fixedrange": True},
            yaxis2={"tickformat": "00xX"},
            title="Memory Map",
        )
        filename = str(memtab.elf_metadata["filename"]).replace(".elf", "_category_memmap.html" if self.category_based else "_memmap.html")
        base_filename = os.path.basename(filename)
        filename = os.path.join(os.getcwd(), base_filename)
        fig.write_html(filename)

    def __get_region_keys(self, response: pd.DataFrame, key: str) -> List[str]:
        """
        Get the unique region keys from the response dataframe.

        Args:
            response: DataFrame containing symbol information
            key: Column name to get unique values from ('categories' or 'elf_section')

        Returns:
            List of unique region keys
        """
        if self.category_based:
            return [str(x) for x in response[key].apply(lambda x: x["0"]).unique().tolist()]
        return [str(x) for x in response[key].unique().tolist()]

    def __get_region_mask(self, response: pd.DataFrame, key: str, key_name: str) -> pd.Series:
        """
        Get a boolean mask for the dataframe rows that match the given key name.

        Args:
            response: DataFrame containing symbol information
            key: Column name to filter on ('categories' or 'elf_section')
            key_name: Value to match in the key column

        Returns:
            Boolean mask series to filter the dataframe
        """
        if self.category_based:
            return response[key].apply(lambda x: x["0"] == key_name)
        return response[key] == key_name

    def __get_category_scatter_plot(
        self, fig: go.Figure, key_idx: int, key_name: str, region_addresses: List[int], region_x_bounds: List[float], region_x_min: float, region_x_max: float
    ) -> Tuple[go.Scatter, int]:
        if not self.category_based:
            max_addr = max(region_addresses)
            min_addr = min(region_addresses)
            region_y_list = [min_addr, max_addr, max_addr, min_addr, min_addr]
            item = go.Scatter(
                x=region_x_bounds,
                y=region_y_list,
                name=key_name,
                mode="text",
                fill="toself",
                legendgroup=key_name,
            )
            row = 1 if max_addr >= 50000000 else 2
        else:
            fillcolor = fig.layout.template.layout.colorway[key_idx % len(fig.layout.template.layout.colorway)]
            item = go.Scatter(
                x=[(region_x_min + region_x_max) / 2],
                y=[0],
                name=key_name,
                mode="markers",
                legendgroup=key_name,
                showlegend=True,
                marker={"color": fillcolor},
            )
            row = 2
        return item, row

    def __get_symbol_scatter_plots(
        self,
        fig: go.Figure,
        key_idx: int,
        idx: int,
        region_addresses: List[int],
        region_sizes: List[int],
        region_effective_sizes: List[int],
        region_symbols: List[str],
        key_name: str,
        symbol_x_bounds: List[int],
    ) -> Tuple[int, go.Scatter, go.Scatter]:
        base_addr = region_addresses[idx]
        symbol_end_addr = int(base_addr + region_sizes[idx])
        effective_size_end_addr = int(base_addr + region_effective_sizes[idx])
        symbol_y_list = [base_addr, symbol_end_addr, symbol_end_addr, base_addr, base_addr]
        symbol_effective_size_y_list = [
            symbol_end_addr,
            effective_size_end_addr,
            effective_size_end_addr,
            symbol_end_addr,
            symbol_end_addr,
        ]
        symbol_name = region_symbols[idx][:20]
        symbol_scatter = go.Scatter(
            x=symbol_x_bounds,
            y=symbol_y_list,
            name=symbol_name,
            mode="none",
            fill="toself",
            legendgroup=key_name,
            showlegend=False,
        )
        effective_size_scatter = go.Scatter(
            x=symbol_x_bounds,
            y=symbol_effective_size_y_list,
            name=symbol_name + " effective size",
            mode="none",
            fill="toself",
            legendgroup=key_name,
            showlegend=False,
        )
        if self.category_based:
            fillcolor = fig.layout.template.layout.colorway[key_idx % len(fig.layout.template.layout.colorway)]
            symbol_scatter.fillcolor = fillcolor
            effective_size_scatter.fillcolor = fillcolor
        return base_addr, symbol_scatter, effective_size_scatter
