[//]: # (Introduction part of AvailSim4 User Guide.)

# AvailSim4 project description

T. Cartier-Michaud, A. Apollonio, T. Buffet, M. Blaszkiewicz

CERN, TE-MPE-CB, Geneva, Switzerland

This document is a user guide describing the inputs of AvailSim4 and the features behind it.

## List of contents

[[_TOC_]]

## Introduction

AvailSim4 is a software used to predict the reliability and availability of complex systems. The main use cases at CERN
are accelerators belonging to the CERN complex, as well as accelerators of collaborating institutes or projects (e.g.
[MYRRHA](https://sckcen.be/en/Technology_future/MYRRHA)). In addition, specific machine protection studies(e.g.
for the HL-LHC Inner Triplet magnets protection [^1]) are carried out with this tool. The computational core of the
software is a Discrete Event Simulation (DES) engine, which simulates the failure behavior of a system over a specified
period of time. The evolution of the system follows a set of rules defined by the programmer/user, which determines the
next state of the system depending on its current state, see figure below for a high level schematic of the algorithm.
![DES](./figures/chart_DES.png "Principle of Discrete Event Simulation")

A simple example of the timeline of a system is sketched in the figure below.
![timeline](./figures/simpleTimeLine.png "Example of a timeline")

Evaluation of a system's timeline can last from milliseconds to minutes depending on the number of components inside the
system and the number of events to simulate. This computation is typically performed from 10<sup>2</sup> to 10<sup>
7</sup> times inside the Monte Carlo algorithm to generate statistics of reliability and availability. In addition, due
the possible uncertainty on some input parameters, a study generally requires to run the Monte Carlo algorithm multiple
times, from 10 to 10<sup>3</sup> times, to perform a so-called sensitivity analysis over defined sets of parameters
specifying the system’s failure behavior. Despite handling the time in a discrete manner (which accelerates the
computation as each time step simulated modifies the state of the system, no time step is useless), this approach is
computationally expensive as Monte Carlo algorithms converge slowly and the sensitivity analysis is not performed
analytically. Still, this is a powerful method allowing to model complex time dependencies between components and
providing an in-depth monitoring of complex systems. Below is the pseudo-code for the nested loops of the algorithm:

```python
# sensitivity analysis
for uniqueInput in listOfInputs:
   # Monte Carlo algorithm
   for idSimulation in range(0,numberOfSimulations):
       # Discrete Event Simulation algorithm
       while t < t_end
           # handling events
```

[^1]: Reliability studies for HL-LHC Inner Triplet magnets
protection: [internal note edms 2308131](https://edms.cern.ch/document/2308131/1)

## Inputs

Standard inputs of AvailSim4 are grouped in three files:

- system file, describing the modelled system,
- simulation file, detailing configuration of the simulations,
- sensitivity analysis file, containing settings of the sensitivity analysis.

Each file has a pre-defined structure of spreadsheets and columns within them. The next subsections give an overview of
each of the inputs files and their expected structure.

Certain values can be repeated in different locations to establish links. In this document, those locations are
marked as `PK` (which stands for `Primary Key`) and `FK` (stands for `Foreign Key`). The primary keys must be unique
for each record in the table and foreign keys represent the corresponding PK in another other locations of the input.

Some of the cells may require defining more than one value. AvailSim4 inputs accept individual values as well as one
and two dimensional lists. Valid examples include:

* `1`
* `2.0`
* `1, 2, 3, 4`
* `paramter_A`
* `parameter_A, parameter_B`
* `[1, 2, 3, 4]`
* `[parameter_A, parameter_B]`
* `[[1.0, 2.0, 3.5], [4.0, 5.5, 6.0]]`

The case (upper/lower) is not important. Usage of most special characters is discouraged. Quotation marks and spaces are
ignored (and, as such, can be used freely, keeping in mind that they have no effect).

In addition, cells supporting lists can be specified using Python literals. To do that, utilize standard Python
functions preceeding them with a `#` sign. For instance, using the following string in a cell: `#range(0, 10)` is
equivalent to specifying `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]`.

### `ARCHITECTURE` input sheet

A system is described by a tree in which each node represents a component.
`Basic` components are the leaves. They are actual components (or groups of physical components) to which a failure mode
is assigned. Thus, a basic component would fail according to its failure mode, not according to any children component
as it is a leaf in the system's tree. The status of a basic component is determined by its history, depending on if a
failure mode impacted that component, or any other feature such as periodic inspection.
`Compound` components are defined to group basic components, they are the nodes of the tree. Such components are used to
conveniently express redundancy in a subset of components or to initialize the system itself when symmetries can be
found within the tree. Also, it can provide a desired granularity to compute statistics. A compound component is said to
have children, which can be either compound or basic. The state of a compound component is defined by states of its
children, following rules defined in the inputs.

Below is an example of a system.
![system](./figures/systemDescription.png)
In the sketch above, `fm` stands for failure mode. The basic component A has 1 failure mode. The basic components C1 and
C2 have the same failure mode which means they are subject to the same mechanism of failure, while still failing at
independent times.

| | ARCHITECTURE | |
| --- | --- | --- |
| PK | `COMPONENT_NAME` | name of a component |
|  | `COMPONENT_TYPE` | component's type defined using keywords `basic` or `compound` |
|  | `COMPONENT_NUMBER` | number of times that component is repeated in a given location of the tree |
| FK | `CHILDREN_NAME` | **optional** (`none`) if the component is a basic; a list of `COMPONENT_NAME` required if the component is a compound |
|  | `CHILDREN_LOGIC` |  **optional** (`none`) if the component is a basic; a reference to a logical function required if the component is of compound type|
|  | `IN_MRU` |  **optional** (`none`) if the component is not part of a minimal replaceable unit, otherwise a list of `MRU` |
|  | `TRIGGER_MRU` | **optional** (`none`) if the component does not trigger any `MRU`, otherwise a list of `MRU` names which will be triggered |
|  | `COMMENTS` | **optional** notes |

The component specified in the first row of the sheet has to be the root element of the tree. Thus the `ARCHITECTURE` of
the system sketched above is the following:
![exampleOfARCHITECTURE](./figures/example_of_ARCHITECTURE_sheet.png)

Note that components which are not connected to the tree (i.e. are not listed as child of any compound), will be removed
when the simulation is executed.

#### Shared children

A feature "shared children" was added to enable defining a component as a child of several parents. If this
feature is not used to model a system, it means the system matches the definition of a tree. If it is used,
the system becomes a [directed acyclic graph](https://en.wikipedia.org/wiki/Directed_acyclic_graph). To specify
that a child with the name "sharedChildrenName" is shared by several parents, the name of the shared child has to be
listed in the `CHILDREN_NAME` of each parent. The name is given with the syntax "sharedChildrenName(lowestCommonParent)"
where the "lowestCommonParent" defines a scope in which the child is shared, see illustrations below.

![noShareChild](./figures/notShared.png)
The component PS (power supply) is not shared by any component. The component is simply called by its name in the
column "CHILDREN_NAME" of the row corresponding to the component A.

![secChild](./figures/secShared.png)
The component PS (power supply) is shared by components A and B, being unique in each sector "sec". The component is
called with the syntax "PS(sec)" in the column `CHILDREN_NAME` of the row corresponding to the components A and B. The
red boxes represent the scope of each shared child, associated to each component named "sec".

![rootChild](./figures/rootShared.png)
The component PS (power supply) is shared by components A and B, being unique in the overall system. The component is
called with the syntax "PS(ROOT)" in the column `CHILDREN_NAME` of the row corresponding to the "ROOT"
component. The red box represents the unique scope of the unique shared child.

#### Status and `CHILDREN_LOGIC`

Each component is in a certain state at any time. The statuses are defined below:

* `FAILED` : Operation stopped because of a fault (basic components) or faults of children. It is the most critical
status for availability as it stops operation.
* `BLIND_FAILED` : Similar to `FAILED` but for undetectable failures. It is the most critical status for protection
systems because the protection functionality might be lost without a possibility to detect it.
* `DEGRADED` : Intermediate status between `FAILED` and `RUNNING`, the component is still `RUNNING` but not in the
nominal conditions. It is less critical than failures as the machine still runs. That status is only taken
by `COMPOUND` with redundant children when the redundancy is still satisfied but some failure(s) already occurred.
* `BLIND_DEGRADED` : Similar to `DEGRADED` but for undetectable failures. It is also less critical than `FAILED`
statuses as the machine still runs, but the failure being blind, no repairs can be scheduled. For protection systems,
a critical loss of redundancy can be produced.
* `HELD` : A component has been repaired but it is not yet released into the `RUNNING` status as it is waiting for a
particular phase prior to be released.
* `INSPECTION` : Period of inspection.
* `UNDER_REPAIR` : Period of repair.
* `RUNNING` : Normal operation.

The default status of a basic component is `RUNNING`, which switches to `FAILED` (`BLIND_FAILED`) when its failure mode
triggers a (blind) failure. Then a repair event would change its status to `UNDER_REPAIR`. Periodic inspections could
set the status to `INPSPECTION`. `DEGRADED` and `BLIND_DEGRADED` can only appear for compound components. In fact, to
define the status of a compound component, one has to use the function specified in the `CHILDREN_LOGIC`
column. Several logics are defined:

* `XOOY` meaning X components must be functioning `Out Of` Y
* `ZTF` with Z = Y-X, the number of `Tolerated Faults`
* `XRC` with X as in  `XOOY`, the number of `Required Components`
* `AND` equivalent to `YOOY`, no fault of the children are tolerated

Internally, the code handles those 4 logics by translating them into `OO` logic. In order to compute those statutes, an
intermediate variable is introduced, the number of children "considered as running", that is to say with one of the
following statuses: `DEGRADED`, `BLIND_DEGRADED` or `RUNNING`. nCAR is the number of children "considered as running" in
the following table.

| status of the parent | `XOOY` |
| --- | --- |
| `INSPECTION` (I)      | if not enough "considered as running" children (nCAR<X) and at least one I|
| `UNDER_REPAIR` (UR)   | if not enough "considered as running" children (nCAR<X) and at least one UR and no I|
| `BLIND_FAILED` (BF)   | if not enough "considered as running" children (nCAR<X) and at least one BF but no I or UR|
| `FAILED` (F)          | if not enough "considered as running" children (nCAR<X) and no BF, I or UR|
| `DEGRADED` (D)        | if enough "considered as running" children (nCAR>=X) and no BF|
| `BLIND_DEGRADED` (BD) | if enough "considered as running" children (nCAR>=X) and at least one BF|
| `RUNNING` (R)         | if every child is R (nR==Y)|

### `FAILURE_MODES` and `FAILURE_MODE_ASSIGNMENTS` input sheets

A failure mode is the description of a failure and repair process. For simplicity of modelling, only a unique failure
mode can be attached to a single basic component. If the physical component is senstive to several failure modes, as,
for example, an active electronic component could fail due to high temperature, vibrations, high voltage/current, etc,
one has to split that component into as many basic components as the number of failure modes needed.

A failure mode is defined using the `FAILURE_MODES` sheet as below:

| | `FAILURE_MODES` | |
| --- | --- | --- |
| PK | `FAILURE_MODE_NAME` | name of the failure mode |
| | `FAILURE_LAW`| a probability law used to predict the time before the next failure; [available options](#probability-laws-used-to-define-duration-of-events)|
| | `FAILURE_PARAMETERS`| the parameters used to feed the `FAILURE_LAW`; see [available options](#probability-laws-used-to-define-duration-of-events) for examples |
| | `REPAIR_LAW`| a probability law used to predict the duration of a repair; [available options](#probability-laws-used-to-define-duration-of-events)|
| | `REPAIR_PARAMETERS`| the parameters used to feed the `REPAIR_LAW`|
| | `TYPE_OF_FAILURE`| `DETECTABLE` or `BLIND` depending on the possibility to monitor a failure. `BLIND` failures can only be detected and repaired by an [`INSPECTION`](#input-sheet-describing-the-inspections-inspections) or an [`MRU`](#input-sheet-describing-the-minimal-replaceable-units-mru).|
| | `HELD_BEFORE_REPAIR` | **optional** - defaults to `NEVER_HELD`; after a failure, a component might not be repaired immediately so it would stay in a `FAILED` or `BLIND_FAILED` status until a specific phase is reached. This argument is defined using either a list of phases (`[PHASE_A,PHASE_B,…]`), or the keyword `HELD_FOREVER` (the component is held until an MRU or periodic inspection unlocks it) or `NEVER_HELD` which is the default value (the component is immediately repaired) and should be used if this feature shall be ignored.|
| | `INSPECTION_NAME`| **optional** - defaults to `NONE`; a periodic inspection of a (blind) failure mode can be performed by linking an [`INSPECTION`](#input-sheet-describing-the-inspections-inspections) element. The respective inspection will be able to identify and repair the blind failure. Put `NONE` if this feature is not used. |
| | `PHASE_NAME`| **optional** - defaults to all phases; if a failure mode can only occur during particular phases, a list can be provided; e.g. `[PHASE_A,PHASE_B,…]`.|
| | `NEXT_PHASE_IF_FAILURE`| **optional** - defaults to `NONE`; a failure mode can bypass the default sequence of phases by requiring to go to a particular phase, in case of simultaneous failures, `NEXT_PHASE_IF_FAILURE` has priority over the `NEXT_DEFAULT_PHASE_IF_FAILURE` (see [table below](#input-sheet-describing-the-phases-phases) for more details on how to control phases). |
| | `PHASE_CHANGE_TRIGGER` | **optional** - defaults to `NEVER`; when a failure occurs one can force the phase to change: (1) immediately after failure taking place using the keyword `AFTER_FAILURE`, (2) after completion of a repair using keyword `AFTER_REPAIR` when the root node is working again, (3)to never change the phase by this failure mode with the keyword `NEVER`. For a blind failure, the timing should be `NEVER` or `AFTER_FAILURE`, it makes no sense to set the value to `AFTER_REPAIR`. |
| | `HELD_AFTER_REPAIR` | **optional** - defaults to `NEVER_HELD`; after a component has been repaired, it might not go back to the `RUNNING` state immediately but it could stay in an `HELD` status until a specific phase is reached. This argument is filled using, either a list of phases, or the keyword `HELD_FOREVER` (the component is held until an MRU or periodic inspection unlocks it) or `NEVER_HELD` which is the default value (the component is immediately released from its `HELD` status to the `RUNNING` status). |
|  | `COMMENTS` | optional notes |

The link between a component and failure mode is defined in the sheet `FAILURE_MODE_ASSIGNMENTS` as below:

| | `FAILURE_MODE_ASSIGNMENTS` | |
| --- | --- | --- |
| FK | `COMPONENT_NAME` | component name from the `ARCHITECTURE` sheet |
| FK | `FAILURE_MODE_NAME` | failure mode name from the `FAILURE_MODES` sheet |

### `MRU` input sheet

`MRU` stands for Minimal Replaceable Unit. In some cases, to repair a unique failed component one has to replace a
subset of components which forms a "minimal replaceable unit". It would be the case when a faulty unit/rack is replaced
by a spare one, while the failure mode investigations and actual repair are done afterwards offsite. This can lead to
better availability while in-depth diagnostics are performed at a deferred stage. It can also reduce the dose received
by operators.

In AvailSim4, two arguments in the system file - `ARCHITECTURE` sheet are used to specify the mechanisms of an `MRU`.
First, a component can be a part of a subset of components replaced when the `MRU` is triggered, this is controlled by
the argument `IN_MRU` of the sheet `ARCHITECTURE`. Then, the replacement of that `MRU` is triggered when an arbitrary
subset of components fall into a given state - those components are identified by the argument `TRIGGER_MRU` of the
sheet `ARCHITECTURE`. Having two arguments allows greater flexibility: a component could be in an `MRU` but never
trigger any `MRU` because its failure is not monitored for example. This feature allows for "long range out of the tree
logic" interactions without using complex/artificial "shared child" logic. The rest of the parameters of the `MRU` are
defined in the sheet `MRU`. One important parameter for the topology of the system is the `LOWEST_COMMON_ANCESTOR_SCOPE`
which define a scope similarly to the shared child feature. Using tree parameters, it allows to model different
configurations such as the tree cases described below.

![MRU_trigger](./figures/MRU_map.png)

A defined failure of the component A, which is expensive, triggers a replacement of the `MRU` consisting of the two
components C which are cheap. If any component C fails, it only triggers the replacement of the two C components, not
the component A.

![MRU_one_scope](./figures/MRU_lca_root.png)

The ROOT component defines the lowest common ancestor scope of the `MRU`, only one `MRU` is present in the system (the
yellow box). If the MRU is triggered, every PS in the system will be changed

![MRU_two_scopes](./figures/MRU_lca_sec.png)

The component sec defines the lowest common ancestor scope of the MRU, two scopes are defined for the two sec
components. If an MRU is triggered, only the two PS in one sector will be changed.

The definition of a `MRU` also requires extra parameters reported in the table below.

| | `MRU` | |
| --- | --- | --- |
| PK | `MRU_NAME` | name of a `MRU` |
|  | `MRU_LAW` | statistical law used to estimate the duration of the `MRU` repair/intervention (`fix` = constant duration, `exp` = exponential, etc.) [available options](#probability-laws-used-to-define-duration-of-events)|
|  | `MRU_PARAMETERS` | parameters used for the `MRU_LAW` provided, see [available options](#probability-laws-used-to-define-duration-of-events) for examples|
|  | `MRU_SCHEDULE` | not implemented yet, leave empty or put `immediate` for future compatibility; the execution of the `MRU` could be `immediate` or after a particular delay |
| FK | `LOWEST_COMMON_ANCESTOR_SCOPE` | this is a `COMPONENT_NAME` in the path between a component and the root component, it defines the size of the scope (see figures above); this column can also contain a list of all possible lowest common ancestors for the MRU components. **Optional** - if left empty, the root of the system is assumed to be the lowest common ancestor |
|  | `TRIGGERING_STATUS` | list of statuses that a triggering component should take to trigger the MRU, e.g. `UNDER_REPAIR`  |
|  | `COMMENTS` | optional notes |

### `PHASES` input sheet

Many systems are not static systems but dynamic systems which have different modes of operations. A simple example of
operational modes would be "switched off", "switching on", "operating", "switching off". While "switched off" and
"operating" can be seen as static modes, going from one to the other might imply significant transients, changing the
environmental condition (temperature, pressure, vibrations, etc) and often requiring software sequences. Such operations
can be sensitive to "failure on demand".

In order to model these different regimes, the phases feature has been developed. It is tailored to the needs of LHC,
which operates in cycles of about 15 phases. Then each phase and their sequence are described in the sheet `PHASES` as
shown in the table below. If a system does not require phases to be modeled, this table can remain empty. Generally,
phases are defined across the entire system; i.e. phases cannot be defined for single components or sub-systems.

| | `PHASES` | |
| --- | --- | --- |
| PK | `PHASE_NAME` | name of the phase. Do not use the name `NONE` as it is a keyword reserved for special, default phase defined in the code.|
| | `PHASE_LAW` | a probability law used to predict the duration of the phase; [available options](#probability-laws-used-to-define-duration-of-events) |
| | `PHASE_PARAMETERS` | the parameters used to feed the `PHASE_LAW` |
| | `FIRST_PHASE` | boolean value (`True`/`False`, or `0`/`1`) used to define the initial phase. `True` or `1` for the initial phase and `False` or `0` for the rest.  **Optional** - defaults to `FALSE`. Note that the system has to have exactly one phase with this value set to `True`.|
| FK | `NEXT_DEFAULT_PHASE` | name of the phase in which the system goes after the current phase ends without a failure|
| FK | `NEXT_DEFAULT_PHASE_IF_FAILURE` | name of the phase in which the system goes as soon as any failure occurs in the current phase. This can can be overruled in the `FAILURE_MODE` sheet if a specific failure mode requires a different sequence of phases. **Optional** - defaults to `NONE`. |
|  | `COMMENTS` | optional notes |

A timeline showing a sequence of phases is presented below:
![MRU](./figures/simple_phases_timeline.png)

The phase sheet can be left empty if no phases should be used. In that case, a 'dummy'-phase `None` will automatically created.

### `PHASE_JUMP` input sheet

In order to be able to change the phase of the system using any component and any status (not only basic failing),
an extra mechanism is used, the `PHASE_JUMP`. In this sheet, triggers are defined as below:

| `PHASE_JUMP` | |
| --- | --- |
| `TRIGGERING_COMPONENT_NAME` | the name of a component that should trigger the jump|
| `TRIGGERED_BY_COMPONENT_STATUS` | list of statuses that will trigger the jump; e.g. `[FAILED,UNDER_REPAIR]`|
| `FROM_PHASE` | list of phases in which the given rule will apply; e.g. `[PHASE_A,PHASE_B]`. **Optional** - defaults to all phases.|
| `TO_PHASE` | phase in which the system will jump; e.g. `[PHASE_C]` |
|  `COMMENTS` | optional notes |

### `INSPECTIONS` input sheet

In order to increase availability and reliability, components can be repaired or replaced before they fail. In order to
model such strategy, periodic inspections are used. They are described in the sheet `INSPECTIONS` by the following
argument:

| | `INSPECTIONS` | |
| --- | --- | --- |
| PK | `INSPECTION_NAME` | name of the inspection |
| | `INSPECTION_PERIOD` | the duration after which an inspection is performed; note that it is constant and deterministic |
| | `INSPECTION_DURATION` | the duration of the inspection (and repair) itself |
| | `COMMENTS` | optional notes |

Inspections are attached to failure modes, in the `FAILURE_MODES` sheet, because an inspection does not necessarily
detect every blind failure of a component. Some inspections can be performed remotely as a software check-up or even a
test. Any inspection lasts a predefined amount of time and causes all randomly-scheduled events to be assigned new
execution times (for exponentially distiributed events it is not a problem, for other, to maintain properties of the
selected probability distribution -- inspections should not be used at all or with particular caution). Inspections
count towards overall elapsed time, as well as phase and component statistics, since conceptually (for now) they are
events just like failures or repairs.

### `ROOT_CAUSE_ANALYSIS` input sheet

Root cause analysis feature is useful to understand more complex dependencies underlying observed failures. In this input
sheet, users can define a list of components and corresponding statuses which will be monitored during the simulation. When
selected component's status changes to the one listed in this sheet, statuses of all components in the system will be recorded
and saved in a ROOT_CAUSE_ANALYSIS_RESULTS sheet. To save the results, user has to specify "RCA" diagnostic in the simulation file.

| `ROOT_CAUSE_ANALYSIS` | |
| --- | --- |
| `TRIGGERING_COMPONENT_NAME` | the name of a component that should trigger the root cause analysis snapshot |
| `TRIGGERED_BY_COMPONENT_STATUS` | list of statuses that will trigger the snapshot when the component is assinged them |
| `TRIGGERED_IN_PHASE` | list of phases in which given rule will apply; **optional** - by default all |
| `COMMENTS` | optional notes |

The root cause analysis can also be used as detailed extended timeline, by setting all components, all component statuses, and all phases as triggers. In order to be able to read the correct sequence of events in the generated output, the number of simulations has to be set to one in the simulation file.

### `SIMULATION` input file

A file, named with the suffix "_simulation.xlsx", is used to describe the numerical parameters of a simulation, that is
to specify the parameters of the Monte Carlo algorithm.

| SIMULATION | |
| --- | --- |
| `SIMULATION_TYPE` | type of simulation, available options: `MONTE_CARLO` and `QUASI_MONTE_CARLO` (Monte Carlo approach based on low-discrepancy sequences instead of standard pseudo-random numbers) |
| `MIN_NUMBER_OF_SIMULATION` | the minimum number of iterations performed in the Monte Carlo algorithm (number of Discrete Event Simulation evaluations)|
| `MAX_NUMBER_OF_SIMULATION` | the maximum number of iterations performed in the Monte Carlo algorithm (number of Discrete Event Simulation evaluations). **Optional** - by default equal to `MIN_NUMBER_OF_SIMULATION` |
| `CONVERGENCE_MARGIN` | not implemented yet, early stop criterion used to adapt the number of iterations to the value of the probability one wants to estimate. **Optional** and not required, any value will be ignored. |
| `MAX_EXECUTION_TIME` | not implemented yet, early stop criterion based on the computation time. Not required, any value will be ignored, except for execution with HTCondor argument, where this value (increased by 10%) is used as a job parameter. **Optional** - by default set to 10 times the number of iterations. |
| `SEED` | the seed used by the random generator. Such a parameter is useful for reproducibility and can be used to distribute Monte Carlo iterations over different jobs in a batch scheduler. When `None` is used as the value, the random number generator will use a self-generated "random" seed. **Optional** - by default `None`. |
| `DIAGNOSTICS` | Defines exported results. Define list of required results from the available options:  `SUMMARY` providing statistics for components and their statuses, `LAST_TIMELINE` printing the timeline of the last Monte Carlo iteration, `RCA` to save root cause analysis results, `COMPONENT_TREE_SIMPLE` and `COMPONENT_TREE_EXTENDED` to get a schematic of the tree. `CRITICAL_FAILURE_PATHS` to save minimal critical failure paths of the system. See the output section for more details. **Optional** - by default `SUMMARY`. |
| `SIMULATION_DURATION` | duration of the simulated period |
| `COMMENTS` | optional notes |

### `SENSITIVITY_ANALYSIS` input file

The framework supports running a limited sensitivity analysis to observe the impact of input parameters changes
on the simulation outcomes. Users may select individual input paramaters and provide a list of values which will be used
to replace the original values from the system input file in the simulation runs. This is equivalent to creating
multiple system files and controlling their execution directly. The sensitivity analysis feature provides a streamlined
way to acheive the same result - which becomes crucial once the number of paramaters grows and managing the instances
individually is difficult.

The input provides means to modify more than one parameter. The exploration strategies mechanism allows changes to be
applied one at the time, be mixed with other parameter changes or be matched positionally with them. For more
details, see explanations provided below.

| `SENSITIVITY_ANALYSIS` | |
| --- | --- |
| `PARAMETER_NAME` | the name of the parameter and primary key to explore in the format `name_of_the_parameter`/`primary_key`, see below for more details |
| `VALUES` | a list of values to explore |
| `EXPLORATION_STRATEGY` | one of the following keywords: `INNER`, `OUTER` or `ZIP`|
| `COMMENTS` | optional notes |

One special value, `SEED`, can be used to control the number of instances running the simulations, which is a
particularly useful for distributed and multicore environments. Using `SEED` as the `PARAMETER_NAME` and providing the
list of seeds in the `VALUES` cell will trigger the simulations with different seeds (i.e., independent from others).

#### Parameter name

This parameter name is expressed usign the following syntax: `name_of_the_parameter`/`primary_key`;
`name_of_the_parameter` is the column name which values will be modified, the `primary_key` is the key indicating the
row where one wants to change values. Column names are unique across the entire system input file, so they uniquely
identify the space of the modification. The primary key is an individual column in each table which is selected to be
unique across all rows in a table. Usually it is the component or failure mode name; to make sure, see the relevant
section of this guide.

For instance, `FAILURE_PARAMETERS`/`POWER_SUPPLY_FAILURE` means that the row will be modifying values of the
`FAILURE_PARAMETERS` cell for the failure mode `POWER_SUPPLY_FAILURE`.

#### Values

It is important to mention that the sensitivity analysis takes a list of arguments of the same type as the one used in
the first place. For example, in case of the `FAILURE_PARAMETERS`, the input is normally a list of one or more elements:
the first case covers the use of the exponential distribution which is defined using its mean only, the second case
covers the use of the normal law which is defined by its mean and standard deviation. In that particular case, the
sensitivity analysis requires a list to run, such as `[mean1, mean2]` in case of one-parameter distributions
or a list of lists, such as `[[mean1,std1], [mean2,st2]]`, in case of other distributions.

The list of values `VALUES` can be explicit, but it can also be entered as a python expression using `#` at the beginning.
This expression can use `numpy` and should either return a `list`, a `range` or a `numpy.array` such as:

* `#[x**2 for x in range(10)]`
* `#range(0,9000,1000)`
* `#numpy.random.normal(10,1,size=(100,))`

#### Exploration strategies

The exploration strategies decide how combinations of sensitivity analysis parameters will be combined in the resulting
simulations. There are three strategies defined so far: `INNER`, `OUTER`, `ZIP`.

To simplify the explanations, let us define the following notation. We assume that C<sub>system,simulation</sub> is the
initial configuration of system and simulation described by the input files. The n<sup>th</sup> modifier tuple is
defined as (T<sub>n</sub>,P<sub>n</sub>,L<sub>n</sub>), where:

* T<sub>n</sub> can take the following values: I, O, Z, respecitively for `INNER`, `OUTER` or `ZIP` strategy,
* P<sub>n</sub> is the modified parameter,
* L<sub>n</sub> is the list of values used to modify the parameter.

X = C([P=V]) is a copy of the initial configuration C except for the parameter P which takes the value V in that
instance.

The different sensitivity analysis strategies are producing the following new configurations:

* `INNER`: if one or several `INNER` strategies are defined, each resulting configuration is identical to C with
  singular modification that is only one of the values L<sub>n</sub> of the modified paramater P<sub>n</sub>. For
  example, having two `INNER` strategies (I,P1,[1,2,3]) and (I,P2,[11,12]) will produce the following list of
  configurations:
  * C([P1=1])
  * C([P1=2])
  * C([P1=3])
  * C([P2=11])
  * C([P2=12])
* `OUTER`: if one or several `OUTER` strategies are defined in the input file, each resulting configurations will be
  identical to C, except for the parameters targeted by the different strategies using an "outer product" approach. The
  difference from `INNER` strategy is that instead of going sequentially through consecutive modification rules, the
  modifications will be applied simultaneously, creating an "outer product" of modified parameters. For example, having
  two `OUTER` strategies (O,P1,[1,2,3]) and (O,P2,[11,12]) will produce the following list of configurations:
  * C([P1=1, P2=11])
  * C([P1=2, P2=11])
  * C([P1=3, P2=11])
  * C([P1=1, P2=12])
  * C([P1=2, P2=12])
  * C([P1=3, P2=12])
* `ZIP`: a `ZIP` strategy requires at least two rows with lists of equal lenghts to be defined properly. The resulting
  configurations will be all identical to C, except for the targeted parameters. However, instead of creating outer
  product of modfied values to be used, each value in L<sub>n</sub> is matched positionally with a value in
  L<sub>m</sub>. For example, having two `ZIP` strategies (Z,P1,[1,2,3]) and (Z,P2,[11,12,13]) will produce the
  following list of configurations:
  * C([P1=1, P2=11])
  * C([P1=2, P2=12])
  * C([P1=3, P2=13])

In case the `SENSITIVITY_ANALYSIS` sheet contains several rows describing different strategies, the modifiers are first
divided into groups accoriding to their exploration strategy. Those groups are dealt with according to the rules
described above. After this step is finished, an outer product is performed between all resulting modifiers of different
strategies. For example, having six strategies (I,P1,[1,2]), (I,P2,[11,12]), (O,P3,[a,b]), (O,P4,[D,E]),
(Z, P5, [x,c]), (Z, P6, [y,u]) will result in:

* The first step produces the following groups:
  * modifiers with `INNER` strategy from (I,P1,[1,2]) and (I,P2,[11,12]):
    * C([P1 = 1])
    * C([P1 = 2])
    * C([P2 = 11])
    * C([P2 = 12])
  * modifiers with `OUTER` strategy from (O,P3,[a,b]) and (O,P4,[D,E]):
    * C([P3 = a, P4 = D])
    * C([P3 = a, P4 = E])
    * C([P3 = b, P4 = D])
    * C([P3 = b, P4 = E])
  * modifiers with `ZIP` strategy from (Z, P5, [x,c]) and (Z, P6, [y,u]):
    * C([P5 = x, P6 = y])
    * C([P5 = c, P6 = u])
* In the second step, an outer product among all those parameters is created (see **Details** below for the full list)

<details>

* Example outer product result:
  * C([P1 = 1, P3=a, P4=D, P5 = x, P6 = y])
  * C([P1 = 1, P3=a, P4=D, P5 = c, P6 = u])
  * C([P1 = 1, P3=a, P4=E, P5 = x, P6 = y])
  * C([P1 = 1, P3=a, P4=E, P5 = c, P6 = u])
  * C([P1 = 1, P3=b, P4=D, P5 = x, P6 = y])
  * C([P1 = 1, P3=b, P4=D, P5 = c, P6 = u])
  * C([P1 = 1, P3=b, P4=E, P5 = x, P6 = y])
  * C([P1 = 1, P3=b, P4=E, P5 = c, P6 = u])
  * C([P1 = 2, P3=a, P4=D, P5 = x, P6 = y])
  * C([P1 = 2, P3=a, P4=D, P5 = c, P6 = u])
  * C([P1 = 2, P3=a, P4=E, P5 = x, P6 = y])
  * C([P1 = 2, P3=a, P4=E, P5 = c, P6 = u])
  * C([P1 = 2, P3=b, P4=D, P5 = x, P6 = y])
  * C([P1 = 2, P3=b, P4=D, P5 = c, P6 = u])
  * C([P1 = 2, P3=b, P4=E, P5 = x, P6 = y])
  * C([P1 = 2, P3=b, P4=E, P5 = c, P6 = u])
  * C([P2 = 11, P3=a, P4=D, P5 = x, P6 = y])
  * C([P2 = 11, P3=a, P4=D, P5 = c, P6 = u])
  * C([P2 = 11, P3=a, P4=E, P5 = x, P6 = y])
  * C([P2 = 11, P3=a, P4=E, P5 = c, P6 = u])
  * C([P2 = 11, P3=b, P4=D, P5 = x, P6 = y])
  * C([P2 = 11, P3=b, P4=D, P5 = c, P6 = u])
  * C([P2 = 11, P3=b, P4=E, P5 = x, P6 = y])
  * C([P2 = 11, P3=b, P4=E, P5 = c, P6 = u])
  * C([P2 = 12, P3=a, P4=D, P5 = x, P6 = y])
  * C([P2 = 12, P3=a, P4=D, P5 = c, P6 = u])
  * C([P2 = 12, P3=a, P4=E, P5 = x, P6 = y])
  * C([P2 = 12, P3=a, P4=E, P5 = c, P6 = u])
  * C([P2 = 12, P3=b, P4=D, P5 = x, P6 = y])
  * C([P2 = 12, P3=b, P4=D, P5 = c, P6 = u])
  * C([P2 = 12, P3=b, P4=E, P5 = x, P6 = y])
  * C([P2 = 12, P3=b, P4=E, P5 = c, P6 = u])

</details>

### Probability laws used to define duration of events

Duration of various elements of the model can be controlled by specifying the distributions from which samples are
drawn. Table below summarizes available options and specifies parameters that can be passed to define the distributions.
Listed aliases are the only ways to define a given probability law.
Note that durations are regenerated at every phase change and inspection. It is not advised to use them if system behavior is modeled with Weibull, Deterministic, Normal & Exponentiated Weibull distributions as this will alter system behaviour.

| Type | Aliases | Parameters |
| --- | ---- | --- |
| Deterministic | `FIX`, `DETERMINISTIC`, `DETERMINISTICLAW`, `DETERMINISTIC_LAW` | Single parameter defining a fixed duration |
| Normal | `NORMAL`, `NORMALLAW`, `NORMAL_LAW`| Two parameters: the first defines the mean and the second defines the standard deviation of the distribution |
| Exponential | `EXP`, `EXPONENTIAL`, `EXPONENTIALLAW`, `EXPONENTIAL_LAW` | The first parameter defines the scale (MTBF; inverse rate), the second one (optional) is a shift parameter. |
| Weibull | `weibull`, `WEIBULL`, `WEIBULLLAW`, `WEIBULL_LAW` | Accepts up to 3 parameters, the last one is optional. The first one is the scale (characteristic lifetime), the second defines the shape and the third one (optional) is the shift parameter. |
| Exponentiated Weibull | `EW`, `EXPWEI`, `EXPWEIBULL`, `EXPONENTIATEDWEIBULL` | Four parameters: scale, first shape, second shape and shift (location). |
| Binomial | `POFOD`, `FOD`,`BINOMIAL`, `BINOMIALLAW`, `BINOMIAL_LAW` | Probability to fail when entering a phase. If no phases are specified (`none` or empty cell), then the failure may occur at the beginning of any phase. |

### Optional python file describing custom children logic

It is possible for users to define some "custom children logic" following the same architecture as the [ChildrenLogic
class](/availsim4core/src/context/system/children_logic/children_logic.py), i.e. having an `__init__`, `__repr__` and `evaluate` function. The `CHILDREN_LOGIC` column in the `ARCHITECTURE` sheet of the file describing the system can then refer to those new children logics.
The name of the new class has to be in CAPITAL LETTERS in the python file because every input read by AvailSim4 is turned
into capital letters in order to be insensitive to the lower/upper case. How to point the simulation to the right input files
is described in the `README.md`, which is available in the root folder.

## Outputs

The output of the code is a unique `.xlsx` file containing several sheets and (optionally) additional image files.
Every sheet used as an input is copied to the output file to keep parameters and results together. When a
sensitivity analysis is used, the copied input sheets are the ones corresponding to the specific simulation performed,
that is to say the original input sheets modified by the respective set of sensitivity analysis parameters.

The rules of status propagation are listed in a table in section [Status and CHILDREN_LOGIC](#status-and-children_logic).
It is worth noting that `FAILED` (detectable failure) status of a basic component does not get propagated since it is
immediately followed by `UNDER_REPAIR` status.

Besides providing statistics of components' statuses, the `RESULTS` sheet accounts also for phases, listing them similarly
to statistics of other status changes.

The number of output sheets in the `.xlsx` file depends strictly on the `DIAGNOSTICS` column in the system input file.
To create a `RESULTS`, `RESULTS_ROOT_SUMMARY` and `RESULTS_PHASE_SUMMARY` sheets, only the `SUMMARY` option has to be
included in the `DIAGNOSTICS` column of the system input file.

### `RESULTS` output sheet

The most detailed sheet is the `RESULTS` sheet. At the end of each Discrete Event Simulation, the timeline
produced is used to compute different metrics (number of occurrences of an event type within a timeline, total duration
of an event type within a timeline) for each event present in the timeline (combination of `component` x `phase`
x `status` x `description`). With each new iteration of the Monte Carlo algorithm a few statistical measures are computed:
maximum value, mean value, standard deviation and a "BOOLEAN" value which is the number of timelines for which
a particular event occurred at least once. The "BOOLEAN" indicator is useful for reliability studies where one often
wants to know if some event occurred at least once.

Statistics of component statuses occurring in the simulations are presented grouped by component name, phase and
description. More details are presented in the table below.

| Column name             | Description |
| ---                     | --- |
| `component`             | Component of which status is described in a given row. |
| `phase`                 | Phase in which a component's status was present. |
| `status`                | Name of a component's status described by a given row. |
| `description`           | Text recounting a direct reason of entering a given status. Note that in the case of more than one failure causing the event described in the row, the description refers only to the last contributing event. Therefore, some statuses' statistics might be split into two or more separate rows. |
| `_MEAN_OCCURRENCES`     | Mean number of status's occurrences in all DES iterations. |
| `_MAX_OCCURRENCES`      | Maximum number of occurences of a given event in any DES iteration. |
| `_STD_OCCURRENCES`      | Standard deviation of numbers of occurences in any DES iteration. |
| `_BOOL_OCCURRENCES`     | Fraction of DES iterations in which a given status was observed. |
| `_MEAN_DURATION`        | Mean time elaspsed in a given status in all DES iterations. |
| `_MAX_DURATION`         | Maximum duration of a given event in any DES iteration. |
| `_STD_DURATION`         | Standard deviation of given event's duration in any DES iteration. |
| `_BOOLEAN_DURATION`     | Fraction of DES iterations in which a given status was observed. |

To create a `RESULTS` sheet, `SUMMARY` option has to be listed in
the `DIAGNOSTICS` column of the system input file.

Note that also `phase` statistics are available in the `RESULTS` sheet as a 'dummy'-component `Phase` is automatically created, which allows to infer detailed information about the triggering of `phases`.

### `RESULTS_ROOT_SUMMARY` output sheet

One sheet is dedicated to the statistics of the root component because it is often in the overall availability or
reliability that the user is interested. It contains the following statistics: uptime duration, downtime duration, total
and availability.

To create a `RESULTS_ROOT_SUMMARY` sheet, `SUMMARY` option has to be listed in
the `DIAGNOSTICS` column of the system input file.

### `RESULTS_PHASE_SUMMARY` output sheet

This results sheet is provides statistics about phases.  Contains the following information:

| Column name                                   | Description |
| ---                                           | --- |
| `OCCURRENCES`                                 | number of times the simulation entered a given phase |
| `TOTAL_DURATION`                              | total time spent in a given phase |
| `MEAN_DURATION`                               | average time spent in a given phase, calculated as total duration spent in a phase divided by the number of its occurrences |
| `NORMAL_START_OF_A_PHASE`                     | number of times when a phase was entered not because of any failures (i.e., with descriptions "default" or "Init") |
| `START_OF_A_PHASE_DUE_TO_A_FAILURE`           | number of times when a phase was entered because of a failure (i.e., with descriptions "default failure" or "specific failure") |
| `START_OF_A_PHASE_DUE_TO_A_SPECIFIC_FAILURE`  | number of times when a phase was entered because of a specific failure (i.e. with description "specific failure") |
| `SUM_OF_DETECTABLE_FAILURES_IN_A_PHASE`       | total number of detectable failures occurring in a given phase |
| `SUM_OF_BLIND_FAILURES_IN_A_PHASE`            | total number of blind failures occurring in a given phase |
| `TOTAL_DURATION_OF_THE_RUNNING_STATUS`        | total time the root component spent in a running state |
| `TOTAL_DURATION_OF_THE_UNDER_REPAIR_STATUS`   | total time the root component spent in an under repair state |
| `TOTAL_DURATION_OF_THE_DEGRADED_STATUS`       | total time the root component spent in a degraded state |
| `TOTAL_DURATION_OF_THE_BLIND_DEGRADED_STATUS` | total time the root component spent in a blind degraded state |
| `TOTAL_DURATION_OF_THE_FAILED_STATUS`         | total time the root component spent in a failed state |
| `TOTAL_DURATION_OF_THE_BLIND_FAILED_STATUS`   | total time the root component spent in a blind failed state |
| `TOTAL_DURATION_OF_THE_INSPECTION_STATUS`     | total time the root component spent in an inspection state |
| `RATIO_OF_PHASE_WITHOUT_DETECTABLE_FAILURES`  | difference between the number of phase occurences and the number of detectable failures divided by the number of phase occurences |
| `FRACTION_OF_UPTIME_WITHIN_THE_PHASE`         | total duration of system in running, degraded or blind degraded states divided by the phase duration |
| `FRACTION_OF_UPTIME_WITHIN_THE_TOTAL_DURATION`| total duration of system in running, degraded or blind degraded states divided by the simulation duration |

To create a `RESULTS_PHASE_SUMMARY` sheet, `SUMMARY` option has to be listed in
the `DIAGNOSTICS` column of the system input file.

### `EXECUTION_METRICS` output sheet

One sheet is dedicated to the metric of the simulation such as:

* the execution time, the number of DES simulations executed (compared to the number of DES simulations asked in the inputs),
* the mean/max/standard deviation number of time iterations in a DES,
* the mean/max/standard deviation number of b events executed in a DES,
* the mean/max/standard deviation number of c events executed in a DES,
* the mean/max/standard deviation number of b events removed in a DES,
* the mean/max/standard deviation number of c events removed in a DES,
* the mean/max/standard deviation number for the length of the time line,
* the number of compound components,
* the number of basic components.

This sheet is created automatically.

### `RESULTS_LAST_TIMELINE` output sheet

As explained in the introduction, the algorithm is based on the evaluation of timeline performed with a Discrete event
approach. Such timelines are produced using different random seeds within a Monte Carlo algorithm. Although the Monte
Carlo algorithm requires a large number of timelines to converge, already exporting just the last timeline can help
users to understand the sequence of events effectively happening in their model. Thus, this sheet is seen as a tool to
debug the input file. The output is as follows:

| LAST_TIMELINE | |
| --- | --- |
| `timestamp` | the timestamp at which an event occurred |
| `phase` | the phase in which an event occurred |
| `component` | the component on which the event occurred. If a model uses phases, one of the component is `PHASE`|
| `description` | a brief description of the event such as "power_converter_failure in INJECTION" |

To create a `RESULTS_LAST_TIMELINE` sheet, user has to specify `LAST_TIMELINE` option in the simulation input file.

### `RESULTS_ROOT_CAUSE_ANALYSIS_RESULTS` output sheet

This sheet contains a list of records that present the statuses of all components in the system when one of the specified
components enters given status (as defined in the input file `ROOT_CAUSE_ANALYSIS`).

| `RESULTS_ROOT_CAUSE_ANALYSIS` | |
| --- | --- |
| `analysis_id` | ID of the analysis; can be used to determine the seed or particular run of the algorithm in which the event occurred |
| `timestamp` | event's timestamp within a single DES iteration |
| `rca_component_trigger` | name of the component that triggered the snapshot |
| `rca_status_trigger` | status of the component that triggered the snapshot |
| `rca_phase_trigger` | phase in which the event took place |
| `snapshot_root_cause` | unique name of the component which triggered the chain of status changes in component tree that eventually led to the snapshot |
| `description` | a description copied from the event triggering the event |
| [statuses] | the remaining columns headers are statuses in the simulations (i.e., "FAILED" or "UNDER_REPAIR") with cell contents being the components that are in a given status at the moment of taking the snapshot. Note that the "RUNNING" status is excluded as a default status. |

For the AvailSim4 to save this sheet after finishing simulations, the user has to specify `RCA` diagnostic in the simulation input file.

### `RESULTS_COMPONENT_TREE_SIMPLE` and `RESULTS_COMPONENT_TREE_EXTENDED` output sheets

Those sheets contain two representations, one simple and one extended, of the tree. The indentation of the content indicates
the depth of the component in the tree.

To create those sheets, user has to specify `COMPONENT_TREE_SIMPLE` and/or `COMPONENT_TREE_EXTENDED` option in the simulation input file.

### `RESULTS_CONNECTIVITY_MATRIX` output sheet

The connectivity matrix is a square matrix with as many lines/columns as component in the system. Its content is represented by:

* +1 if the component on the line is the parent of the component on the column
* -1 if the component on the line is the child of the component on the column
* 0 otherwise

To create a `RESULTS_CONNECTIVITY_MATRIX` sheet, user has to specify `CONNECTIVITY_MATRIX` option in the simulation input file.

### `RESULTS_COMPONENT_LISTING` output sheet

In a similar way to `RESULTS_COMPONENT_TREE_SIMPLE` and `RESULTS_COMPONENT_TREE_EXTENDED` sheets, the `RESULTS_COMPONENT_LISTING`
sheet lists every component in the system but does not include any indentation. Without indentation, it's possible for the user
to define filter to review the type of component/failure mode present in the system.

To create a `RESULTS_COMPONENT_LISTING` sheet, user has to specify `COMPONENT_LISTING` option in the simulation input file.

### `RESULTS_CRITICAL_FAILURE_PATHS` output sheet

`RESULTS_CRITICAL_FAILURE_PATHS` contains a list of sets of components which failures lead to a critical failure of the entire
system. Components are identified by their names and unique IDs. Each row represents a single critical failure path, in which
each column either contains a component name or is empty.
By default, the root component is considered to be the root component of the system as described in the `ARCHITECTURE` sheet.
It is possible to choose a specific component by providing its name between parenthesis such as: `CRITICAL_FAILURE_PATHS(specific_component_name)`.

To create a `RESULTS_CRITICAL_FAILURE_PATHS` sheet, user has to specify `CRITICAL_FAILURE_PATHS` option in the system input file.

### Output diagram containing a representation of the system

In a similar way to `RESULTS_COMPONENT_TREE_SIMPLE`, `RESULTS_COMPONENT_TREE_EXTENDED`, `RESULTS_COMPONENT_LISTING` and
`RESULTS_CONNECTIVITY_MATRIX` sheets, the `GRAPH` options allows to print the structure of the tree in png files.
To create those graphics, `GRAPH` option has to be listed in the `DIAGNOSTICS` column of the system input file. Also it
requires the use of some packages not so straightforward to install, see the readme `Visualization tools` section.

## Priority rules of events

* `ORDER_START_INSPECTION_EVENT` = -7
* `ORDER_END_INSPECTION_EVENT` = -6
* `ORDER_JUMP_PHASE_EVENT` = -5
* `ORDER_NEXT_PHASE_EVENT_IF_SPECIFIC_FAILURE` = -4
* `ORDER_NEXT_PHASE_EVENT` = -3
* `ORDER_POSTPONE_C_EVENT` = -2
* `MRU_ORDER_REPAIR_EVENT` = -1
* `ORDER_FAILURE_EVENT` = 0
* `REEVALUATE_ORDER_ALL_FAILURE_EVENTS` = 1
* `REEVALUATE_ORDER_ALL_INSPECTION_EVENTS` = 2
* `ORDER_REPAIR_EVENT` = 3
* `ORDER_END_HOLDING_EVENT` = 4

## Cleaning rules of events

By default, an event does not modify the list of existing events. However, executing certain types of events leads to removing other events queued for execution. For example, event starting a repair of an MRU, `MinimalReplaceableUnitStartRepairingEvent`, cancels any pending repair or failure.

| type of event | b events to be cleaned | c events to be cleaned |
| --- | --- | --- |
|DetectableFailureEvent| depending on the value of `PHASE_CHANGE_TRIGGER`: next_phase_event, next_phase_if_failure_event, jump_phase_event |none|
|BlindFailureEvent| depending on the value of `PHASE_CHANGE_TRIGGER`: next_phase_event, next_phase_if_failure_event, jump_phase_event |none|
|EndHoldingEvent|none|none|
|StartInspectionEvent|DetectableFailureEvent, BlindFailureEvent, StartRepairingEvent, EndRepairingEvent, EndHoldingEvent, ?PHASES?| none|
|EndInspectionEvent|none|none|
|NextPhaseEvent|DetectableFailureEvent, BlindFailureEvent, NextPhaseEvent, NextPhaseIfFailureEvent, JumpPhaseEvent| OrderNextPhaseEvent, OrderNextPhaseIfFailureEvent|
|NextPhaseIfFailureEvent| idem than NextPhaseEvent|idem than NextPhaseEvent|
|JumpPhaseEvent|idem than NextPhaseEvent|idem than NextPhaseEvent|
|StartRepairingEvent|none|none|
|EndRepairingEvent| depending on the value of `PHASE_CHANGE_TRIGGER`: NextPhaseEvent, NextPhaseIfFailureEvent, JumpPhaseEvent | depending on the value of `PHASE_CHANGE_TRIGGER`: OrderNextPhaseEvent, OrderNextPhaseIfFailureEvent|
|MinimalReplaceableUnitStartRepairingEvent|DetectableFailureEvent, BlindFailureEvent, EndRepairingEvent, StartRepairingEvent, EndHoldingEvent| OrderRepairEvent, OrderFailureEvent, OrderEndHoldingEvent|
|MinimalReplaceableUnitEndRepairingEvent|none|none|

## Tests

In the repository, one can find many End To End (E2E) tests used in the continuous integration framework. Such E2E can
be used as a starting point to derive new inputs files (it is not advised to change the test files themselves). Alternatively,
one can also find several useful models already present in the input directory.

## Running the code

In order to use the code, download it from the git repository: <https://gitlab.cern.ch/availsim4/availsim4core>

A `README.md` is available in the root folder and specifies how to run the code in various environments.

Simulations can be performed using user's local machine or a computing cluster. The latter option is especially useful
for extensive simulations of rare-events, where large number of samples is required. In case of AvailSim4, multiple
instances of the program can be initiated and simulate the same parameters provided that the values of seed for random
number generation do not overlap in different runs. For more details, check Sensitivity Analysis and HTCondor sections
of this document.

### CERN HTCondor

At CERN, users can utilize the HTCondor cluster for running parallel jobs. This is facilitiated by a specialized HTCondor runner module of AvailSim4. In this mode, every combination of parameters defined in the sensitivity analysis file triggers a single job. Notably, one of the parameters that can be controled through the sensitivity analysis file is the initial seed value. The jobs submission is performed from an lxplus node.

The recommended AvailSim4 usage on HTCondor requires some additional steps. Jobs running on HTCondor machines are generally not welcome to access user space of the AFS, but should access only files stored in its workspace. Since generally Python packages are installed in the user space, every single job would trigger multiple accesses to the user space. The following is a step-by-step instruction:

1. `ssh user@lxplus` where `user` is the CERN user, lxplus access might have to be requested here:
<https://resources.web.cern.ch/resources/Manage/Linux/Default.aspx>
2. `git clone` the repository and then enter `cd availsim4core`
3. `source /cvmfs/sft.cern.ch/lcg/releases/LCG_102b/Python/3.9.12/x86_64-centos7-gcc11-opt/Python-env.sh` in order to
use python provided by CERN's CMVFS. This command has to be run each time you connect to lxplus (or could be configured
in the `.bashrc`)
4. `python -m venv env` and `source env/bin/active` to create and activate the virtual environment,
5. `pip install -r requirements.txt --target [target directory] --ignore-installed` from the root folder of the
repository which containing the requirements; target directory should point to a location where additional dependencies
for AvailSim4 can be stored. Recommended locations are the ones within the AFS workspace (`/afs/cern.ch/work/...`)
rather than user space, as the latter one cause problems for the HTCondor configuration.
6. `export PYTHONPATH=[target directory]` to change the default location where Python looks for dependencies for the
main script running on the node

To run a sensitivity analysis using HTCondor, use absolute paths and store input/ouput data under `/afs`:

```bash
python3.7 availsim4.py
  --system ABSOLUTE_PATH_TO_AVAILSIM4/availsim4core/test/E2E/input/convergence/convergence_test_system.xlsx
  --simulation ABSOLUTE_PATH_TO_AVAILSIM4/availsim4core/test/E2E/input/convergence/N1000_simulation.xlsx
  --output_folder ABSOLUTE_PATH_TO_AVAILSIM4/availsim4core/test/E2E/output/convergence/
  --sensitivity_analysis ABSOLUTE_PATH_TO_AVAILSIM4/availsim4core/test/E2E/input/convergence/convergence_test_sensitivityAnalysis.xlsx
  --HTCondor
  --HTCondor_extra_argument +AccountingGroup="group_u_XX.XXX"
```

The HTCondor module creates copies of input files modified according to the sensitivity analysis parameters. E.g., a sensitivity analysis file containing the following table:

| PARAMETER_NAME | VALUES | EXPLORATION_STRATEGY |
| --- | --- | --- |
| SEED | 0, 10, 20 | outer |
| FAILURE_MODE_NAME/FAILURE_MODE | 10, 15 | outer |

will yield six result directories, each containing AvailSim4 input files with a different combination of parameters (first one with seed equal 0, and failure mode equal 10, second one with seed equal 10 and failure mode set to 15, etc.). In addition, each directory contains a short bash script to run the specific job and logs. It is also possible to have "random" seeds by using constant value "-1". The random number generator will then utilize "unpredictable entropy" to generate the seed. In combination
with lists specified using Python literals a possible content of the `VALUES` cell is `[-1 for _ in range (0, 10)]` which evaluates to `[-1, -1, -1, -1, -1, -1, -1, -1, -1, -1]`, equivalent to 10 random seeds for Monte Carlo simulations.

After preparing those files, the HTCondor runner module prepares also a separate master script to run all jobs in a single job cluster. Content of the script is defined in `availsim4core/src/runner/htcondor_runner.py`. This script is used to trigger parallel jobs by submitting it to the scheduler (not the individual ones - those are only auxiliary, for the user, e.g., to restart certain jobs).

**HTCondor thresholds**
Schedulers are selecting given jobs to run accroding to priorities calculated for each job separately. Considered factors include the manually assigned priority (controlled through the argument "AccountingGroup"), but also operational aspects, such as the user defined wall time. In AvailSim4 context, this variable is equal to the value of `MAX_EXECUTION_TIME` in the simulation input file.

For background context, HTCondor jobs can be also assgined "flavors" with corresponding wall times are pre:

```python
espresso     = 20 minutes
microcentury = 1 hour
longlunch    = 2 hours
workday      = 8 hours
tomorrow     = 1 day
testmatch    = 3 days
nextweek     = 1 week
```

The shorter the wall time, the more likely the job is to start running (in practice, this means that more jobs will be running concurrently). On the other hand, when a job reaches its predefined wall time and has not stored its results - it will be terminated and all results will be irreversably lost. Therefore, it is advised to set the amount of time that will be as short as possible, yet long enough for all the jobs to finish.

Generally, there is no limit on the number of simulatnousely submitted jobs. It is up to the user, into how many pieces to split the computational task. Of course, increasing fragmentation means that combining and analysis becomes more complex. Additionally, users of the AFS need to take into account the available size of their AFS space (can be checked through a command line interface or in CERN Resources Portal, <resources.web.cern.ch>,  "List Services" > "AFS Workspaces" > "Settings"), as more jobs store more files as intermediary results or inputs.

The limit on the number of jobs running in parallel is 10,000. This is the maximum number that can be assigned by a scheduler - and there is only one scheduler assigned per user. Any job which exceeds its wall time will be removed, as well as jobs in state `HELD` after 24 hours and the ones that were restarted more than 10 times [^2].

Frequently encountered problems:

* "bigbird01.cern.ch - SECMAN:2007:Failed to end classad message.": schedulers unreachable at the moment, no action
required, users can only wait.
* "Job was held. No condor_shadow installed that supports vanilla jobs on V6.3.3 or newer resources Code 24 Subcode 0"
and jobs with the status "HELD": try releasing jobs using command `condor_release [BATCH_NAME]`, where `BATCH_NAME` can
be obtained from a table returned by the condor_q command.
* More frequently encountered problems are described in [^3].

Grafana dashboards for monitoring the clusters:

* [Users](https://batch-carbon.cern.ch/grafana/dashboard/db/user-batch-jobs)
* [Cluster](https://batch-carbon.cern.ch/grafana/dashboard/db/cluster-batch-jobs)
* [Experiments](https://monit-grafana.cern.ch/d/000000865/experiment-batch-details)
* [Schedulers](https://monit-grafana.cern.ch/d/000000868/schedds)

[^2]: Batch Docs: Service Limits, <https://batchdocs.web.cern.ch/concepts/service-limits.html>
[^3]: HTCondor Issues When Running SixTrack, A.Mereghetti, <https://indico.cern.ch/event/677302/contributions/2772978/attachments/1560422/2456272/AM_2017-11-17.pdf>

## Bibliography

## License

Copyright © CERN 2021. Released under the [GPL 3.0 only license](../../LICENSE). All rights not expressly granted are reserved.
