# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.context.system.system_template import SystemTemplate
from availsim4core.src.simulation.simulation import Simulation


class Analysis:
    """
    Domain object of which represents the an Analysis to be performed.
    Contains both the {SystemTemplate} and {simulation}.
    """
    __slots__ = 'id', 'system_template', 'simulation'

    def __init__(self,
                 identifier: int,
                 system_template: SystemTemplate,
                 simulation: Simulation):
        self.id = identifier
        self.system_template = system_template
        self.simulation = simulation

    def __eq__(self, other):
        return self.id == other.id \
               and self.system_template == other.system_template \
               and self.simulation == other.simulation

    def __str__(self):
        return f"id={self.id}, system_template={self.system_template}, simulation={self.simulation}"
