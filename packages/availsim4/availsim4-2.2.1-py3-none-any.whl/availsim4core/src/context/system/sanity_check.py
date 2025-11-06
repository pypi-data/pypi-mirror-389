# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module used to define sanity checks which are tested at each execution to avoid simulating invalid input files.
This is both used to be sure that the user did not forget / misunderstand something and also to avoid starting
simulations which after many hours will eventually stop because of an inconsistency in the input file or a bug caused
by a combination of parameters which is not allowed.
"""

import logging

from typing import List

from availsim4core.src.context.system.children_logic.and_ import And
from availsim4core.src.context.system.children_logic.oo import Oo
from availsim4core.src.context.system.children_logic.required_component import RequiredComponent
from availsim4core.src.context.system.children_logic.tolerated_fault import ToleratedFault
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.context.system.system_template import SystemTemplate

from availsim4core.src.context.system.system_utils import SystemUtils


class ChildrenLogicSanityCheckError(Exception):
    """This error is thrown when a user specifies children logic that does not conform to the component structure."""


class IncoherentModelException(Exception):
    """Exception thrown when the model defined by the user has some flaws which require fixing."""


def _compare_and_log_diff(tree_list: List[str],
                         system_template_list: List[str],
                         description: str) -> bool:
    """
    Function taking two lists of strings, comparing them and logging the results using a description string.
    This function is specialized to compare names defined in the input file and names found in the tree simulated
    """

    matching = True

    tree_set = set(tree_list)
    template_set = set(system_template_list)

    tree_minus_input = tree_set - template_set
    if tree_minus_input:
        matching = False
        logging.warning("%s present in the tree but not in the system template: %s", description, tree_minus_input)

    input_minus_tree = template_set - tree_set
    if input_minus_tree:
        matching = False
        logging.warning("%s present in the system template but not in the tree: %s", description, input_minus_tree)

    return matching


def export_content_of_tree(root: Component) -> dict:
    """
    Function exploring a tree and extracting the information present in it
    :param root: component being the root of the tree to study
    :return: dict of list of names present in the tree
    """

    list_of_component_names_in_the_tree = []
    list_of_failure_mode_names_in_the_tree = []
    list_of_inspection_names_in_the_tree = []
    list_of_phase_names_in_the_tree = []
    list_of_mru_names_in_the_tree = []

    for component in root.to_set():
        list_of_component_names_in_the_tree.append(component.name)
        if not component.get_children():
            list_of_failure_mode_names_in_the_tree.append(component.failure_mode.name)
            for phase in component.failure_mode.phase_set:
                list_of_phase_names_in_the_tree.append(phase.name)
                list_of_phase_names_in_the_tree.append(phase.next.name)
                if phase.next_phase_if_failure:
                    list_of_phase_names_in_the_tree.append(phase.next_phase_if_failure.name)
            if component.failure_mode.failure_mode_next_phase_if_failure is not None:
                list_of_phase_names_in_the_tree.append(component.failure_mode.failure_mode_next_phase_if_failure.name)
            if component.failure_mode.held_before_repair_phase_set is not set():
                list_of_phase_names_in_the_tree.extend(
                    [phase.name for phase in component.failure_mode.held_before_repair_phase_set])
            if component.failure_mode.held_after_repair_phase_set is not set():
                list_of_phase_names_in_the_tree.extend(
                    [phase.name for phase in component.failure_mode.held_after_repair_phase_set])
            if component.failure_mode.inspection is not None:
                list_of_inspection_names_in_the_tree.append(component.failure_mode.inspection.name)
            for mru in component.list_of_mru_group:
                list_of_mru_names_in_the_tree.append(mru.name)
        for mru in component.list_of_mru_trigger:
            list_of_mru_names_in_the_tree.append(mru.name)
            list_of_component_names_in_the_tree.extend(mru.scope_common_ancestor)

    return {"component names":list_of_component_names_in_the_tree,
            "failure mode names":list_of_failure_mode_names_in_the_tree,
            "inspection names":list_of_inspection_names_in_the_tree,
            "phase names":list_of_phase_names_in_the_tree,
            "mru names":list_of_mru_names_in_the_tree}


def check_the_first_phase(system_template: SystemTemplate) -> bool:
    """This method checks if the system template has exactly one phase selected as the first one. If this is not the
    case, it throws the IncoherentModelException."""
    if not any(phase.is_first_phase for phase in system_template.phase_set):
        msg = "None of the phases is defined as the first one"
        logging.exception(msg)
        raise IncoherentModelException(msg)

    if sum(phase.is_first_phase for phase in system_template.phase_set) > 1:
        msg = "More than one phase is defined as the first one"
        logging.exception(msg)
        raise IncoherentModelException(msg)


def export_content_of_system_template(system_template: SystemTemplate) -> dict:
    """
    Function exploring a system template (the object corresponding to the input file) and extracting the information
     present in it
    :param system_template:
    :return: dict of list of names present in the tree
    """

    list_of_component_names_in_the_system_template = []
    list_of_failure_mode_names_in_the_system_template = []
    list_of_inspection_names_in_the_system_template = []
    list_of_phase_names_in_the_system_template = []
    list_of_mru_names_in_the_system_template = []

    names_of_mrus_with_trigger_definend = []

    # architecture entries
    for architecture_entry in system_template.architecture_entry_list:
        list_of_component_names_in_the_system_template.append(architecture_entry.component_name)
        list_of_component_names_in_the_system_template.extend([SystemUtils.extract_name_of_function_from_string(entry)
                                                               for entry in architecture_entry.children_name_list])
        list_of_mru_names_in_the_system_template.extend(architecture_entry.in_mru_str_list)
        list_of_mru_names_in_the_system_template.extend(architecture_entry.trigger_mru_str_list)
        names_of_mrus_with_trigger_definend.extend(architecture_entry.trigger_mru_str_list)

    # failure mode assignments entries
    for failure_mode_assignments in system_template.failure_mode_assignments_list:
        list_of_component_names_in_the_system_template.append(failure_mode_assignments.component_name)
        list_of_failure_mode_names_in_the_system_template.append(failure_mode_assignments.failure_mode.name)

    # failure mode assignments entries
    for failure_mode in system_template.failure_mode_list:
        list_of_failure_mode_names_in_the_system_template.append(failure_mode.name)
        list_of_phase_names_in_the_system_template.extend([p.name for p in failure_mode.phase_set])
        list_of_phase_names_in_the_system_template.extend([p.name for p in failure_mode.held_after_repair_phase_set])
        list_of_phase_names_in_the_system_template.extend([p.name for p in failure_mode.held_before_repair_phase_set])
        if failure_mode.failure_mode_next_phase_if_failure is not None:
            list_of_phase_names_in_the_system_template.append(failure_mode.failure_mode_next_phase_if_failure.name)

    # MRU entries
    for mru in system_template.mru_list:
        list_of_mru_names_in_the_system_template.append(mru.name)
        list_of_component_names_in_the_system_template.extend(mru.scope_common_ancestor)
        if mru.repair_schedule != "":
            logging.warning("The following MRU %s has a defined schedule - although this feature is not available yet.",
                            mru.name)

    missing_triggers = set(list_of_mru_names_in_the_system_template) - set(names_of_mrus_with_trigger_definend)
    if missing_triggers:
        logging.warning("The MRUs %s do not have triggers defined in the system.",
                            missing_triggers)

    # PHASES entries
    for phase in system_template.phase_set:
        list_of_phase_names_in_the_system_template.append(phase.name)
        if phase.next_phase_if_failure:
            list_of_phase_names_in_the_system_template.append(phase.next_phase_if_failure.name)

    # INSPECTION entries
    for inspection in system_template.inspection_list:
        list_of_inspection_names_in_the_system_template.append(inspection.name)

    return {"component names":list_of_component_names_in_the_system_template,
            "failure mode names":list_of_failure_mode_names_in_the_system_template,
            "inspection names":list_of_inspection_names_in_the_system_template,
            "phase names":list_of_phase_names_in_the_system_template,
            "mru names":list_of_mru_names_in_the_system_template}


def children_logic_validity(component: Component):
    """
    Recursive function parsing the tree to check the validity of the children logic, if it is not a custom one
    :param component: component which is currently studied
    :return: nothing, but raise an error if some inconsistency is spotted
    """

    if isinstance(component, Compound):
        number_of_children = len(component.get_children())

        if isinstance(component.children_logic, RequiredComponent):
            if number_of_children < component.children_logic.minimum_number_of_required_component:
                message = f"{type(component.children_logic)} children logic of component {component.name} has less" \
                          f" children ({number_of_children}) than the minimum number of required components (" \
                          f"{component.children_logic.minimum_number_of_required_component}), thus the parent " \
                          f"component can never be in a RUNNING status."
                logging.exception(message)
                raise ChildrenLogicSanityCheckError(message)
            elif number_of_children == component.children_logic.minimum_number_of_required_component:
                message = f"{type(component.children_logic)} children logic of component {component.name} has as " \
                          f" many children ({number_of_children}) as the minimum number of required components (" \
                          f"{component.children_logic.minimum_number_of_required_component}), thus it is equivalent" \
                          f" to an And logic."
                logging.warning(message)

        elif isinstance(component.children_logic, ToleratedFault):
            if number_of_children < component.children_logic.fault_tolerance:
                message = f"{type(component.children_logic)} children logic of component {component.name} has less" \
                          f" children ({number_of_children}) than the number of tolerated faults (" \
                          f"{component.children_logic.fault_tolerance}), thus the parent component will always be" \
                          f" in a RUNNING status."
                logging.warning(message)
            elif number_of_children == component.children_logic.fault_tolerance:
                message = f"{type(component.children_logic)} children logic of component {component.name} has as " \
                          f" many children ({number_of_children}) as the number of tolerated faults (" \
                          f"{component.children_logic.fault_tolerance}), thus  the parent component will always be" \
                          f" in a RUNNING status."
                logging.warning(message)

        elif isinstance(component.children_logic, And):
            pass

        elif isinstance(component.children_logic, Oo):

            if number_of_children != component.children_logic.total_number_of_component:
                message = f"{type(component.children_logic)} children logic of component {component.name} has a " \
                          f" different number of children ({number_of_children}) than the one provided in the input" \
                          f" file ({component.children_logic.total_number_of_component})."
                logging.exception(message)
                raise ChildrenLogicSanityCheckError(message)
            elif component.children_logic.minimum_number_of_required_component > \
                    component.children_logic.total_number_of_component:
                message = f"{type(component.children_logic)} children logic of component {component.name} has less" \
                          f" children ({number_of_children}) than the minimum number required component (" \
                          f"{component.children_logic.minimum_number_of_required_component}), thus the parent " \
                          f"component can never be in a RUNNING status."
                logging.exception(message)
                raise ChildrenLogicSanityCheckError(message)
            elif number_of_children == component.children_logic.minimum_number_of_required_component:
                message = f"{type(component.children_logic)} children logic of component {component.name} has as " \
                          f" many children ({number_of_children}) than the minimum number required component (" \
                          f"{component.children_logic.minimum_number_of_required_component}), thus it is equivalent" \
                          f" to an And logic."
                logging.warning(message)

        else:
            message = f"{type(component.children_logic)} children logic of component {component.name} cannot be " \
                      f"analysed in the sanity checks, most likely it is a user defined children logic."
            logging.warning(message)

        for child in component.get_children():
            children_logic_validity(child)


def run(system_template: SystemTemplate, root: Component) -> bool:
    """
    Function which list all the names present in the tree (component name, failure mode name, etc) and the names
    present in the input file. A comparison is performed to do a simple, but not exhaustive, test
    """

    dict_of_lists_of_names_extracted_from_the_tree = export_content_of_tree(root)
    dict_of_lists_of_names_extracted_from_the_system_template = export_content_of_system_template(system_template)

    # logging possible differences between names extracted from the input file and
    # names extracted form the tree simulated
    matching=True
    for key, values in dict_of_lists_of_names_extracted_from_the_tree.items():
        matching = matching and _compare_and_log_diff(values,
                                                      dict_of_lists_of_names_extracted_from_the_system_template[key],
                                                      key)

    # counting the number of failure modes present in the component tree
    total_number_of_failure_modes_in_the_system = 0
    for component in root.to_set():
        if isinstance(component, Basic):
            total_number_of_failure_modes_in_the_system += 1
    if total_number_of_failure_modes_in_the_system == 0:
        msg = "No failure mode present in the system tree"
        logging.exception(msg)
        raise IncoherentModelException(msg)

    children_logic_validity(root)
    check_the_first_phase(system_template)

    return matching
