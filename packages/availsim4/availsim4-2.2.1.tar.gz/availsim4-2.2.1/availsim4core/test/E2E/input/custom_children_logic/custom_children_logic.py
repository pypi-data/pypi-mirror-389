# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import logging
from typing import List

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.children_logic.children_logic import ChildrenLogic
from availsim4core.src.context.system.children_logic.oo import Oo, ChildrenLogicOoError
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.context.system.component_tree.status import Status


###
# The first custom logic is a copy of the "Out Of" logic with the number of tolerated faults and number of components
# forced to 10 and 30 for the test to pass. It is a dummy example with no added value than checking the import.
###
class CUSTOM1(ChildrenLogic):
    """
    class used to handle an "Out of" logic. "Out Of" means X component(s) out of Y components has(ve) to be in the
    RUNNING state for the parent to be in the RUNNING state
    """

    def __init__(self):
        self.minimum_number_of_required_component = 10
        self.total_number_of_component = 30

    def __repr__(self):
        return f"{self.minimum_number_of_required_component}OO{self.total_number_of_component}"

    @staticmethod
    def count_status_occurrence(status: Status, list_of_children: List[Component]) -> int:
        """
        Number of occurrences of a given status from the given list of component.
        :param status: status to evaluate
        :param list_of_children: full list of children
        :return occurrence: int, the occurrence of the given status within the given component list.
        """

        return len([child for child in list_of_children if child.status == status])

    def evaluate(self, list_of_children: List[Component], context: Context) -> Status:

        total_number_of_component = len(list_of_children)
        if (self.total_number_of_component is not None and
            self.total_number_of_component != total_number_of_component):

                list_of_parents_name = []
                for child in list_of_children:
                    for parent in child._parents:
                        list_of_parents_name.append(f"{parent.name}_{parent.local_id}_{parent.global_id}")

                message_exception = f"Total number of children components should be {self.total_number_of_component} " \
                                    f"according to the CHILDREN_LOGIC_INPUT of component(s) {set(list_of_parents_name)} " \
                                    f"but it is equal to {total_number_of_component}"
                logging.exception(message_exception)
                raise ChildrenLogicOoError(message_exception)


        occurrence_by_status = {}

        # search for the presence of different statuses
        for status in [Status.FAILED, Status.BLIND_FAILED, Status.HELD,
                       Status.DEGRADED, Status.BLIND_DEGRADED,
                       Status.INSPECTION, Status.UNDER_REPAIR,
                       Status.RUNNING]:
            occurrence_by_status[status] = self.count_status_occurrence(status, list_of_children)

        considered_as_running = occurrence_by_status[Status.RUNNING] + \
                                occurrence_by_status[Status.DEGRADED] + \
                                occurrence_by_status[Status.BLIND_DEGRADED]

        # RUNNING
        if occurrence_by_status[Status.RUNNING] == total_number_of_component:
            return Status.RUNNING
        else:
            # DEGRADED
            if considered_as_running >= self.minimum_number_of_required_component:

                if occurrence_by_status[Status.BLIND_FAILED] + occurrence_by_status[Status.BLIND_DEGRADED] == 0:
                    return Status.DEGRADED
                elif occurrence_by_status[Status.BLIND_FAILED] + occurrence_by_status[Status.BLIND_DEGRADED] > 0:
                    return Status.BLIND_DEGRADED
                else:
                    raise ChildrenLogicOoError(
                        "Unexpected negative occurrence of Statuses in Oo children logic - Degraded")

            elif considered_as_running < self.minimum_number_of_required_component:

                if occurrence_by_status[Status.INSPECTION] > 0:
                    return Status.INSPECTION
                elif occurrence_by_status[Status.INSPECTION] == 0 and occurrence_by_status[Status.UNDER_REPAIR] > 0:
                    return Status.UNDER_REPAIR
                elif occurrence_by_status[Status.INSPECTION] + occurrence_by_status[Status.UNDER_REPAIR] == 0 \
                        and occurrence_by_status[Status.BLIND_FAILED] + occurrence_by_status[Status.BLIND_DEGRADED] > 0:
                    return Status.BLIND_FAILED
                elif considered_as_running + occurrence_by_status[
                    Status.HELD] >= self.minimum_number_of_required_component:
                    return Status.HELD
                elif occurrence_by_status[Status.INSPECTION] + occurrence_by_status[Status.UNDER_REPAIR] \
                        + occurrence_by_status[Status.BLIND_FAILED] + occurrence_by_status[Status.BLIND_DEGRADED] == 0:
                    # Default Case
                    return Status.FAILED
                else:
                    raise ChildrenLogicOoError(
                        f"Unexpected occurrence of Statuses in Oo children logic over the components {list_of_children}"
                        )
            else:
                message_exception = f"Unexpected occurrence of Statuses in Oo children logic"
                logging.exception(message_exception)
                raise ChildrenLogicOoError(message_exception)


###
# The second custom logic is a copy of the "AND" logic with the number of tolerated faults and number of components
# forced to 0 and 1 for the test to pass. It is a dummy example with no added value than checking the import.
###
class CUSTOM2(Oo):
    def __init__(self):
        super().__init__(0,1)

    def __repr__(self):
        return "AND"

    def evaluate(self, list_of_children: List[Component], context: Context) -> Status:
        self.minimum_number_of_required_component = len(list_of_children)

        return super().evaluate(list_of_children, context)


###
# The third custom logic is a copy of the "AND" logic with the number of tolerated faults and number of components
# forced to 0 and 1 for the test to pass. It is a dummy example with no added value than checking the import.
###
class CUSTOM3(Oo):
    def __init__(self):
        super().__init__(0,2)

    def __repr__(self):
        return "AND"

    def evaluate(self, list_of_children: List[Component], context: Context) -> Status:
        self.minimum_number_of_required_component = len(list_of_children)

        return super().evaluate(list_of_children, context)

###
# This custom logic is applies AND or OR children logic depending on the current phase. This test ensures that the
# context variable is accessible from the evaluate method.
###
class CUSTOM4(Oo):
    def __init__(self):
        super().__init__(0,10)

    def __repr__(self):
        return "AND"

    def evaluate(self, list_of_children: List[Component], context: Context) -> Status:
        self.minimum_number_of_required_component = len(list_of_children)
        current_phase_name = context.phase_manager.current_phase.name

        if current_phase_name=='STANDARD':
            self.minimum_number_of_required_component = len(list_of_children)
        else:
            self.minimum_number_of_required_component = 1
        return super().evaluate(list_of_children, context)
