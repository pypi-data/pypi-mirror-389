# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import logging
from typing import List, Optional

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.children_logic.children_logic import ChildrenLogic
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.context.system.component_tree.status import Status


class ChildrenLogicOoError(Exception):
    """Exception thrown when definitions or evaluations of the children logic render invalid situations"""


class Oo(ChildrenLogic):
    """
    This class is used to handle the "out of" logic. "Out of" means that X components out of Y components have to be in
    the RUNNING state for the parent to be in the RUNNING state. Other classes, such as And, RequiredComponents and
    ToleratedFault, all inherit from this one and - essentially - provide interfaces to the Oo logic (as AND translates
    to XooX, etc.).
    """

    def __init__(self,
                 minimum_number_of_required_component: int,
                 total_number_of_component: Optional[int] = None):
        self.minimum_number_of_required_component = minimum_number_of_required_component
        self.total_number_of_component = total_number_of_component

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

    def evaluate(self, list_of_children: List[Component], _: Context) -> Status:

        total_number_of_component = len(list_of_children)
        if (self.total_number_of_component is not None and self.total_number_of_component != total_number_of_component):
            list_of_parents_name = []
            for child in list_of_children:
                for parent in child.get_parents():
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
                message_exception = "Unexpected occurrence of Statuses in Oo children logic"
                logging.exception(message_exception)
                raise ChildrenLogicOoError(message_exception)
