# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from __future__ import annotations

from availsim4core.src.context.system.children_logic.oo import Oo


class RequiredComponent(Oo):
    """Class handling required component children logic

    Through this logic, users can define how many components are required to work without explicitly stating the number
    of that component's children. In other words, X RC is equivalent to XooY, where Y is set to the number of children.
    """

    def __init__(self, minimum_number_of_required_component: int):
        super().__init__(minimum_number_of_required_component)

    def __repr__(self):
        return f"{self.minimum_number_of_required_component}RC"
