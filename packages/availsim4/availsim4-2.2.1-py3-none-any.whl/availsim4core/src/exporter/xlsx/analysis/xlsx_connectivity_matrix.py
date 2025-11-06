# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for XLSXResultExporterConnectivityMatrix class
"""
import pathlib
from typing import List, Optional
import pandas

from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.exporter.xlsx.xlsx_exporter import XLSXExporter
from availsim4core.src.results.simulation_results import SimulationResults


class XLSXConnectivityMatrix(XLSXExporter):
    """
    This class defines an XLSX exporter of the components' connectivity matrix
    """


    def export(self, _: Optional[SimulationResults] = None) -> List[pathlib.Path]:

        def connectivity_matrix_children_export(root: Component):
            """
            Function building a matrix with +1 recursively exploring the system in order to build a graphical
            representation of the system. This "extended" version of the tree exporter provides a detailed output.
            A simple version exists too. The function is called on the root component. Then if a component has children,
            it is called again for its children.
            """

            set_of_components = root.to_set()

            ret = ';'

            # header
            for component_col in set_of_components:
                ret += f"{component_col.name}_{component_col.local_id}_{component_col.global_id}; "
            ret += '\n'

            for component_row in set_of_components:

                # header row wise
                ret += f"{component_row.name}_{component_row.local_id}_{component_row.global_id}; "

                child_list = component_row.get_children()
                parent_list = component_row._parents

                for component_col in set_of_components:

                    if component_col in child_list:
                        ret+="1;"
                    elif component_col in parent_list:
                        ret+="-1;"
                    else:
                        ret+="0;"

                ret+='\n'

            return ret

        connectivity_matrix_string = connectivity_matrix_children_export(self.root_component)
        connectivity_matrix = pandas.DataFrame([x.split(';') for x in connectivity_matrix_string.split('\n')])
        filepath = self.export_dataframe(connectivity_matrix, "RESULTS_CONNECTIVITY_MATRIX")
        return [filepath]
