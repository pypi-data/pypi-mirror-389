# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for XLSXResultExporterListing class
"""

import pathlib
from typing import List, Optional
import pandas

from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.exporter.xlsx.xlsx_exporter import XLSXExporter
from availsim4core.src.results.simulation_results import SimulationResults


class XLSXComponentListing(XLSXExporter):
    """
    This class defines an XLSX exporter which prints a list of components into the output file
    """

    @staticmethod
    def component_listing_export(root_component: Component):
        """
        Function exploring the system in order to build a list of components in the system.
        """

        ret = ""

        for component in root_component.to_set():

            if component.get_children():
                # if that component has children (then it is a Compound type), apply the same function to the children
                ret += f"{component.name};{component.local_id};{component.global_id}; compound;" \
                       f" -; -; -; {[x.name for x in component.list_of_mru_trigger]}\n"
            else:
                # else, the current component is a basic and has failure mode(s), those a printed
                ret += f"{component.name};{component.local_id};{component.global_id}; basic;" \
                       f"{component.failure_mode.name}; " \
                       f"{component.failure_mode.failure.type_of_failure}; " \
                       f"{[x.name for x in component.list_of_mru_group]}; " \
                       f"{[x.name for x in component.list_of_mru_trigger]}\n"

        return ret

    def export(self, _: Optional[SimulationResults] = None) -> List[pathlib.Path]:
        tree_string = self.component_listing_export(self.root_component)
        tree_dataframe = pandas.DataFrame([x.split(';') for x in tree_string.split('\n')],columns=[
            "COMPONENT_NAME", "local_id", "global_id", "COMPONENT_TYPE",
            "FAILURE_MODE_NAME", "TYPE_OF_FAILURE",
            "IN_MRU", "TRIGGER_MRU"
        ])

        filepath = self.export_dataframe(tree_dataframe, 'RESULTS_COMPONENT_LISTING')
        return [filepath]
