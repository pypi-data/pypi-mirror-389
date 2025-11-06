# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""Module of the Reader interface"""

from abc import ABC, abstractmethod
import pathlib
from typing import Union
from availsim4core.src.context.system.system_template import SystemTemplate

from availsim4core.src.simulation.simulation import Simulation

class Reader(ABC):
    """Interface of the readers with one required `read` method"""

    @abstractmethod
    def read(self, file_path: pathlib.Path) -> Union[Simulation, SystemTemplate]:
        """The only method required by the Reader interface.
        """
