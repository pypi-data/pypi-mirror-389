"""
This module defines strings shared by Excel reader and exporter.
"""

from enum import Enum


class SystemTemplateSheet:
    """Names of worksheets is the file defining the system"""
    ARCHITECTURE = "ARCHITECTURE"
    FAILURE_MODES = "FAILURE_MODES"
    FAILURE_MODE_ASSIGNMENTS = "FAILURE_MODE_ASSIGNMENTS"
    MINIMAL_REPLACEABLE_UNIT = "MRU"
    INSPECTIONS = "INSPECTIONS"
    PHASES = "PHASES"
    ROOT_CAUSE_ANALYSIS = "ROOT_CAUSE_ANALYSIS"
    PHASE_JUMP = "PHASE_JUMP"


class SystemTemplateArchitectureColumn:
    """Column names of the Architecture sheet in the file defining the system"""
    COMPONENT_NAME = "COMPONENT_NAME"
    COMPONENT_TYPE = "COMPONENT_TYPE"
    COMPONENT_NUMBER = "COMPONENT_NUMBER"
    CHILDREN_NAME = "CHILDREN_NAME"
    CHILDREN_LOGIC = "CHILDREN_LOGIC"
    IN_MRU = "IN_MRU"
    TRIGGER_MRU = "TRIGGER_MRU"
    COMMENTS = "COMMENTS"


class SystemTemplateFailureModeAssignmentsColumn:
    """Column names of the Failure Mode Assignment worksheet"""
    COMPONENT_NAME = "COMPONENT_NAME"
    FAILURE_MODE_NAME = "FAILURE_MODE_NAME"
    COMMENTS = "COMMENTS"


class SystemTemplateFailureModeColumn:
    """Column names of the Failure Mode worksheet"""
    FAILURE_MODE_NAME = "FAILURE_MODE_NAME"
    FAILURE_LAW = "FAILURE_LAW"
    FAILURE_PARAMETERS = "FAILURE_PARAMETERS"
    REPAIR_LAW = "REPAIR_LAW"
    REPAIR_PARAMETERS = "REPAIR_PARAMETERS"
    TYPE_OF_FAILURE = "TYPE_OF_FAILURE"
    HELD_BEFORE_REPAIR = "HELD_BEFORE_REPAIR"
    INSPECTION_NAME = "INSPECTION_NAME"
    PHASE_NAME = "PHASE_NAME"
    PHASE_NEXT_IF_FAILURE_NAME = "NEXT_PHASE_IF_FAILURE"
    PHASE_CHANGE_TRIGGER = "PHASE_CHANGE_TRIGGER"
    HELD_AFTER_REPAIR = "HELD_AFTER_REPAIR"
    REPAIR_STRATEGY = "REPAIR_STRATEGY"
    COMMENTS = "COMMENTS"


class SystemTemplateMinimalReplaceableUnitColumn:
    """Column names of the Minimal Replaceable Unit worksheet"""
    MINIMAL_REPLACEABLE_UNIT_NAME = "MRU_NAME"
    REPAIR_LAW = "MRU_LAW"
    REPAIR_PARAMETERS = "MRU_PARAMETERS"
    REPAIR_SCHEDULE = "MRU_SCHEDULE"
    LOWEST_COMMON_ANCESTOR = "LOWEST_COMMON_ANCESTOR_SCOPE"
    TRIGGERING_STATUS = "TRIGGERING_STATUS"
    COMMENTS = "COMMENTS"


class SystemTemplateInspectionsColumn:
    """Column names of the Inspection worksheet"""
    INSPECTION_NAME = "INSPECTION_NAME"
    INSPECTION_PERIOD = "INSPECTION_PERIOD"
    INSPECTION_DURATION = "INSPECTION_DURATION"
    COMMENTS = "COMMENTS"


class SystemTemplatePhasesColumn:
    """Column names of the Phases worksheet"""
    PHASE_NAME = "PHASE_NAME"
    PHASE_LAW = "PHASE_LAW"
    PHASE_PARAMETERS = "PHASE_PARAMETERS"
    PHASE_NEXT = "NEXT_DEFAULT_PHASE"
    PHASE_FIRST = "FIRST_PHASE"
    PHASE_NEXT_IF_FAILURE = "NEXT_DEFAULT_PHASE_IF_FAILURE"
    COMMENTS = "COMMENTS"


class SystemTemplateRootCauseAnalysisColumn:
    """Column names of the Root Cause Analysis worksheet"""
    COMPONENT_NAME = "TRIGGERING_COMPONENT_NAME"
    COMPONENT_STATUS = "TRIGGERED_BY_COMPONENT_STATUS"
    PHASE = "TRIGGERED_IN_PHASE"
    COMMENTS = "COMMENTS"


class SystemTemplatePhaseJumpColumn:
    """Column names of the Phase Jump worksheet"""
    COMPONENT_NAME = "TRIGGERING_COMPONENT_NAME"
    COMPONENT_STATUS = "TRIGGERED_BY_COMPONENT_STATUS"
    FROM_PHASE = "FROM_PHASE"
    TO_PHASE = "TO_PHASE"
    COMMENTS = "COMMENTS"


class SystemTemplateField:
    """Default empty line - used only for exporting"""
    NONE = "NONE"


class SimulationMonteCarloColumn:
    MINIMUM_NUMBER_OF_SIMULATION = "MIN_NUMBER_OF_SIMULATION"
    MAXIMUM_NUMBER_OF_SIMULATION = "MAX_NUMBER_OF_SIMULATION"
    CONVERGENCE_MARGIN = "CONVERGENCE_MARGIN"
    MAXIMUM_EXECUTION_TIME = "MAX_EXECUTION_TIME"
    SEED = "SEED"
    DIAGNOSTICS = "DIAGNOSTICS"
    DURATION = "SIMULATION_DURATION"


class SimulationSplittingMonteCarloColumn:
    SYSTEM_ROOT_COMPONENT = "SYSTEM_ROOT_COMPONENT"


class SimulationSheet:
    SHEET = "SIMULATION"
    TYPE = "SIMULATION_TYPE"


class SimulationType:
    MONTE_CARLO = "MONTE_CARLO"
    QUASI_MONTE_CARLO = "QUASI_MONTE_CARLO"
    SPLITTING_MONTE_CARLO = "SPLITTING_MONTE_CARLO"
