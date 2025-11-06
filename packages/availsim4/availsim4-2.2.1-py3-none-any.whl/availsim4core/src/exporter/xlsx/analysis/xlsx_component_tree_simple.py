# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for XLSXResultExporterComponentTreeSimple class
"""

import pathlib
from typing import List, Optional
import pandas

from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.exporter.xlsx.xlsx_exporter import XLSXExporter
from availsim4core.src.results.simulation_results import SimulationResults


class XLSXComponentTreeSimple(XLSXExporter):
    """
    This class defines an XLSX exporter printing a simple tree into the output file.
    """


    def export(self, _: Optional[SimulationResults] = None) -> List[pathlib.Path]:

        def component_tree_simple_export(component: Component, level=0):
            """
            Function recursively exploring the system in order to build a graphical representation of the system.
            This "simple" version of the tree exporter provides a "light" output. A "extended" version exists too.
            The function is called on the root component. Then if a component has children, it is called again for its
            children.
            """

            # line printed in the output for the current component
            ret = (";" * (level) +
                   f"{component.name}_{component.local_id}_{component.global_id}\n")

            # if that component has children (then it is a Compound type), apply the same function to the children
            if component.get_children():
                for child in component.get_children():
                    ret += component_tree_simple_export(child,level + 1)

            return ret

        tree_string = component_tree_simple_export(self.root_component)

        tree_dataframe = pandas.DataFrame([x.split(';') for x in tree_string.split('\n')])
        filepath = self.export_dataframe(tree_dataframe, "RESULTS_COMPONENT_TREE_SIMPLE")
        return [filepath]
