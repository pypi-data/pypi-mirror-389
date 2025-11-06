# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

class SystemModifierCombination:
    """
    SystemTemplate modifier Combination describes a new system based on the Sensitivity Analysis file.
    It defines the Combination list which needs to be applied on the initial SystemTemplate
    in order to get all the analysis.
    """

    def __init__(self, system_modifier_list):
        self.system_modifier_list = system_modifier_list

    def __str__(self):
        return str(self.system_modifier_list)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.system_modifier_list == other.system_modifier_list
