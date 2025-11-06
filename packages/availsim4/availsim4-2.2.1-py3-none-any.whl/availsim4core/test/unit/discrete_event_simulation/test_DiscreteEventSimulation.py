# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.context.context import Context
from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.rca.rca_manager import RootCauseAnalysisManager
from availsim4core.src.context.system.children_logic.and_ import And
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.failure import Failure, FailureType
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.context.system.inspection import Inspection
from availsim4core.src.context.system.probability_law.deterministic_law import DeterministicLaw
from availsim4core.src.discrete_event_simulation.discrete_event_simulation import DiscreteEventSimulation
from availsim4core.src.discrete_event_simulation.event.b_event.failure_event.blind_failure_event import \
    BlindFailureEvent
from availsim4core.src.discrete_event_simulation.event.b_event.failure_event.detectable_failure_event import \
    DetectableFailureEvent
from availsim4core.src.discrete_event_simulation.event.b_event.inspection_event.start_inspection_event import \
    StartInspectionEvent
from availsim4core.src.discrete_event_simulation.event.b_event.repair_event.end_repairing_event import EndRepairingEvent
from availsim4core.src.discrete_event_simulation.event.b_event.repair_event.start_repairing_event import \
    StartRepairingEvent
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEventPriority
from availsim4core.src.discrete_event_simulation.event.c_event.inspection_event.order_end_inspection_event import \
    OrderEndInspectionEvent
from availsim4core.src.discrete_event_simulation.event.c_event.repair_event.order_repair_event import OrderRepairEvent
from availsim4core.src.timeline.record_component import RecordComponent
from availsim4core.src.timeline.record_generator import RecordGenerator
from availsim4core.src.timeline.record_phase import RecordPhase


