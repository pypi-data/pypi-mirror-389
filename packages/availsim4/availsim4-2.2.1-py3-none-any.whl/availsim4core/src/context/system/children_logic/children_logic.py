# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from typing import List

from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.context import Context


class ChildrenLogic:
    """
    Class which defines the Logic between a Component and its Children.
    """

    def __repr__(self):
        return "Not defined"

    def evaluate(self, list_of_children: List[Component], context: Context) -> Status:
        """
        Given a list of Children component, this method evaluates the Status.
        :param list_of_children: The list of Children of the node to evaluate.
        :param context: the context of the simulation (structure containing almost everything)
        :return: The Status of the evaluated node.
        """
