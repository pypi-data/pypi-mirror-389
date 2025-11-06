# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for XLSXResultExporterGraph class
"""

import logging
import os
import pathlib
import matplotlib.pyplot as plt
import networkx as nx

from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.exporter.exporter import Exporter


class GraphExporter(Exporter):
    """
    This class defines an XLSX exporter of the components' graph
    """

    OUTPUT_FILE_TEMPLATE_PNG = 'simulation_result_{}_{}.png'
    OUTPUT_FILE_TEMPLATE_SVG = 'simulation_result_{}_{}.svg'
    OUTPUT_FILE_TEMPLATE_DOT = 'simulation_result_{}_{}.svg'

    def export(self, *_):
        def graph_export(root: Component):

            def get_name(component: Component):
                """
                :param component:
                :return: string identifying a component by its name
                """
                name = f"{component.name}_{component.local_id}_{component.global_id}"
                if component.list_of_mru_trigger:
                    name+= '\nTRIGGER MRU: '+"".join([x.name+', ' for x in component.list_of_mru_trigger])
                if isinstance(component, Basic) and component.list_of_mru_group:
                    name+= '\nIN MRU: '+"".join([x.name+', ' for x in component.list_of_mru_group])
                return name

            def get_edge(parent: Component,
                         list_of_edges,
                         shell_dict,
                         level=0):
                """
                Recursive function defining the list of edges and the depth of each node
                :param parent: component studied
                :param list_of_edges: accumulated list of edges
                :param shell_dict: accumulated dictionaries of the different node (component) in the different layers
                (shell)
                :param level: depth of the component (use for the shell)
                :return:
                """

                parent_name = get_name(parent)

                if level in shell_dict.keys():
                    # extend the current level
                    shell_dict[level].append(parent_name)
                else:
                    # instantiate the level with a list containing one element
                    shell_dict[level] = [parent_name]

                for child in parent.get_children():
                    child_name = get_name(child)
                    list_of_edges.append((parent_name, child_name))
                    list_of_edges, shell_dict = get_edge(child,
                                                         list_of_edges,
                                                         shell_dict,
                                                         level+1)

                return list_of_edges, shell_dict

            def generate_picture_with_linux_command(picture_format: str):
                """
                Function using the command "dot" present on linux os to generate a picture
                :param picture_format:
                :return:
                """
                output_dot = self.OUTPUT_FILE_TEMPLATE_PNG.format(self.analysis.id,
                                                             self.unique_output_file_identifier
                                                             ).split(".png", maxsplit=1)[0] + '_linux.' + picture_format
                output_filepath = pathlib.Path(self.output_folder) / output_dot
                command = f"dot -T{picture_format} {dot_filename} > {output_filepath}"
                try:
                    os.system(command)
                    return output_filepath
                except OSError:
                    logging.warning("Impossible to generate %s", output_dot)

            list_of_edges, shell_dict = get_edge(root, [], {0: []}, level=0)
            paths_created_files = []

            graph = nx.DiGraph()
            graph.add_edges_from(list_of_edges)
            # generating a dot file
            dot_filename = 'tmp_tree_file.dot'
            nx.drawing.nx_agraph.write_dot(graph, dot_filename)
            # using the dot file to create picture directly from the linux os
            paths_created_files.append(generate_picture_with_linux_command('png'))
            paths_created_files.append(generate_picture_with_linux_command('svg'))

            number_of_layers_in_the_graph = len(shell_dict.keys())
            number_of_columns_in_the_graph = max([len(x) for x in shell_dict.values()])
            plt.figure(figsize=(3*number_of_columns_in_the_graph,
                                1*number_of_layers_in_the_graph))

            # generate a picture within python
            pos = nx.drawing.nx_agraph.graphviz_layout(graph, prog='dot')
            labels = nx.draw_networkx_labels(
                graph,
                pos,
                font_size=10,
                horizontalalignment="right",
                verticalalignment="top"
            )
            # rotate the labels by 15 degrees in order to improve the readability / limit the overlap between text
            for _, ticks in labels.items():
                ticks.set_rotation(15)

            nx.draw(
                graph,
                pos=pos,
                labels=labels,
                with_labels=False,
                arrows=True,
                arrowsize=20,
                node_color='red',
                node_size=10,
                alpha=.25
            )



            output_python_png = pathlib.Path(self.OUTPUT_FILE_TEMPLATE_PNG.format(self.analysis.id,
                                                                     self.unique_output_file_identifier))
            plt.savefig(self.output_folder / output_python_png, dpi=300)
            paths_created_files.append(self.output_folder / output_python_png)

            output_python_svg = pathlib.Path(self.OUTPUT_FILE_TEMPLATE_SVG.format(self.analysis.id,
                                                                     self.unique_output_file_identifier))
            plt.savefig(self.output_folder / output_python_svg)
            paths_created_files.append(self.output_folder / output_python_svg)
            return paths_created_files

        return graph_export(self.root_component)