class test_DiscreteEventSimulation(unittest.TestCase):

    def test_run(self):
        phase = PhaseManager.NO_PHASE

        failure_mode_1 = FailureMode("test_run",
                                     DeterministicLaw([1]),
                                     DeterministicLaw([1]),
                                     Failure(FailureType.DETECTABLE),
                                     [phase],
                                     None,
                                     [phase],
                                     None,
                                     'AFTER_REPAIR',
                                     [phase])

        phase_manager = PhaseManager([phase],set())

        root_component = Compound(1, "ROOT", 0, [], And(), [])
        _basic = Basic(2, "BASIC", 0, [root_component], failure_mode_1, [], [])
        _basic_name_and_ids = f"{_basic.name}_{_basic.local_id}_{_basic.global_id}"
        root_component.add_children_list([_basic])

        rca_manager = RootCauseAnalysisManager(set(), root_component.to_set())
        context = Context(root_component, phase_manager, rca_manager, set(), set())

        discrete_event_simulation = DiscreteEventSimulation(0, 3, context)

        _,_ = discrete_event_simulation.run()

        expected_root_node_timeline = RecordGenerator.get_initial_records(0, context)
        expected_root_node_timeline.extend([
            RecordComponent(_basic, Status.FAILED, 1, phase, f"test_run failure mode of component {_basic_name_and_ids}"),
            RecordComponent(root_component, Status.FAILED, 1, phase, f"test_run failure mode of component {_basic_name_and_ids}"),
            RecordComponent(_basic, Status.UNDER_REPAIR, 1, phase, f"UNDER REPAIR - component {_basic_name_and_ids}"),
            RecordComponent(root_component, Status.UNDER_REPAIR, 1, phase, f"UNDER REPAIR - component {_basic_name_and_ids}"),
            RecordComponent(_basic, Status.RUNNING, 2, phase, f"REPAIRED - component {_basic_name_and_ids}"),
            RecordComponent(root_component, Status.RUNNING, 2, phase, f"REPAIRED - component {_basic_name_and_ids}"),
            RecordPhase(phase, 2, PhaseManager.DEFAULT_PHASE_IF_FAILURE_DESCRIPTION),
            RecordComponent(root_component, Status.RUNNING, 2, phase, "Update following a phase change"),
            RecordComponent(_basic, Status.RUNNING, 2, phase, "Update following a phase change"),
            RecordComponent(_basic, Status.FAILED, 3, phase, f"test_run failure mode of component {_basic_name_and_ids}"),
            RecordComponent(root_component, Status.FAILED, 3, phase, f"test_run failure mode of component {_basic_name_and_ids}"),
            RecordComponent(_basic, Status.UNDER_REPAIR, 3, phase, f"UNDER REPAIR - component {_basic_name_and_ids}"),
            RecordComponent(root_component, Status.UNDER_REPAIR, 3, phase, f"UNDER REPAIR - component {_basic_name_and_ids}")
        ])

        self.assertEqual(root_component.status, Status.UNDER_REPAIR)
        self.assertEqual(_basic.status, Status.UNDER_REPAIR)
        self.assertEqual(discrete_event_simulation.context.timeline_record.record_list,
                         expected_root_node_timeline)

    def test_run__blind_failures(self):
        phase = Phase("phase_test", DeterministicLaw([10]), True)
        phase.set_next_phase(PhaseManager.NO_PHASE)

        failure_mode_1 = FailureMode("test_run",
                                     DeterministicLaw([2]),
                                     DeterministicLaw([2]),
                                     Failure(FailureType.BLIND),
                                     [phase],
                                     None,
                                     [phase],
                                     None,
                                     'NEVER',
                                     [phase])

        phase_manager = PhaseManager([phase],set())

        root_component = Compound(1, "ROOT", 0, [], And(), [])
        _basic = Basic(2, "BASIC", 0, [root_component], failure_mode_1, [], [])
        _basic_name_and_ids = f"{_basic.name}_{_basic.local_id}_{_basic.global_id}"
        root_component.add_children_list([_basic])

        rca_manager = RootCauseAnalysisManager(set(), root_component.to_set())
        context = Context(root_component, phase_manager, rca_manager, set(), set())

        discrete_event_simulation = DiscreteEventSimulation(0, 5, context)

        _, _ = discrete_event_simulation.run()

        expected_root_node_timeline = RecordGenerator.get_initial_records(0, context)
        expected_root_node_timeline.extend([
            RecordComponent(_basic, Status.BLIND_FAILED, 2, phase, f"test_run failure mode of component {_basic_name_and_ids}"),
            RecordComponent(root_component, Status.BLIND_FAILED, 2, phase, f"test_run failure mode of component {_basic_name_and_ids}")])
        self.assertEqual(root_component.status, Status.BLIND_FAILED)
        self.assertEqual(_basic.status, Status.BLIND_FAILED)
        self.assertListEqual(discrete_event_simulation.context.timeline_record.record_list, expected_root_node_timeline)

    def test_run__inspection_events(self):
        inspection_name = "long_shut_down"
        inspection_period = 5
        inspection_duration = 1

        phase = Phase("phase_test", DeterministicLaw([10]), True)
        phase.set_next_phase(PhaseManager.NO_PHASE)

        failure_mode_1 = FailureMode("test_run",
                                     DeterministicLaw([2]),
                                     DeterministicLaw([2]),
                                     Failure(FailureType.BLIND),
                                     [phase],
                                     Inspection(inspection_name, inspection_period, inspection_duration),
                                     [phase],
                                     None,
                                     'NEVER',
                                     [phase])

        phase_manager = PhaseManager([phase],set())

        root_component = Compound(1, "ROOT", 0, [], And(), [])
        _basic = Basic(2, "BASIC", 0, [root_component], failure_mode_1, [], [])
        _basic_name = f"{_basic.name}_{_basic.local_id}_{_basic.global_id}"
        root_component.add_children_list([_basic])

        rca_manager = RootCauseAnalysisManager(set(), root_component.to_set())
        context = Context(root_component, phase_manager, rca_manager, set(), set())
        discrete_event_simulation = DiscreteEventSimulation(0,
                                                            inspection_period + inspection_duration,
                                                            context)

        _,_ = discrete_event_simulation.run()

        expected_root_node_timeline = RecordGenerator.get_initial_records(0, context)
        expected_root_node_timeline.extend([
            RecordComponent(_basic, Status.BLIND_FAILED, 2, phase, f"test_run failure mode of component {_basic_name}"),
            RecordComponent(root_component, Status.BLIND_FAILED, 2, phase, f"test_run failure mode of component {_basic_name}"),
            RecordComponent(_basic, Status.INSPECTION, 5, phase, f"INSPECTION"),
            RecordComponent(root_component, Status.INSPECTION, 5, phase, f"INSPECTION"),
            RecordComponent(_basic, Status.RUNNING, 6, phase, f"EndInspectionEvent"),
            RecordComponent(root_component, Status.RUNNING, 6, phase, f"EndInspectionEvent")])
        self.assertEqual(root_component.status, Status.RUNNING)
        self.assertEqual(_basic.status, Status.RUNNING)
        self.assertListEqual(discrete_event_simulation.context.timeline_record.record_list, expected_root_node_timeline)

    def test__execute_b_event__detectable_failure(self):
        phase = Phase("phase_test", DeterministicLaw([10]),  True)
        phase.set_next_phase(PhaseManager.NO_PHASE)

        failure_mode_1 = FailureMode("test__execute_b_event",
                                     DeterministicLaw([1]),
                                     DeterministicLaw([1]),
                                     Failure(FailureType.DETECTABLE),
                                     [phase],
                                     None,
                                     [phase],
                                     None,
                                     'AFTER_REPAIR',
                                     [phase])

        phase_manager = PhaseManager([phase],set())

        root_component = Compound(1, "ROOT", 0, [], And(), [])
        _basic = Basic(2, "BASIC", 0, [root_component], failure_mode_1, [], [])
        root_component.add_children_list([_basic])

        rca_manager = RootCauseAnalysisManager(set(), root_component.to_set())
        context = Context(root_component, phase_manager, rca_manager, set(), set())

        detectable_failure_event = DetectableFailureEvent(0, context, _basic, failure_mode_1)

        discrete_event_simulation = DiscreteEventSimulation(0, 3, context)

        discrete_event_simulation._execute_b_event(detectable_failure_event)

        self.assertEqual(_basic.status, Status.FAILED)

        expected_c_events_set = set([OrderRepairEvent(
            priority=CEventPriority.ORDER_REPAIR_EVENT,
            context=context,
            component=_basic,
            event=detectable_failure_event,
            failure_mode=failure_mode_1
        )
        ])
        self.assertEqual(discrete_event_simulation.context.c_events_set, expected_c_events_set)

    def test__execute_b_event__inspection(self):
        inspection_name = "long_shut_down"
        inspection_period = 4
        inspection_duration = 2

        phase = Phase("phase_test", DeterministicLaw([10]), True)
        phase.set_next_phase(PhaseManager.NO_PHASE)

        failure_mode_1 = FailureMode("test__execute_b_event",
                                     DeterministicLaw([10]),
                                     DeterministicLaw([10]),
                                     Failure(FailureType.DETECTABLE),
                                     [phase],
                                     Inspection(inspection_name, inspection_period, inspection_duration),
                                     [phase],
                                     None,
                                     'AFTER_REPAIR',
                                     [phase])

        phase_manager = PhaseManager([phase],set())

        root_component = Compound(1, "ROOT", 0, [], And(), [])
        _basic = Basic(2, "BASIC", 0, [root_component], failure_mode_1, [], [])
        root_component.add_children_list([_basic])

        rca_manager = RootCauseAnalysisManager(set(), root_component.to_set())


        context = Context(root_component, phase_manager, rca_manager, set(), set())

        inspection_event = StartInspectionEvent(0, context, _basic, failure_mode_1)

        discrete_event_simulation = DiscreteEventSimulation(0, 3, context)

        discrete_event_simulation._execute_b_event(inspection_event)

        self.assertEqual(_basic.status, Status.INSPECTION)

        expected_c_events_set = set([OrderEndInspectionEvent(
            priority=CEventPriority.ORDER_END_INSPECTION_EVENT,
            context=context,
            component=_basic,
            event=inspection_event,
            failure_mode=failure_mode_1
        )
        ])

        self.assertEqual(discrete_event_simulation.context.c_events_set, expected_c_events_set)

    def test__execute_b_event__blind_failure(self):
        phase = Phase("phase_test", DeterministicLaw([10]), True)
        phase.set_next_phase(PhaseManager.NO_PHASE)

        failure_mode_1 = FailureMode("test__execute_b_event",
                                     DeterministicLaw([1]),
                                     DeterministicLaw([1]),
                                     Failure(FailureType.BLIND),
                                     [phase],
                                     None,
                                     [phase],
                                     None,
                                     'NEVER',
                                     [phase])

        phase_manager = PhaseManager([phase],set())

        root_component = Compound(1, "ROOT", 0, [], And(), [])
        _basic = Basic(2, "BASIC", 0, [root_component], failure_mode_1, [], [])
        root_component.add_children_list([_basic])

        rca_manager = RootCauseAnalysisManager(set(), root_component.to_set())
        context = Context(root_component, phase_manager, rca_manager)

        blind_failure_event = BlindFailureEvent(0, context, _basic, failure_mode_1)

        discrete_event_simulation = DiscreteEventSimulation(0, 3, context)

        discrete_event_simulation._execute_b_event(blind_failure_event)

        self.assertEqual(_basic.status, Status.BLIND_FAILED)
        self.assertEqual(discrete_event_simulation.context.c_events_set, set())

    def test__execute_c_events(self):
        phase = Phase("phase_test", DeterministicLaw(10), True)
        phase.set_next_phase(PhaseManager.NO_PHASE)

        failure_mode_1 = FailureMode("test__execute_c_event",
                                     DeterministicLaw([1]),
                                     DeterministicLaw([1]),
                                     Failure(FailureType.DETECTABLE),
                                     [phase],
                                     None,
                                     [phase],
                                     None,
                                     'AFTER_REPAIR',
                                     [phase])

        phase_manager = PhaseManager([phase],set())

        root_component = Compound(1, "ROOT", 0, [], And(), [])
        _basic = Basic(2, "BASIC", 0, [root_component], failure_mode_1, [], [])
        root_component.add_children_list([_basic])

        rca_manager = RootCauseAnalysisManager(set(), root_component.to_set())
        context = Context(root_component, phase_manager, rca_manager, set(), set())

        order_repair_event = OrderRepairEvent(priority=0,
                                              context=context,
                                              component=_basic,
                                              event=DetectableFailureEvent(0, context, _basic, failure_mode_1),
                                              failure_mode=failure_mode_1)

        discrete_event_simulation = DiscreteEventSimulation(0, 3, context, set(), set())
        discrete_event_simulation.context.c_events_set = set([order_repair_event])

        discrete_event_simulation._execute_c_events()

        expected_b_event_set = set([StartRepairingEvent(0, context, _basic, order_repair_event),
                                    EndRepairingEvent(1, context, _basic, order_repair_event, failure_mode_1)])

        self.assertEqual(expected_b_event_set, discrete_event_simulation.context.b_events_set)
        self.assertFalse(discrete_event_simulation.context.c_events_set)


if __name__ == '__main__':
    unittest.main()
