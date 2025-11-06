# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from typing import List

from availsim4core.src.context.system.children_logic.oo import Oo
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.context import Context


class And(Oo):
    """Class handling AND children logic

    This children logic requires all of the children to be in operational state for the parent to be working.
    """

    def __init__(self):
        super().__init__(0)

    def __repr__(self):
        return "AND"

    def evaluate(self, list_of_children: List[Component], _: Context) -> Status:
        self.minimum_number_of_required_component = len(list_of_children)

        return super().evaluate(list_of_children, _)
