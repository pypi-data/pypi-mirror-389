# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for XLSXResultExporterComponentTreeExtended class
"""

import pathlib
from typing import List, Optional
import pandas

from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.exporter.xlsx.xlsx_exporter import XLSXExporter
from availsim4core.src.results.simulation_results import SimulationResults


class XLSXComponentTreeExtended(XLSXExporter):
    """
    This class defines an XLSX exporter printing an extended (i.e., including more details) tree into the output file
    """
    def export(self, _: Optional[SimulationResults] = None) -> List[pathlib.Path]:

        def component_tree_extended_export(component: Component, level=0):
            """
            Function recursively exploring the system in order to build a graphical representation of the system.
            This "extended" version of the tree exporter provides a detailed output. A simple version exists too.
            The function is called on the root component. Then if a component has children, it is called again for its
            children.
            """

            # Variable used to get the logic between the parent of the current component and the current component.
            # It is possible that a component has several parents if it's a "shared child".
            dict_of_children_logic = {}
            for parent in component.get_parents():
                dict_of_children_logic[parent.__repr__()] = parent.children_logic

            if level == 0:
                # if level ==0, then the current component is the root component, it has no parent,
                # only a "light" string is used to described the component
                ret = (";" * (level) +
                       f"{component.name}_{component.local_id}_{component.global_id}; ROOT COMPONENT HAS NO PARENT \n")
            else:
                # else, the current component has some parent(s),
                # a more detailed string is used, with logic applied by its parent(s)
                ret = (";" * (level - 1) + f"logic = {dict_of_children_logic};"
                f"{component.name}_{component.local_id}_{component.global_id}; parents = {component.get_parents()} \n")

            if isinstance(component, Compound): # component.get_children():
                # if that component has children (then it is a Compound type), apply the same function to the children
                for child in component.get_children():
                    ret += component_tree_extended_export(child,level + 1)
            elif isinstance(component, Basic):
                # else, the current component is a basic and has failure mode(s), those a printed
                ret += (";" * (level + 1) +
                        f"failure mode = {component.failure_mode}\n")

            return ret

        tree_string = component_tree_extended_export(self.root_component)
        tree_dataframe = pandas.DataFrame([x.split(';') for x in tree_string.split('\n')])
        filepath = self.export_dataframe(tree_dataframe,
                                         "RESULTS_COMPONENT_TREE_EXTENDED")
        return [filepath]
