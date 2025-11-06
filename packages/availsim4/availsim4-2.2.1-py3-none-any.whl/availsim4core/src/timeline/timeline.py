# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from typing import List

from availsim4core.src.context.rca.rca_manager import RootCauseAnalysisManager
from availsim4core.src.timeline.record import Record
from availsim4core.src.timeline.record_component import RecordComponent


class Timeline:
    """
    Timeline of records which have been proceed in the simulation.
    The timeline is ordered.
    """

    def __init__(self, rca_manager: RootCauseAnalysisManager = None):
        self.record_list: List[Record] = []
        self.rca_manager: RootCauseAnalysisManager = rca_manager
        self.add_records = self._add_records
        if rca_manager is not None:
            self.add_records = self._add_records_with_rca


    def __eq__(self,other):
        return self.record_list == other.record_list

    def __str__(self):
        return str(self.record_list)

    def __repr__(self):
        return self.__str__()

    def _add_records(self, new_records: List[Record], _) -> None:
        """The method `add_records` has two implementations in the Timeline class. This one simply
        extends the list of records stored by the timeline with entries passed in the first parameter.

        Args:
            new_records (List[Record]): a list of records to be added to the timeline.
            _ (int): seed is used in the other method, but is not needed in this variant.
        """
        self.record_list.extend(new_records)

    def _add_records_with_rca(self, new_records: List[Record], seed: int) -> None:
        """The method `_add_records_with_rca` has two implementations in the Timeline class. This one aside from
        extending the list of records, also triggers checks of the RCA analysis.

        Args:
            new_records (List[Record]): a list of records to be added to the timeline.
            seed (int): The number identifying the analysis (RCA needs it to distinguish between different runs in
                results)
        """
        self.rca_manager.trigger_root_cause_analysis_check(new_records, seed)
        self._add_records(new_records, seed)

    def extract_record_from_types(self, types):
        """
        Given a tuple a class types this method returns corresponding list of record matching this types.
        :param types: Class types to be filtered out from the list.
        :return: the list of records corresponding to the given types.
        """
        return [record
                for record in self.record_list
                if isinstance(record, types)]

    def _get_previous_record_of_type(self, specified_type):
        """
        Function getting the previous record of a given type.
        :param specified_type: type of the desired record
        :return: None if no record have been found, otherwise the record founded
        """
        counter = 0
        for record in reversed(self.record_list):
            if isinstance(record, specified_type):
                counter += 1
                if counter == 2:
                    return record
        return None

    def _get_previous_record_of_basic_in_status(self, basic, status):
        """
        Function getting the previous record linked to a specific basic component in a specific status.
        :param basic: component to find back in the list of event
        :param status: status to find back in the list of event
        :return: None if no record have been found, otherwise the record founded
        """
        counter = 0
        for record in reversed(self.record_list):
            if isinstance(record,RecordComponent) and record.component == basic:
                    # the list of events in the inputs all have a 'basic' attribute because they have failures event
                    # attached to them that one wants to postpone
                    counter += 1
                    if (counter >= 2) and (record.status == status):
                        return record
        return None
