[//]: # (Introduction part of AvailSim4 User Guide.)

# AvailSim4 project description

T. Cartier-Michaud, A. Apollonio, T. Buffet, M. Blaszkiewicz

CERN, TE-MPE-CB, Geneva, Switzerland

This document is a developer guide describing certain aspects relevant for project developers.

## Contributions

External contributions to the project are welcome. They can be provided through opening pull requests. It is highly recommended to discuss changes or additions through opening an issue beforehand.

Each contribution needs to agree to a Developer Certificate of Origin (DCO) by adding a dedicated `Signed-off-by:` line to all commits. Please use `git commit –signoff` in order to automate this. All merge requests must include a signature in the form: `Signed-off-by: Firstname Lastname <email.address@domain.org>`.

## File templates

Each file should contain a following license declaration:

```python
# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 202X. All rights not expressly granted are reserved.
```

## Coding conventions

Follow PEP 8 style guide for Python code. A quick list of often-encountered matters:

- Names of modules, packages, variables and other code elements, follow the standard Python naming conventions:
  - module, package, methods and variables should follow snake case (`function_name`),
  - classes, type variables should follow CapWords case (`ClassName`),
  - constants - uppercase (`CONSTANT`).
- Internal "private" methods should be indicated by an underscore (`_`).
- The recommended maximal line lenght is **120 characters**.
- Each class and function should have a docstring, see the examples below.
- For logging messages, use `%` operator for formatting strings.
- String quote character is expected to be double quotation mark `"`. Exceptions can be made to avoid escaping quote
characters.

Method docstring template:

```python
"""Single sentence description of the method.

Extended description with additional relevant details.

Args:
    argument: Description of the first argument. Generally, should mention type. If longer than one line, then intended
        right.
    other_argument: Description of the second argument.

Returns:
    Description of the method outcome.

Raises:
    NameError: Information about errors thrown by the function
"""
```

Class docstring template:

```python
"""Single sentence description of the class.

Additional description of the class.

Attributes:
    first_ attribute: Description of the first attribute. Generally, should mention type. If longer than one line, then
        intended right.
    other_argument: Description of the second argument.
"""
```

## References and resources



## `__hash__`, `__eq__` and `__lt__` of B events

| object | attributes | hash | eq | lt |
| --- | --- | --- | --- | --- |
| BEvent(Event) | absolute_occurrence_time, context, priority | None | absolute_occurrence_time, priority | absolute_occurrence_time, priority |
| BasicBEvent(BEvent) | absolute_occurrence_time, context, basic, priority | None | super() and basic | super() or super() and basic |
| FailureEvent(BasicBEvent) | absolute_occurrence_time, context, basic, failure_mode, priority | type, absolute_occurrence_time, priority, basic, failure_mode | super() and failure_mode | None |
| DetectableFailureEvent(FailureEvent) | absolute_occurrence_time, context, basic, failure_mode, priority | None | None | None |
| BlindFailureEvent(FailureEvent) | absolute_occurrence_time, context, basic, failure_mode, priority | None | None | None |
| EndHoldingEvent(BasicBEvent) | absolute_occurrence_time, context, basic, failure_mode, held_event, priority | type, absolute_occurrence_time, priority, basic, failure_mode, held_event | super() and failure_mode, held_event | None |
| StartInspectionEvent(BasicBEvent) | absolute_occurrence_time, context, basic, failure_mode, priority | type, absolute_occurrence_time, priority, basic, failure_mode | super() and failure_mode | None |
| EndInspectionEvent(BasicBEvent) | absolute_occurrence_time, context, basic, failure_mode, event, priority | type, absolute_occurrence_time, priority, basic, failure_mode, event | super() and failure_mode, event | None |
| NextPhaseEvent(BEvent) | absolute_occurrence_time, context, priority | type, absolute_occurrence_time, priority | super() | None |
| NextPhaseIfFailureEvent(NextPhaseEvent) | absolute_occurrence_time, context, priority | type, absolute_occurrence_time, priority | super() | None |
| JumpPhaseEvent(NexPhaseEvent) | absolute_occurrence_time, context, priority, failure_mode | type, absolute_occurrence_time, priority, failure_mode | super() and failure_mode| None |
| StartRepairingEvent(BasicBEvent) | absolute_occurrence_time, context, basic, priority, event | type, absolute_occurrence_time, basic, priority, event | super() and event | None |
| EndRepairingEvent(BasicBEvent) | absolute_occurrence_time, context, basic, priority, event, failure_mode | type, absolute_occurrence_time, basic, priority, event, failure_mode | super() and event | None |
| MinimalReplaceableUnitStartRepairingEvent(BasicBEvent) | absolute_occurrence_time, context, basic, priority, event | type, absolute_occurrence_time, basic, priority, event | super() and event | None |
| MinimalReplaceableUnitEndRepairingEvent(BasicBEvent) | absolute_occurrence_time, context, basic, priority, event, mru_trigger | type, absolute_occurrence_time, basic, priority, event, mru_trigger | super() and event, mru_trigger | None |



## `__hash__`, `__eq__` and `__lt__` of C events

WIP: try to remove useless attributes in the hash and equality as it is a significant part of the computation time.
For example, the priority is for now always chosen according to the type of event => redundant information !
Maybe the attribute 'event' could event be removed...

| object | attributes | hash | eq | lt |
| --- | --- | --- | --- | --- |
| CEvent(Event) | context, priority | None | priority  | priority |
| PostponeCEvent(CEvent) | context, priority, postpone_duration, b_event | type, priority, postpone_duration, b_event | super() and postpone_duration and b_event  | None |
| OrderNextPhaseEvent(CEvent) | context, priority | type, priority | super()  | None |
| OrderNextPhaseIfFailureEvent(CEvent) | context, priority, failure_mode | type, priority, failure_mode | super() and failure_mode  | None |
| OrderJumpPhaseEvent(CEvent) | context, priority, phase_jump_trigger | type, priority, phase_jump_trigger | super() and phase_jump_trigger  | None |
| ComponentCEvent(CEvent) | context, priority, component | type, priority, component | super() and component  | super() and component |
| OrderFailureEven(ComponentCEvent) | context, priority, component, event, failure_mode | type, priority, component, event, failure_mode | super() and event and failure_mode  | None |
| ReevaluateOrderAllFailureEvent(ComponentCEvent) | context, priority, component, event | type, priority, component, event | super() and event  | None |
| OrderEndHoldingEvent(ComponentCEvent) | context, priority, component, event, failure_mode, held_event, held_until_phase_set | type, priority, component, event, failure_mode, held_event | super() and event and failure_mode and held_event  | None |
| OrderStartInspectionEvent(ComponentCEvent) | context, priority, component, event, failure_mode | type, priority, component, event, failure_mode | super() and event and failure_mode  | None |
| OrderEndInspectionEvent(ComponentCEvent) | context, priority, component, event, failure_mode | type, priority, component, event, failure_mode | super() and event and failure_mode  | None |
| ReevaluateOrderAllInspectionEvent(ComponentCEvent) | context, priority, component, event | type, priority, component, event | super() and event  | None |
| MinimalReplaceableUnitOrderRepairEvent(ComponentCEvent) | context, priority, component, mru | type, priority, component, mru | super() and mru  | None |
| OrderRepairEvent(ComponentCEvent) | context, priority, component, event, failure_mode | type, priority, component, event, failure_mode | super() and event and failure_mode | None |

## License

Copyright © CERN 2021. Released under the [GPL 3.0 only license](../../LICENSE). All rights not expressly granted are reserved.
