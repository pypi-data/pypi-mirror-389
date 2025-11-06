# AvailSim4 project description

T. Cartier-Michaud, A. Apollonio, T. Buffet
CERN, TE-MPE-PE, Geneva, Switzerland
Internal Note 2020-20
EDMS Nr: 2457825

## Abstract

This document summarizes the specifications of AvailSim4, a software
developed at CERN to predict reliability and availability of modern
particle accelerators and the related technical systems. It is based
on a Monte Carlo Discrete Event Simulation algorithm and allows for
advanced availability and reliability statistics.

## Keywords

Software specifications; Availability; Reliability; Monte Carlo

## 1. Introduction

AvailSim4 is a software used to predict the reliability and availability
of complex systems. The main use cases at CERN are accelerators
belonging to the CERN complex, as well as accelerators of collaborating
institutes or projects (e.g.
[MYRRHA](https://sckcen.be/en/Technology_future/MYRRHA) [1]). In addition,
specific machine protection studies (e.g. for the HL-LHC Inner Triplet
magnets protection ) are carried out with this tool. The computational
core of the software is a Discrete Event Simulation (DES) engine, which
simulates the failure behavior of a system over a specified period of
time. The evolution of the system follows a set of rules defined by the
programmer/user, which determines the next state of the system depending
on its current state, see
Fig.<a href="#fig:DES" data-reference-type="ref"
data-reference="fig:DES">1</a>. A simple example of the timeline of a
system is sketched in
Fig.<a href="#fig:timeLine" data-reference-type="ref"
data-reference="fig:timeLine">2</a>.

<figure id="fig:DES">
<img src="./figures/chart_DES.png" style="width:80.0%" />
<figcaption>Figure 1: Principles of Discrete Event Simulation.</figcaption>
</figure>

<figure id="fig:timeLine">
<img src="./figures/simpleTimeLine.png" style="width:60.0%" />
<figcaption>Figure 2: Example of a timeline.</figcaption>
</figure>

Evaluation of a system’s timeline can last from milliseconds to seconds
depending on the number of components inside the system and the number
of events to simulate. This computation is typically performed from
10<sup>3</sup> to 10<sup>7</sup> times inside the Monte Carlo algorithm
to generate statistics of reliability and availability. In addition, due
the possible uncertainty on some input parameters, a study generally
requires to run the Monte Carlo algorithm multiple times, from 10 to
10<sup>3</sup> times, to perform a so-called sensitivity analysis over
defined sets of parameters specifying the system’s failure behavior.
Despite handling the time in a discrete manner (which accelerates the
computation as each time step simulated modifies the state of the
system, no time step is useless), this approach is computationally
expensive as Monte Carlo algorithms converge slowly and the sensitivity
analysis is not performed analytically. Still, this is a powerful method
allowing to model complex time dependencies between components and
providing an in-depth monitoring of complex systems.

Below we report the pseudo-code for the nested loops of the algorithm:

    # sensitivity analysis
    for uniqueInput in listOfInputs:
        # Monte Carlo algorithm
        for idSimulation in range(0,numberOfSimulations):
            # Discrete Event Simulation algorithm
            while t < t_end
                # handling of events

## 2. Requirements

### 2.1 Lifetime of the software

The software is developed to model the next generation of particle
accelerators (HL-LHC, FCC, CLIC). It is expected to continue developing
the models in the future, which means that the expected lifetime of the
software is about 15 years (and eventually more). This requires to use
high coding standards with respect to documentation and tests, as well
as to choose a programming language that will still be supported in the
future. Python3 has been chosen as it is widely used in many scientific
communities, in particular in the artificial intelligence / big data
domain.

### 2.2 Documentation

AvailSim4 is considered as an “expert tool” which needs a detailed
documentation. Automatic documentation (extraction of comments from the
source code) and graphic description of the code (class / object /
function) should be provided using
[sphinx](http://www.sphinx-doc.org/en/master/) and
[PyCallGraph](http://pycallgraph.slowchop.com/en/master/). No wiki or
collaborative sharing tool is foreseen at the moment.

### 2.3 Tests

A Continuous Integration (CI) framework of the Git repository will be
used to automatically test the code using unitary tests and End to End
(E2E) tests. A list of tests is provided in
[Sec. 5](#5-tests).

### 2.4 Developers

The main developers are likely to be 1 or 2 persons (technical students
and/or fellows) with a commitment of about 0.5 FTE in total. A close
collaboration between the MPE-PE and MPE-MS sections is in place for
development and support.

### 2.5 Users

The main users are and will be at CERN, including its collaborating
institutes (e.g. [MYRRHA](https://sckcen.be/en/Technology_future/MYRRHA)
). A team of 2 or 3 persons (including the developers) is foreseen to
use the software. The interface has to be as simple as possible for
programmers to quickly develop new models and for user to easily adapt
existing models. No Graphical User Interface is foreseen at the moment,
although for the visualization of results discussions are ongoing to use
the AFT framework (see
Fig.<a href="#fig:cardio" data-reference-type="ref"
data-reference="fig:cardio">3</a>). This strategy might be revised if
there will be interest in the community to have access to AvailSim4.

<figure id="fig:cardio">
<img src="./figures/cardio.png" />
<figcaption>Figure 3: Cardiogram view of AFT <span class="citation"
data-cites="AFT"></span>. Top part represents the beam metric, middle
part represents the chronology of phases, bottom part represents the
list of faults.</figcaption>
</figure>

### 2.6 Performance requirements

As the software is developed based on a Monte Carlo engine, the
computational resources needed for a study depend on the size of the
system and the input parameters, which determine the number of events to
be generated.

-   The RAM requirement is likely to be small, considering the current
    trend of having more than 1GB of memory per core for standard
    computers. As an example, the footprint of a python process
    simulating a small system based on 818 components is about 60 MB
    while for a large system based on 40 802 components the footprint is
    about 85 MB. The memory footprint could significantly increase due
    to some new features allowing to plot time lines and new statistical
    measurement but it should not become a problem.

-   The disk space required is likely to be small as well. As an
    example, the complete Inner Triplet study required less than 1 GB.
    Results are stored in csv files, which are easily readable.
    Developing new diagnostics might increase the storage footprint but
    it is not seen as an issue.

-   The main bottleneck is the execution speed of the simulations. For
    the studies performed until now, the execution time is somehow
    linear with respect to the number of events to simulate. Thus, it
    linearly increases with the number of components to simulate (more
    components with the same failure rate results in more failures to
    simulate and more iterations for the algorithm), with the failure
    rates of components (more failures equals more iterations for the
    algorithm) or with the period of time simulated (longer period
    equals more failures to simulate and more iterations for the
    algorithm). Depending on the execution time of a simulation, the
    number of simulations required by the convergence of the Monte Carlo
    algorithm and the number of calls to the Monte Carlo algorithm with
    respect to the range of the sensitivity analysis, the computational
    needs of a study could be met by a simple desktop machine or could
    require the use of CERN’s clusters. An interface with HTCondor[*](#footnotes)
    has already been developed and it has successfully used 50 000
    core.hours in Q4-2019 to study the Inner Triplet Magnet protection [2].
    For this particular study, a unique simulation could last from a few
    minutes up to 240 hours. Because of the large possible needs in
    computing, the performance is always kept as a main priority when
    developing new features. The use of [pypy](https://pypy.org/),
    [pythran](https://pythran.readthedocs.io/en/latest/) or
    [cython](https://cython.org/) is kept as an option to speed up the
    execution on a unique core. Parallelization over multiple cores is
    for now performed by "embarrassingly" distributing the computation
    of groups of timelines to different jobs. The scaling is then of
    100%.

### 2.7 Benchmarks

<table>
<caption>Table 1: * AS4H is the first draft of AvailSim4 with an "hardcoded"
approach.</caption>
<thead>
<tr class="header">
<th style="text-align: left;">model</th>
<th style="text-align: center;">LINAC4 simplified</th>
<th style="text-align: center;">LHC simplified</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">number of components</td>
<td style="text-align: center;">12</td>
<td style="text-align: center;">30</td>
</tr>
<tr class="even">
<td style="text-align: left;">number of failure modes</td>
<td style="text-align: center;">12</td>
<td style="text-align: center;">45</td>
</tr>
<tr class="odd">
<td style="text-align: left;">number of phases</td>
<td style="text-align: center;">1</td>
<td style="text-align: center;">4</td>
</tr>
<tr class="even">
<td style="text-align: left;">number of simulations</td>
<td style="text-align: center;">1000</td>
<td style="text-align: center;">1000</td>
</tr>
<tr class="odd">
<td style="text-align: left;">mean number of iterations per simulation
(AVS4)</td>
<td style="text-align: center;">400</td>
<td style="text-align: center;">2100</td>
</tr>
<tr class="even">
<td style="text-align: left;">computation time ELMAS (compiled &amp;
commercial <span class="citation" data-cites="ELMAS"></span>)</td>
<td style="text-align: center;">0.1 s</td>
<td style="text-align: center;">-</td>
</tr>
<tr class="odd">
<td style="text-align: left;">computation time AS3 old</td>
<td style="text-align: center;">900 s</td>
<td style="text-align: center;">-</td>
</tr>
<tr class="even">
<td style="text-align: left;">computation time and RAM AS3 current</td>
<td style="text-align: center;">240 s / 290 MB</td>
<td style="text-align: center;">870 s / 4.8 GB</td>
</tr>
<tr class="odd">
<td style="text-align: left;">computation time and RAM AS4H*</td>
<td style="text-align: center;">2.4 s / 60 MB</td>
<td style="text-align: center;">-</td>
</tr>
<tr class="even">
<td style="text-align: left;">computation time and RAM AS4</td>
<td style="text-align: center;">55 s / 80 MB</td>
<td style="text-align: center;">-</td>
</tr>
</tbody>
</table>

\* AS4H is the first draft of AvailSim4 with an "hardcoded" approach.

The number of temporal iterations (innermost loop of the algorithm
described end of
[Sec. 1](#1-introduction) and measured with AvailSim4)
which is necessary to perform a simulation has proven to be
representative of the computation time for the Inner Triplet study [2]. It
allows to take into account some information from the probability of
failure of each component and their time to repair as increasing the
probability of failing increases the number of repairs, thus the number
of iterations and the computation time.

The **LINAC4 simplified** model has been used in the past [3] and could be
an indicative benchmark. As described in
[Sec. 6](#6-list-of-studies), this model is based on 12 components
having one failure mode each. The execution time of an AvailSim3 version
of May 2018 (dismissed) is 3.75 slower compared to the actual version of
AvailSim3 on a current machine (i5-6500) with a peak RAM footprint at
290MB. Compared to the current version of AvailSim3, AvailSim4H (first
draft, hardcoded version) is 100 times faster and the peak RAM footprint
is 60MB. In each of those 4 runs, the results are consistent,
considering the Monte Carlo nature of the simulation and the acceptable
simulation error. The factor 100 in speed observed between AvailSim3 and
the initial hardcoded AvailSim4 is due to the much simpler structure of
AvailSim4H, which is close to a tailored scripting for each model
allowing to code only required features, whereas AvailSim3 always uses
complex mechanisms allowing to describe complex models. The reduced RAM
footprint (a python terminal taking about 50MB) is driven by the results
of the 1000 simulations which are not accumulated in RAM to compute the
statistics but statistics are computed by iteration.

**LHC simplified** model, using the phases feature, should be one of the
main benchmarks to evaluate AvailSim4. As described in
[Sec. 6](#6-list-of-studies), this model is based on 30 components
associated to 45 failure modes and 4 phases. The current version of
AvailSim3 requires around 870s for 1000 simulations and peaks at 4.8GB
of RAM footprint. See
[Sec. 6](#6-list-of-studies) for the description of more systems.

### 2.8 Distribution

AvailSim4 being written in python3, the potential distribution outside
CERN is under discussion with the CERN Knowledge Transfer Group and will
be finalized once the user community is better identified. AvailSim4
successfully runs on different OSs (tested on windows 10 and different
Unix/Linux). Compatibility with SWAN (notebooks at CERN) should be kept,
but no issue was raised until now.

## 3. Inputs

Inputs of AvailSim4 are supposed to provide the necessary information to
describe any system reliability/availability model (see
<a href="#sec:system" data-reference-type="ref"
data-reference="sec:system">3.1</a>) and to define the parameters needed
by the Monte Carlo algorithm (see
<a href="#sec:algo" data-reference-type="ref"
data-reference="sec:algo">3.2</a>). Those parameters are a collection of
X? tables, out of which Y? tables are optional (containing advanced
features) and Z? are necessary for regular systems (containing basic
information). During AvailSim4 development, the focus is on basic
parameters, keeping advanced features for dedicated developments.
Parameters or entire tables with \* are optional but they are
represented in this document to give an idea of possible future
features. *P**K* stands for *Primary Key* and must be unique for each
record in the table. *F**K* stands for *Foreign Key* and represents the
*Primary Key* of another table or the same table. It is worth to mention
that users could have difficulties to fill in those tables which could
lead to sometimes dangerous silent bugs. For this reason, it is better
to have an input which is slightly redundant, decreasing the probability
of having a silent bug. Finally, AvailSim4 is mainly used for
sensitivity analyses, such study can also be parametrized and run
automatically (see <a href="#sec:sensitivity" data-reference-type="ref"
data-reference="sec:sensitivity">3.3</a>).

### 3.1 Description of a system

A **system** is made of a hierarchy of "basic components" (see
Tab.<a href="#tab:system" data-reference-type="ref"
data-reference="tab:system">2</a>). "Compound components" are defined to
group basic and/or (nested) compound components for convenience as it
might ease the initialization of the system or accelerate the
computation during the simulation and even help better partition for the
statistical analysis. While a basic component can fail according to
failure modes, a compound component would fail according to its basic
components and the logic that describes their relation. See
Fig.<a href="#fig:systemDescription" data-reference-type="ref"
data-reference="fig:systemDescription">4</a> for the sketch of a system.

<figure id="fig:systemDescription">
<img src="./figures/systemDescription.png" style="width:80.0%" />
<figcaption>Figure 4: Sketch of a system based of 4 basic components. C1 and C2
are grouped under the compound component C. fm* are different failure
modes assigned to the components.</figcaption>
</figure>

<table>
<caption>Table 2: Fields describing a system architecture by listing its
components and relations.</caption>
<thead>
<tr class="header">
<th colspan="3" style="text-align: left;">system architecture</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">PK</td>
<td style="text-align: left;">componentName</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">componentType</td>
<td style="text-align: left;">basic,compound</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">componentNumber</td>
<td style="text-align: left;">integer</td>
</tr>
<tr class="even">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">childrenName(lowestCommonParentName)</td>
<td style="text-align: left;">list(text)</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">childrenLogic</td>
<td style="text-align: left;">and, XooY, custom function</td>
</tr>
<tr class="even">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">inMRU</td>
<td style="text-align: left;">list(text)</td>
</tr>
<tr class="odd">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">triggerMRU</td>
<td style="text-align: left;">list(text)</td>
</tr>
<tr class="even">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">* location (from Tab.<a
href="#tab:locations" data-reference-type="ref"
data-reference="tab:locations">11</a>)</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="odd">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">* impacted system (from Tab.<a
href="#tab:restartTimes" data-reference-type="ref"
data-reference="tab:restartTimes">12</a>)</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">* device type (from Tab.<a
href="#tab:spares" data-reference-type="ref"
data-reference="tab:spares">13</a>)</td>
<td style="text-align: left;">text</td>
</tr>
</tbody>
</table>

Fields describing a system architecture by listing its components and
relations.

Here are the meaning and constraints on the preceding parameters:

-   *componentType* explicitly define if a component is composed of sub
    components (compound) or if it is the lowest node of a branch
    (basic). Only basic components can fail according to failure modes,
    compound components fail according to their children.

-   The parameter *childrenName* is a list of strings defining the
    children of a given component. If a child is shared by different
    parents, its name should be written as
    childName(lowestCommonParentName). This feature is detailed
    [Sec. 7.1.4](#714-sharedchild-feature). If the component is a
    basic, the cell is field with "none".

-   *childrenLogic* specifies which logical function to use in order to
    define if a compound is running. A table defining the possible
    transitions between statuses according to the logic is defined
    Tab.<a href="#tab:XooYlogicStatus" data-reference-type="ref"
    data-reference="tab:XooYlogicStatus">21</a> and
    Tab.<a href="#tab:ANDlogicStatus" data-reference-type="ref"
    data-reference="tab:ANDlogicStatus">20</a> in the section
    [Sec. 7.1.1](#711-status-handling-feature).

-   *inMRU* for "in Minimal Replaceable Unit" defines if a given
    component is included in an MRU, see
    [Sec. 7.1.5](#715-minimal-replaceable-unit) for details.

-   *triggerMRU* for "trigger Minimal Replaceable Unit replacement"
    defines if a given component can trigger the repair/replacement of a
    given MRU, see [Sec. 7.1.5](#715-minimal-replaceable-unit) for details.

-   The parameter *\* location* is linked to the table location
    Tab.<a href="#tab:locations" data-reference-type="ref"
    data-reference="tab:locations">11</a> and defines where the
    component is located. Indeed, to repair a component, technicians
    might have to physically reach it (e.g. if it’s in the LHC tunnel or
    in accessible area with beam), which defines an access time. This
    access time is then taken into account to compute the total duration
    of a failure.

-   When a component fails, it might shutdown a parent system which
    needs to be restarted after repair, like the compound component ROOT
    in Fig.<a href="#fig:systemDescription" data-reference-type="ref"
    data-reference="fig:systemDescription">4</a>. The variable *\*
    impacted system* links to such information, providing a restart time
    duration.

-   *\* device type* allows to link any component to a type of device
    and thus to the amount of spares for such component. This detail can
    be useful as the production rate of spares, the maximum storage
    capacity or the location of storage are parameters which can limit
    the performance of a machine.

**Minimal replaceable units** are a way to define group of components
which are repaired / replaced all together. Often some units are
replaced instead of repaired on site in order to lower risk (radiation)
and/or maximize availability. See
[Sec. 7.1.5](#715-minimal-replaceable-unit) for more details.

<table>
<caption>Table 3: Fields describing a Minimal Replaceable Unit.</caption>
<thead>
<tr class="header">
<th colspan="3" style="text-align: left;">system architecture</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">PK</td>
<td style="text-align: left;">MRUNname</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">repairLaw</td>
<td style="text-align: left;">exponential, Weibull, custom function</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">repairParameters</td>
<td style="text-align: left;">list(float)</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">* repairSchedule</td>
<td style="text-align: left;">immediate,shadow,custom</td>
</tr>
<tr class="odd">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">lowestScopeCommonAncestor</td>
<td style="text-align: left;">test</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">triggeringStatus</td>
<td style="text-align: left;">Status</td>
</tr>
</tbody>
</table>

Fields describing a Minimal Replaceable Unit.

-   *MRUName* is the name referring to an MRU.

-   *repairLaw* defines the type of probability distribution function
    used to generate the time to fail. The deterministic/fix failure law
    is simply a constant function returning a unique value.

-   *failureParameters* is used to feed the probability law define
    above.

-   *\* repairSchedule* defines when a replacement can take place.

-   *\* lowestScopeCommonAncestor* is used to define a top boundary of
    the subset of components within a specific minimal replaceable,
    similarly to "share child" feature
    [Sec. 7.1.4](#714-sharedchild-feature).

-   *triggeringStatus* defines the status of the triggering component
    (component with name of the current MRU in its triggerMRU list of
    MRU) triggering the minimal replaceable unit.

**Failure modes** are possible ways for a basic component to fail. For
example an active electronic component could fail due to high
temperature, vibrations, too high voltage/current, etc. A failure mode
is described by
Tab.<a href="#tab:failureModes" data-reference-type="ref"
data-reference="tab:failureModes">4</a>. Several failure modes are
attached to components in
Fig.<a href="#fig:systemDescription" data-reference-type="ref"
data-reference="fig:systemDescription">4</a>.

<table>
<caption>Table 4: Fields describing a failure mode.</caption>
<thead>
<tr class="header">
<th colspan="3" style="text-align: left;">failure modes</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">PK</td>
<td style="text-align: left;">failureModeName</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">failureLaw</td>
<td style="text-align: left;">exponential, Weibull, custom function,
...</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">failureParameters</td>
<td style="text-align: left;">list(float)</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">* references for the TTF distribution</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">repairLaw</td>
<td style="text-align: left;">exponential, Weibull, custom function</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">repairParameters</td>
<td style="text-align: left;">list(float)</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">* references for the TTR distribution</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">typeOfFailure</td>
<td style="text-align: left;">blind, detectable</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">* repairSchedule</td>
<td style="text-align: left;">immediate,shadow,custom</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">inspectionFrequency</td>
<td style="text-align: left;">float</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">inspectionDuration</td>
<td style="text-align: left;">float</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">* on-off site maintenance</td>
<td style="text-align: left;">on, off</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">* standby state</td>
<td style="text-align: left;">cold, hot</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">* simultaneous repairs</td>
<td style="text-align: left;">True, False</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">* repairs parallel to specific phases</td>
<td style="text-align: left;">list(text)</td>
</tr>
<tr class="even">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">* parameter affected by the failure (from
Tab.<a href="#tab:parameters" data-reference-type="ref"
data-reference="tab:parameters">10</a>)</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">* affect type</td>
<td style="text-align: left;">add, subtract, custom function</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">* parameters of the affect</td>
<td style="text-align: left;">list(float)</td>
</tr>
<tr class="odd">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">* manpower type of repair (from Tab.<a
href="#tab:manPower" data-reference-type="ref"
data-reference="tab:manPower">14</a>)</td>
<td style="text-align: left;">list(text)</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">* manpower quantity</td>
<td style="text-align: left;">list(float)</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">* repair strategy</td>
<td style="text-align: left;">repairable, swappable</td>
</tr>
</tbody>
</table>

Fields describing a failure mode.

-   *failureLaw* defines the type of probability distribution function
    used to generate the time to fail. The deterministic/fix failure law
    is simply a constant function returning a unique value.

-   *failureParameters* is used to feed the probability law define
    above.

-   and are the repair version of the and .

-   *typeOfFailure* defines if a failure is immediately detectable or if
    it is blind. According to the additional parameter *\*
    repairSchedule*, it is possible to define when a failure can be
    repaired. Tab.<a href="#tab:repairAction" data-reference-type="ref"
    data-reference="tab:repairAction">5</a> specifies the possible
    combinations.

-   If specified, the parameters *inspectionFrequency* and
    *inspectionDuration* define the periodicity and duration of
    inspections able to detect any blind failure / reset aging effect.

-   The parameter *\* on-off site maintenance* defines if a component
    experiencing a particular failure mode can be repaired remotely,
    thus not adding the access time to its repair time.

-   In case the system is down due to some failure of a component, some
    other components might still have to run as shutting them down is
    too slow or complex, thus those components might still fail while
    the overall system is not running. This is defined by *\* standby
    state*: cold, meaning that the given component cannot fail during
    downtime, while hot means that the given component is still running
    and thus could fail. \[Current version of the code is standby hot by
    default\]

-   Sometimes several components could be repaired simultaneously (in
    parallel) as the access of both components at the same time by
    enough workers is possible and thus reducing the downtime with
    respect to a sequential repair approach. *\* simultaneous repairs*
    defines this attribute. \[Current version of the code does
    simultaneous repair by default\]

-   *\* repairs parallel to specific phases* allows to define a list of
    phases in which a component could be repaired. For example, if a
    fault occurs in LHC at stable beam, the repair can start in parallel
    to ramp down.

-   The group of parameters *\* parameter affected by the failure*, *\*
    affect type* and *\* parameters of the affect* are used to define
    variables accounting for performance (luminosity, power of a
    converter, intensity of a beam, etc) which could then impact the
    state of the system (operation in degraded mode, etc) through using
    Tab.<a href="#tab:consequences" data-reference-type="ref"
    data-reference="tab:consequences">9</a>. This generic way to define
    variables and their evolution should be design to back propagate
    some information to failures modes, for example increasing the
    probability of failure with increasing load on a component.

-   In case cost and manpower resources need to be simulated, it is
    possible to quantify the price and number of persons required using
    *\* manpower type of repair* and *\* manpower quantity*.

-   In the same manner manpower resources are tracked, the stock of
    spare parts can be monitored for component which are swappable and
    not repairable, using the parameter *\* repair strategy*.

<table>
<caption>Table 5: Description of the different repair schedule strategies for
detectable faults.</caption>
<thead>
<tr class="header">
<th style="text-align: left;">repairSchedule - typeOfFailure</th>
<th style="text-align: left;">action</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">immediate - detectable</td>
<td style="text-align: left;">immediate repair</td>
</tr>
<tr class="even">
<td style="text-align: left;">immediate - blind</td>
<td style="text-align: left;">impossible combination</td>
</tr>
<tr class="odd">
<td style="text-align: left;">shadow - detectable</td>
<td style="text-align: left;">repair in the shadow of a longer failure
of another system</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">(unless it becomes critical before)</td>
</tr>
<tr class="odd">
<td style="text-align: left;">shadow - blind</td>
<td style="text-align: left;">once detected, repair in the shadow</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">(unless it becomes critical before)</td>
</tr>
<tr class="odd">
<td style="text-align: left;">custom</td>
<td style="text-align: left;">custom condition to trigger a repair</td>
</tr>
</tbody>
</table>

Description of the different repair schedule strategies for detectable
faults.

The **failure mode assignment** is described in
Tab.<a href="#tab:failureModeAssignments" data-reference-type="ref"
data-reference="tab:failureModeAssignments">6</a>. A unique component
could have several failure modes and those failure modes could change
along the simulations, mainly according to the phase in which the system
is, see Tab.<a href="#tab:phases" data-reference-type="ref"
data-reference="tab:phases">7</a> and
Tab.<a href="#tab:phaseTransitions" data-reference-type="ref"
data-reference="tab:phaseTransitions">8</a>. This table could be
directly incorporated in
Tab.<a href="#tab:system" data-reference-type="ref"
data-reference="tab:system">2</a>.

<table>
<caption>Table 6: Fields describing the assignments of a failure mode.</caption>
<thead>
<tr class="header">
<th colspan="3" style="text-align: left;">failure mode assignments</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">componentName (from Tab.<a
href="#tab:system" data-reference-type="ref"
data-reference="tab:system">2</a>)</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">failureModeName (from Tab.<a
href="#tab:failureModes" data-reference-type="ref"
data-reference="tab:failureModes">4</a>)</td>
<td style="text-align: left;">list(text)</td>
</tr>
<tr class="odd">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">* phaseName (from Tab.<a
href="#tab:phases" data-reference-type="ref"
data-reference="tab:phases">7</a>)</td>
<td style="text-align: left;">list(text)</td>
</tr>
</tbody>
</table>

Fields describing the assignments of a failure mode.

The list of **\* phases** and their properties is described in
Tab.<a href="#tab:phases" data-reference-type="ref"
data-reference="tab:phases">7</a>. If a system does not use phases to
operate, still a top phase is defined, its duration is the duration of
the simulation. Phases could be used to describe the cycles of a given
machine, but could include the technical stops and long shutdowns as
well. It is foreseen to have any number of layers to possibly describe
complex accelerator schedules (e.g. including low-intensity and
high-intensity operation, machine developments, etc.), see
Fig.<a href="#fig:phases" data-reference-type="ref"
data-reference="fig:phases">5</a>.

<table>
<caption>Table 7: Fields describing a phase.</caption>
<thead>
<tr class="header">
<th colspan="3" style="text-align: left;">* phases</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">PK</td>
<td style="text-align: left;">phase’s name</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">description of the phase</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">duration distribution function</td>
<td style="text-align: left;">exponential, Weibull, normal, custom
function</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">parameters of the distribution</td>
<td style="text-align: left;">list(float)</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">references for the distribution</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">phase’s type</td>
<td style="text-align: left;">operation, maintenance, cycle, cycle
start</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">parent phase</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">next default phase</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">** next phase in case of failure</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">* parallel to downtime</td>
<td style="text-align: left;">True, False</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">* custom metric</td>
<td style="text-align: left;">custom function</td>
</tr>
</tbody>
</table>

Fields describing a phase.

-   The duration of a phase can follow probability rules, it can be
    interrupted by a failure or by an external criterion optimising the
    luminosity of the HL-LHC project for example.

-   The *phase’s type* defines if a phase belongs to operation (thus
    downtime decreases the availability) or maintenance (where no
    physics is produced, so no downtime is measured). Also a phase can
    be part of a cycle which starts with "cycle start". Phases in cycles
    are repeated until the parent phase ends.

-   The *custom metric* is an optional function evaluated at the end of
    a phase. It is provided in a string or a \*.py file. A typical use
    would be to compute the luminosity at the end of each stable phase.

<figure id="fig:phases">
<img src="./figures/phases.png" />
<figcaption>Figure 5: Top layer: sketch of a typical accelerator operational
schedule, including "Operation" and "Maintenance" (or Technical Stop)
periods. Middle layer: phases of the machine, Ramp Up, Stable Beam, Ramp
Down. When faults occur, the the cycle go back to Ramp Up. Bottom layer:
Luminosity takes place in Stable Beam, Availability is not of interest
during Maintenance or Technical Stops.</figcaption>
</figure>

A table **\* phase transitions**
(Tab.<a href="#tab:phaseTransitions" data-reference-type="ref"
data-reference="tab:phaseTransitions">8</a>) could be used together with
tables \* consequences
(Tab.<a href="#tab:consequences" data-reference-type="ref"
data-reference="tab:consequences">9</a>) and parameters
(Tab.<a href="#tab:parameters" data-reference-type="ref"
data-reference="tab:parameters">10</a>) to increase the different
possible behaviors of the *\*\* next phase in case of failure* present
in Tab.<a href="#tab:phases" data-reference-type="ref"
data-reference="tab:phases">7</a>.

<table>
<caption>Table 8: Fields describing the transition between phases in case of
fault.</caption>
<thead>
<tr class="header">
<th colspan="3" style="text-align: left;">* phase transitions</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">phase’s name (from Tab.<a
href="#tab:phases" data-reference-type="ref"
data-reference="tab:phases">7</a>)</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">consequence (from Tab.<a
href="#tab:consequences" data-reference-type="ref"
data-reference="tab:consequences">9</a>)</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="odd">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">next phase’s name (from Tab.<a
href="#tab:phases" data-reference-type="ref"
data-reference="tab:phases">7</a>)</td>
<td style="text-align: left;">text</td>
</tr>
</tbody>
</table>

Fields describing the transition between phases in case of fault.

The **\* consequences** are described
Tab.<a href="#tab:consequences" data-reference-type="ref"
data-reference="tab:consequences">9</a>. Consequences are raised by
parameters (see Tab.<a href="#tab:parameters" data-reference-type="ref"
data-reference="tab:parameters">10</a>), themselves relying on failure
modes (see Tab.<a href="#tab:failureModes" data-reference-type="ref"
data-reference="tab:failureModes">4</a>). A chain of consequences can
occur, allowing for very complex behavior. This table should not be used
in the first implementation of AvailSim4.

<table>
<caption>Table 9: Fields describing possible consequences triggered by parameters
(see Tab.<a href="#tab:parameters" data-reference-type="ref"
data-reference="tab:parameters">10</a>).</caption>
<thead>
<tr class="header">
<th colspan="3" style="text-align: left;">* consequences</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">PK</td>
<td style="text-align: left;">consequence’s name</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">overhead time distribution</td>
<td style="text-align: left;">exponential, Weibull, custom function</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">parameters of the distribution</td>
<td style="text-align: left;">list(float)</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">references for the distribution</td>
<td style="text-align: left;">text</td>
</tr>
</tbody>
</table>

Fields describing possible consequences triggered by parameters (see
Tab.<a href="#tab:parameters" data-reference-type="ref"
data-reference="tab:parameters">10</a>).

**\* Parameters** are internal variables used to describe quantities
related to the system on top of the status of each component. They are
modified according to the failure modes (see
Tab.<a href="#tab:failureModes" data-reference-type="ref"
data-reference="tab:failureModes">4</a>) and can trigger consequences
(see Tab.<a href="#tab:consequences" data-reference-type="ref"
data-reference="tab:consequences">9</a>). In a first approach, those
variables will only be used to compute interesting metrics, such as
integrated luminosity.

<table>
<caption>Table 10: Fields describing the logic of a parameter use in Tab.<a
href="#tab:failureModes" data-reference-type="ref"
data-reference="tab:failureModes">4</a>).</caption>
<thead>
<tr class="header">
<th colspan="3" style="text-align: left;">* parameters</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">PK</td>
<td style="text-align: left;">parameter’s name</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">nominal value</td>
<td style="text-align: left;">float</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">maximum value</td>
<td style="text-align: left;">float</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">minimum value</td>
<td style="text-align: left;">float</td>
</tr>
<tr class="odd">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">parameter affected <span
class="math inline">#1</span></td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">affect type <span
class="math inline">#1</span></td>
<td style="text-align: left;">add, subtract, custom function</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">parameters of the affect <span
class="math inline">#1</span></td>
<td style="text-align: left;">list(float)</td>
</tr>
<tr class="even">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">parameter affected <span
class="math inline">#<em>N</em></span></td>
<td style="text-align: left;">text</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">affect type <span
class="math inline">#<em>N</em></span></td>
<td style="text-align: left;">add, subtract, custom function</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">parameters of the affect <span
class="math inline">#<em>N</em></span></td>
<td style="text-align: left;">list(float)</td>
</tr>
<tr class="odd">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">consequence (from Tab.<a
href="#tab:consequences" data-reference-type="ref"
data-reference="tab:consequences">9</a>)</td>
<td style="text-align: left;">text</td>
</tr>
</tbody>
</table>

Fields describing the logic of a parameter use in
Tab.<a href="#tab:failureModes" data-reference-type="ref"
data-reference="tab:failureModes">4</a>).

The **\* location** of a component matters as it defines the access time
in case of repair, see
Tab.<a href="#tab:locations" data-reference-type="ref"
data-reference="tab:locations">11</a>. This table could be merged with
the table system (Tab.<a href="#tab:system" data-reference-type="ref"
data-reference="tab:system">2</a>) or the table failure modes
(Tab.<a href="#tab:failureModes" data-reference-type="ref"
data-reference="tab:failureModes">4</a>). For now the access time is
taken into account by adjusting the repair time reported in the failure
modes table.

<table>
<caption>Table 11: Fields describing a location.</caption>
<thead>
<tr class="header">
<th colspan="3" style="text-align: left;">* locations</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">PK</td>
<td style="text-align: left;">location’s name</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">access time distribution</td>
<td style="text-align: left;">exponential, Weibull, custom function</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">parameters of the distribution</td>
<td style="text-align: left;">list(float)</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">references for the distribution</td>
<td style="text-align: left;">text</td>
</tr>
</tbody>
</table>

Fields describing a location.

In case a repair is needed, not only the access time and the repair time
play roles but also the **\* restart time** of the system in which the
failure occurred. This duration is defined by
Tab.<a href="#tab:restartTimes" data-reference-type="ref"
data-reference="tab:restartTimes">12</a>. This table could be merged
with the table system
(Tab.<a href="#tab:system" data-reference-type="ref"
data-reference="tab:system">2</a>) or the table failure modes
(Tab.<a href="#tab:failureModes" data-reference-type="ref"
data-reference="tab:failureModes">4</a>). For now the access time is
taken into account by adjusting the repair time reported in the failure
modes table.

<table>
<caption>Table 12: Fields describing the restart time of a (sub)system.</caption>
<thead>
<tr class="header">
<th colspan="3" style="text-align: left;">* restart times</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">PK</td>
<td style="text-align: left;">system’s name</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">restart time distribution</td>
<td style="text-align: left;">exponential, Weibull, custom function</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">parameters of the distribution</td>
<td style="text-align: left;">list(float)</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">references for the distribution</td>
<td style="text-align: left;">text</td>
</tr>
</tbody>
</table>

Fields describing the restart time of a (sub)system.

Some repairs might require **\* spares**. Their properties are listed in
Tab.<a href="#tab:spares" data-reference-type="ref"
data-reference="tab:spares">13</a>.

<table>
<caption>Table 13: Fields describing the available spares.</caption>
<thead>
<tr class="header">
<th colspan="3" style="text-align: left;">* spares</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">PK</td>
<td style="text-align: left;">device type</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">location (from Tab.<a
href="#tab:locations" data-reference-type="ref"
data-reference="tab:locations">11</a>)</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">number available</td>
<td style="text-align: left;">integer</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">start up probability in percents</td>
<td style="text-align: left;">float</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">cost in CHF</td>
<td style="text-align: left;">float</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">swap time</td>
<td style="text-align: left;">float</td>
</tr>
</tbody>
</table>

Fields describing the available spares.

Repairs require **\* manpower**. The available workers are list in
Tab.<a href="#tab:manPower" data-reference-type="ref"
data-reference="tab:manPower">14</a>. The description is quite similar
to the spares (see Tab.<a href="#tab:spares" data-reference-type="ref"
data-reference="tab:spares">13</a>).

<table>
<caption>Table 14: Fields describing the available man power.</caption>
<thead>
<tr class="header">
<th colspan="3" style="text-align: left;">* man power</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">PK</td>
<td style="text-align: left;">man power type</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="even">
<td style="text-align: left;">FK</td>
<td style="text-align: left;">location (from Tab.<a
href="#tab:locations" data-reference-type="ref"
data-reference="tab:locations">11</a>)</td>
<td style="text-align: left;">text</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">number available</td>
<td style="text-align: left;">integer</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">cost in CHF</td>
<td style="text-align: left;">float</td>
</tr>
</tbody>
</table>

Fields describing the available man power.

### 3.2 Parameters of the algorithm

While most of the tables provided for the inputs are used to describe
the simulated system, one additional table lists the parameters of the
simulations itself, see
Tab.<a href="#tab:simulation" data-reference-type="ref"
data-reference="tab:simulation">15</a>. A margin parameter *m* is given
to evaluate the desired results precision and the number of required
simulations *N*<sub>*R*</sub>. Let *p* ∈ \[0,1\] be the target
probability we want to simulate, the definition of *N*<sub>*r*</sub> in
the current version of the code is
*N*<sub>*r*</sub> = 10<sup>*m* − log<sub>10</sub>(*p*)</sup> with a
default value of *m* = 2. That is to say we use
*N*<sub>*r*</sub> = 10000 simulations if the probability *p* we want to
estimate is *p* = 0.01. According to the order 0.5 convergence of the
Monte Carlo algorithm [5], such criterion should be
*N*<sub>*r*</sub> = 10<sup>−2log<sub>10</sub>(*p*)</sup> which still
gives *N*<sub>*r*</sub> = 10000 for *p* = 0.01 but increase rapidly when
*p* decreases. Using the margin parameter *m* helps to keep
*N*<sub>*r*</sub> smaller while still providing a good approximation of
the order of *p*.

<table>
<caption>Table 15: Parameters of a Monte Carlo simulation.</caption>
<thead>
<tr class="header">
<th colspan="3" style="text-align: left;">simulation</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">simulationType</td>
<td style="text-align: left;">MonteCarlo, *QuickParse</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td
style="text-align: left;">minimumNumberOfSimulationsWithinTheMonteCarloLoop</td>
<td style="text-align: left;">integer</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td
style="text-align: left;">maximumNumberOfSimulationsWithinTheMonteCarloLoop</td>
<td style="text-align: left;">integer</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">*
marginParameterDefiningAnAppropriateNumberOfSimulations</td>
<td style="text-align: left;">integer</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">* maximumExecutionTime</td>
<td style="text-align: left;">integer</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">initialSeed</td>
<td style="text-align: left;">integer</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">* listOfDiagnosis</td>
<td style="text-align: left;">list(text)</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">durationOfSimulation</td>
<td style="text-align: left;">float</td>
</tr>
</tbody>
</table>

Parameters of a Monte Carlo simulation.

### 3.3 Sensitivity analysis

Each parameter could be expressed as a list, describing the exploration
range of values to perform a sensitivity analysis. With inputs formatted
according to the Common Input Format, many arguments are list
themselves. In order for the user to better understand what is part of
the sensitivity analysis, the lists of values to take into account for
the sensitivity analysis could be provided in a dedicated table
Tab.<a href="#tab:sensitivityAnalysis" data-reference-type="ref"
data-reference="tab:sensitivityAnalysis">16</a>.

<table>
<caption>Table 16: Parameters of a Sensitivity analysis.</caption>
<thead>
<tr class="header">
<th colspan="3" style="text-align: left;">sensitivity analysis</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">parametersName</td>
<td style="text-align: left;">values</td>
<td style="text-align: left;">explorationStrategy</td>
</tr>
<tr class="even">
<td style="text-align: left;">failure mode / klystron / parameters of
the MTTF distribution</td>
<td style="text-align: left;">[200,400,800,1600]</td>
<td style="text-align: left;">outer</td>
</tr>
</tbody>
</table>

Parameters of a Sensitivity analysis.

Different strategies of exploration can be conducted for each parameter
within the sensitivity analysis. This allows to cover large parts of the
parameter space at the minimal cost. Defining *N*<sub>*p*</sub>, the
number of parameters tested for a parameter *p* and *N*<sub>*P*</sub>
the number of parameters, then the number of different inputs tested in
the sensitivity analysis
*N*<sub>*S**A*</sub> = *l**e**n*(*l**i**s**t**O**f**I**n**p**u**t**s*)
(seen at the end of
[Sec. 1](#1-introduction)) is defined by the following
strategies:

-   inner exploration: exploring one dimension at a time.
    $N\_{SA,inner} = \sum\_{p=1}^{p=P} N\_p - N\_P + 1$

-   outer exploration: exploring every dimensions at once.
    $N\_{SA,outer} = \prod\_{p=1}^{p=P} N\_p$

-   random: randomly exploring a fraction *f*<sub>*p*</sub> of each
    dimension at once.
    $N\_{SA,rand} = \prod\_{p=1}^{p=P} f\_p N\_p$
    With *N*<sub>*P*</sub> = 4 and *f*<sub>*p*</sub> = 2/3, only
    (2/3)<sup>4</sup> ≃ 20% of the
    $N\_{SA,outer} = \prod\_{p=1}^{p=P} N\_p$ simulations are performed.

Those strategies are illustrated
Fig.<a href="#fig:sensitivityAnalysis" data-reference-type="ref"
data-reference="fig:sensitivityAnalysis">7</a>.

<figure id="fig:sensitivityAnalysis">
<img src="./figures/sensitivityAnalysis.png" style="width:80.0%" />
<figcaption>Figure 6: Different strategies of sensitivity analysis. Two parameters
are scanned using <span class="math inline">5</span> values for each.
The black box is the initial value. Green boxes = inner exploration (9
boxes). Red box = outer exploration (25 boxes). Purples boxes = random
exploration (15 boxes).</figcaption>
</figure>

## 4. Outputs

Outputs should be defined for debugging purposes, as well as to study
the simulation results.

### 4.1 "Debug" outputs

#### 4.1.1 Textual output

The first debugging outputs should be a/several text file(s) detailing
the whole system as it is initialised by AvailSim4. The content of each
object/list/dictionary should be plotted in a structured way, similarly
to the different input tables, but merged into as few files as possible.
An expert of the studied system should be able to understand this output
file.

#### 4.1.2 Graphical output

In addition to the textual output defining the structure and parameters
of the simulated system, or even its initial state, a graphical output
should be developed to study the simulated timeline of events. Such
figure could be as Fig.<a href="#fig:timeLine" data-reference-type="ref"
data-reference="fig:timeLine">2</a> for a system such as
Fig.<a href="#fig:systemDescription" data-reference-type="ref"
data-reference="fig:systemDescription">4</a>. It is mainly inspired by
[AFT](https://aft.cern.ch/) [4] and
Fig.<a href="#fig:cardio" data-reference-type="ref"
data-reference="fig:cardio">3</a>.

<figure id="fig:sensitivityAnalysis">
<img src="./figures/timelines.png" style="width:80.0%" />
<figcaption>Figure 7: Cartoon of how should look AvailSim4 graphical output. A, B,
C1 and C2 are systems. C1 and C2 are redundant. If both failed, the
whole system is down which is represented with a black box. P represent
the different phases.</figcaption>
</figure>

A discussion has been started with the developers of AFT in order to
process AvailSim4 output data with AFT, saving significant development
time for a graphical output. AvailSim4 could just output data compatible
with the AFT rest API and use it to then generate graphs and even
statistics.

### 4.2 "Study" outputs

With respect to reliability, availability and any performance metric
(e.g. luminosity), in addition to "debug output", we are interested in
statistical results which are for the most part produced by the
[AFT](https://aft.cern.ch/) [4] and used in AWG reports. Discussions are in
progress with the developers of AFT but it seems AFT might struggle to
process 10<sup>3</sup> to 10<sup>6</sup> years of data so AvailSim4
should still process the statistics by itself. Also, due to the large
number of iterations in the Monte Carlo algorithm, statistical
measurements that [AFT](https://aft.cern.ch/) does not produce could be
computed such as probability density functions (≃ histogram) for any
variable of interest. Then, having probability density functions allows
to get mean values, standard deviation and any quantiles. Storing the
results in the form of probability density functions can also allow for
some compression of the results, but mainly enables concatenation of the
results from different simulations.

The following list of variables should be analyzed (the list might be
non-exhaustive):

-   duration of fault and repair by component, failure mode and phase

-   duration and reason for termination of each phase

-   root cause failure (≃ state of the system when a failure occurs)

All those parameters allows to compute duration of "up time" and
"downtime" (availability) as well as the number of critical failures
(reliability). It is necessary to keep in mind that AvailSim4 will be
mainly used to perform sensitivity analyses over large numbers of
parameters, thus it should be easy to load and aggregate multiple
outputs in order to draw sensitivity plots.

## 5. Tests

The continuous integration (CI) framework should be systematically
extended to each feature by the means of unit tests and each model ever
simulated to verify the backward compatibility of the hard-coded/custom
python functions developed for each model (see
[Sec. 8](#8-implementation-of-availsim4)). Also, some analytical tests
(see [Sec. 5.1](#51-analytical-tests)) and sanity checks (see
[Sec. 5.2](#52-sanity-checks)) should be performed.

### 5.1 Analytical tests

Simple systems can be designed in order to verify that simulations
manage to approximate the failure behavior calculated analytically.
Variations of the parameters defining those systems and the
configuration of the Monte Carlo study can easily increase the coverage
of the tests.

-   *N* identical components following an exponential distribution with
    a mean time to fail of 1/*λ* simulated during a time *t*: then the
    probability of failure is *P* = 1 − *e*<sup>−*λ**t**N*</sup>.

-   *M* out of *N* redundancy strategy following the same
    parametrization than the previous example: then the probability of
    failure is
    $P = 1 - \sum\_{i=M}^{N} \frac{N!}{i!(N-i)!}e^{-\lambda t i}(1-e^{-\lambda t})^{N-i}$.

-   forcing the sequencing of events, particular concurrences of
    failures can be produced to test tailored features.

### 5.2 Sanity checks

Sanity checks have always to be true as they are universal rules. They
allow to monitor the quality of the logic within the code. They can be
performed on each simulation or using probability density functions
summarizing the results of a large number of simulations. A long list of
these basic checks can be devised, such as:

-   up/down time partition:
    the duration of downtime plus uptime is equal to the total duration
    of the simulation. (Verified)

-   phase decomposition:
    the sum of time spent in each phase is equal to the total duration
    of the simulation.

-   the down time is equal to the access time + the repair time + the
    restart time.

-   positivity of time duration:
    each duration (phase duration, fault duration, access duration,
    etc.) has to be positive.

-   positivity of spares:
    the amount of spare available cannot be negative.

-   the number of spares used is equal or bellow the initial number of
    spares.

-   a fault can only occur in phases according to the failure mode
    assignment.

-   the total number of components defining the system has to be
    constant.

-   the transition between phases has to follow the transition phase
    table.

-   the number of phase transitions induced by a fault is equal to the
    number of faults inducing a transition of phase.

-   checks of invariants:
    for a system without cycle, using a unique cycling phase should not
    change the statistics.

## 6. List of studies

AvailSim4 was already used for the reliability of the Inner Triplet
protection (see [2]), as well as for a comparative study for the 11 T
magnets. A list of systems which should be modelled in the next 12
months is reported below. The main metrics to describe them is: the
number of components, the number of failure modes, the depth of the
system (= how many layers of components are considered to reach basic
components), the number of iterations per simulation (within the
Discrete Event Simulation algorithm) and the number of simulations
(within the Monte Carlo algorithm). Also the time line for those studies
is specified. A first table focuses on availability model
(Tab.<a href="#tab:availStudies" data-reference-type="ref"
data-reference="tab:availStudies">17</a>, the second table focuses on
reliability model
(Tab.<a href="#tab:reliStudies" data-reference-type="ref"
data-reference="tab:reliStudies">18</a>). That second table generally
requires more components to describe a system, ×<!-- -->100 more
iterations in the Monte Carlo algorithm to converge but 90% less
iterations in the DES algorithm to simulate a timeline.

<table>
<caption>Table 17: Availability studies.</caption>
<thead>
<tr class="header">
<th style="text-align: left;">model</th>
<th style="text-align: center;"># components</th>
<th style="text-align: center;"># fm</th>
<th style="text-align: center;">depth</th>
<th style="text-align: center;">DES iterations</th>
<th style="text-align: center;">MC simulations</th>
<th style="text-align: center;">time of completion</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">LINAC4 simplified</td>
<td style="text-align: center;">12</td>
<td style="text-align: center;">12</td>
<td style="text-align: center;">1</td>
<td style="text-align: center;">400</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;"><strong>done</strong></td>
</tr>
<tr class="even">
<td style="text-align: left;">Booster simplified</td>
<td style="text-align: center;"><span class="math inline">≃</span>
30</td>
<td style="text-align: center;"><span class="math inline">≃</span>
45</td>
<td style="text-align: center;">1</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;">2021</td>
</tr>
<tr class="odd">
<td style="text-align: left;">PS simplified</td>
<td style="text-align: center;"><span class="math inline">≃</span>
30</td>
<td style="text-align: center;"><span class="math inline">≃</span>
45</td>
<td style="text-align: center;">1</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;">2021</td>
</tr>
<tr class="even">
<td style="text-align: left;">SPS simplified</td>
<td style="text-align: center;"><span class="math inline">≃</span>
30</td>
<td style="text-align: center;"><span class="math inline">≃</span>
45</td>
<td style="text-align: center;">1</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;">2021</td>
</tr>
<tr class="odd">
<td style="text-align: left;">LHC simplified</td>
<td style="text-align: center;">30</td>
<td style="text-align: center;">45</td>
<td style="text-align: center;">1</td>
<td style="text-align: center;">2100</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;">end 2020</td>
</tr>
<tr class="even">
<td style="text-align: left;">full chain simplified</td>
<td style="text-align: center;"><span
class="math inline">≃</span>150</td>
<td style="text-align: center;"><span
class="math inline">≃</span>200</td>
<td style="text-align: center;">7</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;">2021</td>
</tr>
<tr class="odd">
<td style="text-align: left;">Myrrha simplified</td>
<td style="text-align: center;"><span
class="math inline">≃</span>150</td>
<td style="text-align: center;"><span
class="math inline">≃</span>200</td>
<td style="text-align: center;">1</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;">end 2020</td>
</tr>
<tr class="even">
<td style="text-align: left;">CLIC simplified</td>
<td style="text-align: center;"><span
class="math inline">≃</span>100</td>
<td style="text-align: center;"><span
class="math inline">≃</span>150</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;">tbd</td>
</tr>
<tr class="odd">
<td style="text-align: left;">FCC simplified</td>
<td style="text-align: center;"><span
class="math inline">≃</span>100</td>
<td style="text-align: center;"><span
class="math inline">≃</span>150</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;">tbd</td>
</tr>
<tr class="even">
<td style="text-align: left;">LINAC4</td>
<td style="text-align: center;"><span class="math inline">≃</span>
400</td>
<td style="text-align: center;"><span class="math inline">≃</span>
600</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;">WIP</td>
</tr>
<tr class="odd">
<td style="text-align: left;">Booster</td>
<td style="text-align: center;"><span class="math inline">≃</span>
100</td>
<td style="text-align: center;"><span class="math inline">≃</span>
300</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;">2021</td>
</tr>
<tr class="even">
<td style="text-align: left;">PS</td>
<td style="text-align: center;"><span class="math inline">≃</span>
100</td>
<td style="text-align: center;"><span class="math inline">≃</span>
300</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;">2021</td>
</tr>
<tr class="odd">
<td style="text-align: left;">SPS</td>
<td style="text-align: center;"><span class="math inline">≃</span>
100</td>
<td style="text-align: center;"><span class="math inline">≃</span>
300</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;">2021</td>
</tr>
<tr class="even">
<td style="text-align: left;">LHC</td>
<td style="text-align: center;"><span class="math inline">≃</span>
100</td>
<td style="text-align: center;"><span class="math inline">≃</span>
300</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;">end of 2021</td>
</tr>
<tr class="odd">
<td style="text-align: left;">full chain</td>
<td style="text-align: center;"><span
class="math inline">≃</span>1000</td>
<td style="text-align: center;"><span
class="math inline">≃</span>2000</td>
<td style="text-align: center;">7</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;">2021</td>
</tr>
<tr class="even">
<td style="text-align: left;">Myrrha</td>
<td style="text-align: center;"><span
class="math inline">≃</span>1000</td>
<td style="text-align: center;"><span
class="math inline">≃</span>2000</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;">end of 2021</td>
</tr>
<tr class="odd">
<td style="text-align: left;">CLIC</td>
<td style="text-align: center;"><span
class="math inline">≃</span>1000</td>
<td style="text-align: center;"><span
class="math inline">≃</span>2000</td>
<td style="text-align: center;">5</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;">tbd</td>
</tr>
<tr class="even">
<td style="text-align: left;">FCC</td>
<td style="text-align: center;"><span
class="math inline">≃</span>1000</td>
<td style="text-align: center;"><span
class="math inline">≃</span>2000</td>
<td style="text-align: center;">5</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^4</td>
<td style="text-align: center;">tbd</td>
</tr>
</tbody>
</table>

Availability studies.

<table>
<caption>Table 18: Reliability studies. * SSA = Solid State Amplifier</caption>
<thead>
<tr class="header">
<th style="text-align: left;">model</th>
<th style="text-align: center;"># components</th>
<th style="text-align: center;"># fm</th>
<th style="text-align: center;">depth</th>
<th style="text-align: center;">DES iterations</th>
<th style="text-align: center;">MC simulations</th>
<th style="text-align: center;">time of completion</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">IT</td>
<td style="text-align: center;">800</td>
<td style="text-align: center;">800</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">150</td>
<td style="text-align: center;">10^6</td>
<td style="text-align: center;"><strong>done</strong></td>
</tr>
<tr class="even">
<td style="text-align: left;">11T</td>
<td style="text-align: center;">110</td>
<td style="text-align: center;">110</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">125</td>
<td style="text-align: center;">10^6</td>
<td style="text-align: center;"><strong>done</strong></td>
</tr>
<tr class="odd">
<td style="text-align: left;">D1 simplified</td>
<td style="text-align: center;"><span
class="math inline">≃</span>50</td>
<td style="text-align: center;"><span
class="math inline">≃</span>50</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^6</td>
<td style="text-align: center;">2020</td>
</tr>
<tr class="even">
<td style="text-align: left;">D2 simplified</td>
<td style="text-align: center;"><span
class="math inline">≃</span>50</td>
<td style="text-align: center;"><span
class="math inline">≃</span>50</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^6</td>
<td style="text-align: center;">2020</td>
</tr>
<tr class="odd">
<td style="text-align: left;">Crab cavities</td>
<td style="text-align: center;"><span
class="math inline">≃</span>50</td>
<td style="text-align: center;"><span
class="math inline">≃</span>50</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^6</td>
<td style="text-align: center;">2021</td>
</tr>
<tr class="even">
<td style="text-align: left;">E-lenses</td>
<td style="text-align: center;"><span
class="math inline">≃</span>50</td>
<td style="text-align: center;"><span
class="math inline">≃</span>50</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^6</td>
<td style="text-align: center;">2021</td>
</tr>
<tr class="odd">
<td style="text-align: left;">Myrrha</td>
<td style="text-align: center;"><span
class="math inline">≃</span>100</td>
<td style="text-align: center;"><span
class="math inline">≃</span>150</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^6</td>
<td style="text-align: center;">2021</td>
</tr>
<tr class="even">
<td style="text-align: left;">Myrrha SSA*</td>
<td style="text-align: center;"><span
class="math inline">≃</span>2000</td>
<td style="text-align: center;"><span
class="math inline">≃</span>1000</td>
<td style="text-align: center;">7</td>
<td style="text-align: center;">?</td>
<td style="text-align: center;">10^6</td>
<td style="text-align: center;">2021</td>
</tr>
</tbody>
</table>

Reliability studies. \* SSA = Solid State Amplifier

### 6.1 Short term

The short term studies are reliability studies required for the HL
project plus the MHYRRHA collaboration.

[**MYRRHA**](https://sckcen.be/en/Technology_future/MYRRHA). This
systems will have to be studied from scratch as no preliminary studies
have been performed within the team. It will required the implementation
of some tailored failure behavior as this system relies on a complex
redundancy mechanism (i.e. fault tolerance) for the RF part. The
collaboration should start during the <u>autumn of 2020</u>. This system
cannot be model by a simple tree. For example, the dynamic compensation
of RF cavity failures will require some custom function in AvailSim4,
but not the development of a general feature, as this is a very specific
use case.

**D1 and D2 magnets**. Following the study of the Inner Triplet
protection reliability, the study of the magnets D1 and D2 should be
performed during <u>2020</u>. For this study, no particular feature in
additon to the basic ones has to be developed.

**Crab cavities**. <u>2021</u>. For this study, no particular feature
has to be developed.

**E-lenses**. <u>2021</u>. For this study, no particular feature has to
be developed.

### 6.2 Mid term

The mid term studies are reliability and availability studies required
to model the whole chain of accelerators at CERN
(seeFig.<a href="#fig:chain" data-reference-type="ref"
data-reference="fig:chain">8</a>). Also a collaboration on
[MYRRHA](https://sckcen.be/en/Technology_future/MYRRHA) will start.

<figure id="fig:chain">
<img src="./figures/Existing-CERN-accelerator-complex.png"
style="width:80.0%" />
<figcaption>Figure 8: Accelerators at CERN.</figcaption>
</figure>

**Linac4**. After initial machine commissioning, a first Reliability Run
(RR) started in July 2017 and lasted until mid-May 2018. A second RR has
been performed in 2019 and allowed to acquire more statistics and could
lead to an update of the initial study. AvailSim3,
[ELMAS](http://www.ramentor.com) [6] and
[Isograph](https://www.isograph.com/) [7] have been used in the past for a
light model and AvailSim3 only for a detailed model. Both the light and
detailed model should be developed with AvailSim4. Finally the model of
the Linac4 is needed to model the whole chain of accelerators at CERN.
This study should be performed during the <u>second semester of
2020</u>.

**Booster**. For this study, the phase feature has to be developed. Also
the "beam destination" feature should be developed (see
Sec.<a href="#sec:features" data-reference-type="ref"
data-reference="sec:features">7</a>).

**PS**. For this study, the phase feature has to be developed. Also the
"beam destination" feature should be developed (see
[Sec. 7](#7-list-of-features)).

**SPS**. For this study, the phase feature has to be developed. Also the
"beam destination" feature should be developed (see
[Sec. 7](#7-list-of-features)).

**LHC**. For this study, the phase feature has to be developed. Also the
"beam destination" feature should be developed (see
[Sec. 7](#7-list-of-features)).


### 6.3 Long term

Long term studies would cover any other upgrade of LHC or any new
accelerator such as FCC and CLIC, in particular their Machine Protection
systems. Some studies of FCC have been performed using
[ELMAS](http://www.ramentor.com) [6], some studies of CLIC have been
performed using AvailSim3 already.


## 7. List of features

Most of the features are self explanatory at the level of the inputs but
the most complex ones are described in this sections
[Sec. 7.1](#71-details-on-core-features). Also some features
which are not general enough to be in the core of AvailSim4 are
described as list of thoughts
[Sec. 7.2](#72-list-of-tailored-features). Finally a few
general optimization features are listed
[Sec. 7.3](#73-optimisation-features).

### 7.1 Details on core features

#### 7.1.1 Status handling feature

Components of a system could be in different status (see
Tab.<a href="#tab:status" data-reference-type="ref"
data-reference="tab:status">19</a>). A hierarchy is established between
the statuses to define the underlying logic in the software.

<table>
<caption>Table 19: List of possible status for basics and components. See enum
class in System/Status.py.</caption>
<thead>
<tr class="header">
<th style="text-align: left;">status</th>
<th style="text-align: left;">meaning</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">FAILED</td>
<td style="text-align: left;">Operation stopped because of a fault
(basic) or a combination of faults of child(ren)</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">(compound). It is the most critical status
for availability as it stops operation.</td>
</tr>
<tr class="odd">
<td style="text-align: left;">BLIND_FAILED</td>
<td style="text-align: left;">Similar to FAILED but for undetectable
failures. It is the most critical status for protection</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">because the protection functionality might
be lost without possibility to detect it.</td>
</tr>
<tr class="odd">
<td style="text-align: left;">DEGRADED</td>
<td style="text-align: left;">Intermediate status between FAILED and
RUNNING, the component is still RUNNING</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">but not in the nominal conditions. It is
less critical than failures as the machine still runs.</td>
</tr>
<tr class="odd">
<td style="text-align: left;">BLIND_DEGRADED</td>
<td style="text-align: left;">Similar to DEGRADED but for undetectable
failures. It is also less critical than FAILED</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">statuses as the machine still runs, but
the failure being blind, no repairs can be scheduled.</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">For protection systems, a critical loss of
redundancy can be produced.</td>
</tr>
<tr class="even">
<td style="text-align: left;">INSPECTION</td>
<td style="text-align: left;">Period of inspection. This status is
chosen more critical than UNDER_REPAIR because</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">it could include repairs and mainly to
better take into account statistics of statuses.</td>
</tr>
<tr class="even">
<td style="text-align: left;">UNDER_REPAIR</td>
<td style="text-align: left;">Period of repair.</td>
</tr>
<tr class="odd">
<td style="text-align: left;">RUNNING</td>
<td style="text-align: left;">Normal operation, any other status in the
system would have priority on this status</td>
</tr>
</tbody>
</table>

List of possible status for basics and components. See enum class in
System/Status.py.

Defining the logic between components is equivalent to specify the two
following functions, given "nS" is the number of children in status "S",
*p**a**r**e**n**t*\_*s**t**a**t**u**s* = *f*<sub>*A**N**D**Y*</sub>(*n**R*,*n**F*,*n**D*,*n**B**F*,*n**B**D*,*n**U**R*,*n**I*)
defines the AND logic with Y children (see see
Tab.<a href="#tab:ANDlogicStatus" data-reference-type="ref"
data-reference="tab:ANDlogicStatus">20</a>) while the XooY logic is
defined by
*p**a**r**e**n**t*\_*s**t**a**t**u**s* = *f*<sub>*X**o**o**Y*</sub>(*n**R*,*n**F*,*n**D*,*n**B**F*,*n**B**D*,*n**U**R*,*n**I*)
(see Tab.<a href="#tab:XooYlogicStatus" data-reference-type="ref"
data-reference="tab:XooYlogicStatus">21</a>). For the XooY logic, some
intermediary variable is used: nCAR is the number of children Considered
As Running, that is to say with the status RUNNING, DEGRADED or
BLIND\_DEGRADED.

<table>
<caption>Table 20: How to attribute status to compound with AND
childrenLogic.</caption>
<thead>
<tr class="header">
<th style="text-align: left;">status</th>
<th style="text-align: left;">AND logic: I &gt;UR &gt;BF &gt;F &gt;BD
&gt;D &gt;R</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">INSPECTION (I)</td>
<td style="text-align: left;">if at least one child is I</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">nF=* , nBF=* , nD=* , nBD=* , nI&gt;0 ,
nUR=* , nR&lt;Y</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr class="even">
<td style="text-align: left;">UNDER_REPAIR (UR)</td>
<td style="text-align: left;">if at least one child is UR and none is
I</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">nF=* , nBF=* , nD=* , nBD=* , nI=0 ,
nUR&gt;0 , nR&lt;Y</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr class="odd">
<td style="text-align: left;">BLIND_FAILED (BF)</td>
<td style="text-align: left;">if at least one child is BF and none is I
or UR</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">nF=* , nBF&gt;0 , nD=* , nBD=* , nI=0 ,
nUR=0 , nR&lt;Y</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr class="even">
<td style="text-align: left;">FAILED (F)</td>
<td style="text-align: left;">if at least one child is F and none is I
or UR or BF</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">nF&gt;0 , nBF=0 , nD=* , nBD=* , nI=0 ,
nUR=0 , nR&lt;Y</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr class="odd">
<td style="text-align: left;">BLIND_DEGRADED (BD)</td>
<td style="text-align: left;">if at least one child is BD and none is I
or UR or BF or F</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">nF=0 , nBF=0 , nD=* , nBD&gt;0 , nI=0 ,
nUR=0 , nR&lt;Y</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr class="even">
<td style="text-align: left;">DEGRADED (D)</td>
<td style="text-align: left;">if at least one child is D and none is I
or UR or BF or F or BD</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">nF=0 , nBF=0 , nD&gt;0 , nBD=0 , nI=0 ,
nUR=0 , nR&lt;Y</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr class="odd">
<td style="text-align: left;">RUNNING (R)</td>
<td style="text-align: left;">if every child is R</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">nF=0 , nBF=0 , nD=0 , nBD=0 , nI=0 , nUR=0
, nR=Y</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
</tbody>
</table>

How to attribute status to compound with AND childrenLogic.

<table>
<caption>Table 21: How to attribute status to compound with XooY
childrenLogic.</caption>
<thead>
<tr class="header">
<th style="text-align: left;">status</th>
<th style="text-align: left;">XooY logic; nCAR = nR + nD + nBD</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: left;">INSPECTION (I)</td>
<td style="text-align: left;">if not enough "considered as running"
children and at least one I</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">nCAR &lt; X , nF + nBF + nD + nBD + nUR =
* , nI&gt;0</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr class="even">
<td style="text-align: left;">UNDER_REPAIR (UR)</td>
<td style="text-align: left;">if not enough "considered as running"
children and at least one UR and no I</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">nCAR &lt; X, nF + nBF + nD + nBD = *, nI=0
, nUR&gt;0</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr class="odd">
<td style="text-align: left;">BLIND_FAILED (BF)</td>
<td style="text-align: left;">if not enough "considered as running"
children and some BLIND but no I or UR status</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">nCAR &lt; X , nBF + nBD &gt; 0 , nF + nD =
* , nI + nUR = 0</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr class="even">
<td style="text-align: left;">FAILED (F)</td>
<td style="text-align: left;">if not enough "considered as running"
children and no BLIND, I or UR status</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">nCAR &lt; X , nBF + nBD = 0 , nF + nD = *
, nI + nUR = 0</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr class="odd">
<td style="text-align: left;">DEGRADED (D)</td>
<td style="text-align: left;">if enough "considered as running" children
and no blind failure</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">X &lt;= nCAR &lt; Y , nBF + nBD = 0 , nF +
nD + nI + nUR = *</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr class="even">
<td style="text-align: left;">BLIND_DEGRADED (D)</td>
<td style="text-align: left;">if enough "considered as running" children
and blind failure</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;">X &lt;= nCAR &lt; Y , nBF + nBD &gt; 0 ,
nF + nD + nI + nUR = *</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr class="odd">
<td style="text-align: left;">RUNNING (R)</td>
<td style="text-align: left;">if every child is considered as
running</td>
</tr>
<tr class="even">
<td style="text-align: left;"></td>
<td style="text-align: left;">nCAR = Y , nF + nBF + nI + nUR = 0</td>
</tr>
<tr class="odd">
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
</tbody>
</table>

How to attribute status to compound with XooY childrenLogic.

#### 7.1.2 Role of B events and C events in DES algorithm

The algorithm used in AvailSim4 (and previous versions of AvailSim) is
based on a Discrete Event Simulation algorithm, with a Three-phase
flavor, within a Monte Carlo algorithm. Tocher [8] and Pidd [9] (both books
difficult to find online) document the "Three-Phase" approach. A short
review of DES history can be found here [10]. This approach makes the
distinction between:

-   B events = Bound events, also called Timed events, Unconditioned
    events. Those events are planned, they do not need any conditions to
    be fulfilled in order to happen but just occur due to a delay being
    expired. In our case, it would be a failure occurring or a repair
    finishing (and its propagation in the system), a periodic inspection
    starting, the end of a phase. B events act on the system and
    generate C events, they do not generate other B events.

-   C events = Conditioned events. Those events are not planned in
    advance but only occur when some particular conditions are present.
    This type of events would be deciding on / planning of actions in
    our case, that is to say creating B events: ordering a repair now or
    at a later date, advancing the end of a phase, etc. The logic
    leading to the creation of B events could be as complex as one
    wants. C events only trigger B events and do not modify the state of
    the system themselves.

A summary of the Discrete Event Simulation algorithm here is presented.

    while True: # keep computing DES

        b_events_valid_context = filtering_according_to_context

        next_b_event = find_next_valid_context_b_event

        if  next_b_event is None or \
            next_b_event.time > duration_of_simulation:
                # stop computing DES
                break

        update_time = next_b_event.time

        execute_valid_context_b_events_and_update_c_events

        execute_c_events_and_update_b_events


A tentative list of B is proposed here:

-   DetectableFailureEvent: a detectable failure changes the status of a
    component to FAILED. This change is immediately propagated to the
    whole system. Depending on the repairSchedule (WIP), immediate or
    shadow (table failureModes
    <a href="#tab:failureModes" data-reference-type="ref"
    data-reference="tab:failureModes">4</a>), different type of C events
    should be generated to then handle the repair.

-   BlindFailureEvent: a blind failure changes the status of a component
    to BLIND\_FAILED. This change is also immediately propagated to the
    whole system but the C event generated is not of the same type.

-   StartRepairingEvent: a start of repair changes the status of a
    component to UNDER\_REPAIR, change which is immediately propagated
    to the whole system. StartRepairingEvent is an immediate action, if
    any wait is required between the failure and the repair, it should
    be modeled by an OrderRepairEvent which waits for some conditions to
    be fulfilled before ordering an immediate repair using a
    StartRepairingEvent event.

-   EndRepairingEvent: an end of repair changes the status of a
    component to RUNNING, change which is immediately propagated to the
    whole system. EndRepairingEvent is an immediate action. The duration
    of the repair is encoded by the C event generating both the
    StartRepairingEvent and EndRepairingEvent. The logic could be more
    complex in later updates of AvailSim4.

-   StartInspectionEvent: a start of inspection event change the status
    to the component to INSPECTION and propagates it. A list of actions
    is performed as described
    [Sec. 7.1.3](#713-inspections).

-   EndInspectionEvent: an end of inspection event change the status to
    the component to RUNNING and propagates it. The duration between
    StartInspectionEvent and EndInspectionEvent is fixed by the C event
    generating those two events.

A tentative list of C is proposed here:

-   OrderFailureEvent: After a repair, a new failure as to be planned as
    the repaired component will eventually fail once more. This is
    performed using OrderFailureEvent, called by the EndRepairingEvent.

-   OrderRepairEvent: when a failure occurred (B event), an "order to
    repair" (C event) is generated. This C event is used to check if
    some resources are ready to start the repair and estimate the end of
    repair time, thus it generates two B events. For now, no check on
    available resources is performed.

-   OrderStartInspection: the start of an inspection is handled by an C
    event as in the future it might be conditioned by different factors
    such as anticipating the start of the inspection if a fault started
    before the theoretical start of the inspection but would last until
    the start of the inspection.

-   OrderEndInspection: the end of an inspection is handled by an C
    event as well as in the future it might be conditioned by different
    factors.

See Fig.<a href="#fig:detailedTimeLine" data-reference-type="ref"
data-reference="fig:detailedTimeLine">9</a> and the sequences bellow:

1.  Initialisation of the first events: failure events and inspection
    events (no phase event for now) populate the list of B events.

2.  Handling the first B event, assuming it is a DetectableFailureEvent.

    1.  Changing status to FAILED.

    2.  Propagating status to parents.

    3.  Generating a C event OrderRepairEvent.

3.  Assuming the next event in the loop is the C event OrderRepairEvent
    (conditions of the C event are met):

    1.  Generating a B event StartRepairingEvent.

    2.  Generating a B event EndRepairingEvent.

    Those two events are generated at once because once a repair is
    started, nothing can interrupt the repair for now.

4.  Assuming the next event is the StartRepairingEvent:

    1.  Changing status to UNDER\_REPAIR.

    2.  Propagating status to parents.

5.  Assuming the next event is the EndRepairingEvent:

    1.  Changing status to RUNNING.

    2.  Propagating status to parents.

    3.  Generating a C event OrderFailureEvent.

6.  Assuming the next event is the OrderFailureEvent:
    Generating a B event DetectableFailureEvent.

<figure id="fig:detailedTimeLine">
<img src="./figures/time_line.png" />
<figcaption>Figure 9: Timeline representing the sequence of events when a
detectable failure occurs.</figcaption>
</figure>

<figure id="fig:detailedTimeLineBlind">
<img src="./figures/time_line_blind.png" />
<figcaption>Figure 10: Timeline representing the sequence of events when a blind
failure occurs.</figcaption>
</figure>

#### 7.1.3 Inspections

Inspections are defined by two floats, a periodicity and a minimal
duration. After a time t = periodicity, the inspection takes place.
Regardless of the status before the inspection, during the inspection
status are forced to INSPECTION while the failure mode concerned
(meaning the coming failures concerned) of each component are reset
(component as good as new). If the duration of repair of a component
which was already at fault is longer than the duration of the periodic
inspection, then the duration of the periodic inspection is extended to
cover the repair duration.

#### 7.1.4 SharedChild feature

The "sharedChild" feature is a feature allowing for different nodes to
share children nodes. Having this feature, the system is not a simple
tree anymore but becomes a [directed acyclic
graph](https://en.wikipedia.org/wiki/Directed_acyclic_graph). To use
this feature, the user would enter the name of the shared child
"*sharedChildName*" in the "*childrenName*" column of the
"*architecture*" table for each parent sharing that given children. The
synthax is "*childName(lastCommonParentName)*. The information
"*lastCommontParentName*" is used to up to which level the shared
component is shared, see
Fig.<a href="#fig:notShared" data-reference-type="ref"
data-reference="fig:notShared">[fig:notShared]</a>,
Fig.<a href="#fig:secShared" data-reference-type="ref"
data-reference="fig:secShared">[fig:secShared]</a> and
Fig.<a href="#fig:rootShared" data-reference-type="ref"
data-reference="fig:rootShared">[fig:rootShared]</a> for self
explanatory examples based on a power supply PS shared by different
components.

<img src="./figures/notShared.png" alt="image" />
<figcaption>Figure 11: The component PS (power supply) is
not shared by any component. The component
is simply called by its name in the column "childrenName".
</figcaption>
<span id="fig:notShared" label="fig:notShared"></span>

<img src="./figures/secShared.png" alt="image" />
<figcaption>Figure 12: The component PS (power supply)
is shared by A and B in each sector (sec1 and
sec2). The component is called with the syntax
"PS(sec)" in the column "childrenName".</figcaption>
<span id="fig:secShared" label="fig:secShared"></span>

<img src="./figures/rootShared.png" alt="image" />
<figcaption>Figure 13: The component PS (power supply) is
unique in the whole system, it is shared by A and
B in both sector (sec1 and sec2). The component
is called with the syntax "PS(ROOT)" in the
column "childrenName".</figcaption>
<span id="fig:rootShared" label="fig:rootShared"></span>

#### 7.1.5 Minimal replaceable unit

In some cases, to repair a unique failed component ones has to replace a
subset of components which forms a "minimal replaceable unit". It would
be the case when a faulty unit is replaced by a spare, while the failure
mode investigations and repair are done later offsite. This can lead to
better availability while in depth diagnostics is performed at a
deferred stage. It can also reduce the dose received by operators.
In AvailSim4, two arguments in the system file / architecture sheet are
used to specify if a component is in an MRU (*inMRU*) and if its failure
trigger the replacement of an MRU (*triggerMRU*). Having two arguments
allows to be more flexible: a component could be in an MRU but never
triggering any MRU, the opposite too. This feature allows for "long
range out of the tree logic" interactions without using complex /
artificial "shared child" logic. See
Fig.<a href="#fig:MRU_map" data-reference-type="ref"
data-reference="fig:MRU_map">[fig:MRU_map]</a> for examples.

<img src="./figures/MRU_map.png" alt="image" />
<figcaption>Figure 14: The component A
which is expensive, when failing,
triggers the replacement of
the MRU, two C components
which are cheap. If a C component
fails, it only triggers the
replacement of the two C components,
not the A component.</figcaption>
<span id="fig:MRU_map" label="fig:MRU_map"></span>

The components included in an MRU are defined using lowest scope common
ancestor like for the shareChildren feature. It allows to model
different configurations such as the two cases described
Fig.<a href="#fig:MRU_lca_root" data-reference-type="ref"
data-reference="fig:MRU_lca_root">[fig:MRU_lca_root]</a> where the
lowest scope common ancestor is the "root" component, defining only one
MRU in the system and
Fig.<a href="#fig:MRU_lca_sec" data-reference-type="ref"
data-reference="fig:MRU_lca_sec">[fig:MRU_lca_sec]</a> where the lowest
scope common ancestor is the "sec" component defining two MRUs in the
system. In those picture the scope is illustrated with yellow boxes.

<img src="./figures/MRU_lca_root.png" alt="image" />
<figcaption>Figure 15: The ROOT component is lowest scope
common ancestor of the MRU, only one MRU is
present in the system (the big yellow box). If the
MRU is triggered, every PS in the system will be
changed.</figcaption>
<span id="fig:MRU_lca_root" label="fig:MRU_lca_root"></span>

<img src="./figures/MRU_lca_sec.png" alt="image" />
<figcaption>Figure 16: The component sec is the lowest scope
common ancestor of the MRU, two MRUs are
defined in the system (the two yellow boxes). If
an MRU is triggered, only PS in on sector will be
changed.</figcaption>
<span id="fig:MRU_lca_sec" label="fig:MRU_lca_sec"></span>

Finally, every component in the minimal replaceable unit would
experience a repair without experiencing themselves a failure. Still
their failure modes (meaning their failures to come) would be reset (all
components belonging to the unit are as good as new).

### 7.2 List of tailored features

-   "beam destination": some accelerators could provide beam to several
    targets/experiments. LHC has 4 experiments, SPS has 3 experiments +
    LHC, etc. This feature could be an extension of the phases feature
    as an accelerator in the injector complex will feed experiments one
    after the other in a so-called supercycle. Some systems will only
    experience failures for particular destinations (e.g. typically
    extraction systems to a given destination).

### 7.3 Optimisation features

-   when simulating the chain of accelerators, it should be possible to
    concatenate models of each accelerator in order to reuse the code
    already written. Being able to concatenate models should allow to
    easily increase the complexity of a model with each study performed,
    as a reliability study of a system under design will become one day
    a system operating at CERN.

-   AvailSim4 should be able to use components which would not be
    defined by the attributes of
    Tab.<a href="#tab:spares" data-reference-type="ref"
    data-reference="tab:spares">13</a> but would be a custom object
    interfacing with Machine Learning algorithms trained for specific
    purposes.

-   splitting the slowest simulation: when doing some sensitivity
    analysis, the slowest simulation is the one requiring the more
    events, if that simulation is spotted and more cores are assigned to
    it, the time required to finished the slowest simulation could be
    reduced. See
    Fig.<a href="#fig:durationOfSimulations" data-reference-type="ref"
    data-reference="fig:durationOfSimulations">11</a> to get an idea of
    how the duration of simulations is distributed for a sensitivity
    analysis of the Inner Triplet. By better distributing the resources
    for the simulations in the red box, the waiting time for the last
    results could be significantly reduced even if the overall
    consumption of core.hours is the same.

    <figure id="fig:durationOfSimulations">
    <img src="./figures/durationOfSimulations.png" style="width:60.0%" />
    <figcaption>Figure 17: Distribution of simulations’ duration for the Inner Triplet
    sensitivity analysis. The distribution tends toward an exponential.
    Three boxes define three group of simulations: green = lots of fast
    simulations, yellow = some normal simulations, red = a few very long
    simulations.</figcaption>
    </figure>

-   only Monte Carlo simulations are foreseen, no Markov Chain or any
    other algorithm. Still, some faster convergence of the Monte Carlo
    simulations could be achieved by using particular sampling of the
    distribution generation, see Quasi-Monte Carlo methods [5]. Also, doing
    the bijection between the parameters asked to be simulated (Mean
    Time To x) and the one actually simulated might avoid some
    overlapping in the sensitivity analysis.

## 8. Implementation of AvailSim4

The new implementation is divided in three parts dealing with 1) the
input, 2) the core of the logic, 3) the output. Those parts are
developed in order to be as independent as possible.

### 8.1 Input

To be easily understandable by users, versioned and shared, the input
should use as few files as possible. The first file, named "system",
fully describes the architecture of the simulated system, the second
file, named "config", describes the parameters of the simulations
algorithm. An optional third file name "sensitivitAnalysis" can be
provided to perform sensitivity analysis. The type of those files should
be xlsx for a wide adoption. Being able to translate an isograph file is
an option kept for further developments.

#### 8.1.1 System file

The system file should follow the Common Input Format description but
only focusing on essential parameters. See tables of
[Sec. 3](#3-inputs). ...WIP...

#### 8.1.2 Config file

The config file is detached from the system file as, during the
development of a system file, some runs will require just a few
iterations of the Monte Carlo algorithm to debug the system file, then a
few thousands iterations to get a idea of the system’s behavior and
finally millions of iterations for the final results. The content of
this file is summarize
Tab.<a href="#tab:simulation" data-reference-type="ref"
data-reference="tab:simulation">15</a>. It appears that a unique system
can be model in different ways, using custom functions to compute the
state of a node according to its children or using several layers of
build-in functions. According to the behavior of the code (execution
time, clarity of the input and the output) some guideline will be
provided.

#### 8.1.3 Sensitivity Analysis file

An optional file can be used to specify sensitivity analysis of
parameters present in the system file, see
Tab.<a href="#tab:sensitivityAnalysis" data-reference-type="ref"
data-reference="tab:sensitivityAnalysis">16</a>.

### 8.2 Core of the logic

From a theoretical point of view any system we would like to simulate
could be described by a graph. Thus, AvailSim4 performance is likely to
be driven by how fast the information can be propagated in the graph. To
build the graph, three options are studied, two libraries
([igraph](https://igraph.org/redirect.html),
[networkx](https://networkx.github.io/)) and a custom approach. A short
study showed that both igraph and networkx have an extremely large
number of features compared to what is required. Both seems to be quite
well maintained (compatibility insured for the last three minor revision
for igraph  ≃ 3 to 6 years) but maybe the foreseen use of 15 years for
AvailSim4 set a limit on which library we should depend on. Last but not
least, even if igraph partially supports (test in the CI) pypy, using
cython, pythran or pypy to compile / run AvailSim4 might be more
complicated. As the second main contribution to the execution time
should be features written in pure python, it is preferred to avoid any
possible issue in the core of AvailSim4. In the end, the custom option
in the form of dictionary of dictionaries is foreseen, such option seems
to be widely adopted in various project as a graph simply requires a few
attributes such as parents, children, siblings in an object to be
implemented.
An UML sketch is present in the git repository, in the directory
documentation.

#### 8.2.1 Accelerating the core

In order to lower the execution time, some intermediate variables could
be used to avoid the browse the graph too many times. Linear algebra
computations based somehow on markov chain are explored to accelerate
the propagation of the state of the system. A list of tuples containing
the time and description of the foreseen events would accelerate the
search for the next events.

### 8.3 Output

The output should be a unique xlsx or ods file for the same reasons of
versioning and sharing than the input. The output could contain
different level of details.

#### 8.3.1 Output summary

A summary of the results should be presented in one sheet, containing
the main metric such as the duration of faults, number of faults,
availability, ... Also some simple and generic computations helping to
understand the results of the simulations could be provided such as the
expected availability directly computed knowing the number of components
in the systems, their MTTF and MTTR, thus without taking into account
the complex mechanisms of phases, different repair strategies or even
redundancies. Other sheets could contain different analysis of the first
sheet, analysis with respect to the phases, the different nodes, the
failure modes, ... The last level, which would not always be saved in
the output to decrease the execution time, would be the complete time
line of each component. Such details can be used to debug the code or to
plot cardiogram using AFT. A file summarizing the architecture of the
system as produced by the input reader would also be provided for debug
purposes and sanity checks.

#### 8.3.2 Post processing of outputs

Mainly for sensitivity analysis and parallel computations, the
concatenation of many simulations has to be possible. In order to
simplify the concatenation, sheets should be tables with well defined
headers that could be concatenated. For sensitivity analysis, a simple
concatenation of files is performed. For parallel computations of the
same system defined by the same parameters except the random seed, then
the concatenation is rather a merge requiring a weighted average for
some metric
(*x*<sub>*n**e**w*</sub> = (*x*<sub>1</sub>\**N*<sub>1</sub>+*x*<sub>2</sub>\**N*<sub>2</sub>)/(*N*<sub>1</sub>+*N*<sub>2</sub>)),
simple sums for other, search of minimum / maximum, etc.

## 9. Outlook

AvailSim4 is a software developed at CERN to perform availability and
reliability studies. It is estimated that this software should be
maintained for at least 15 years. It is written in Python3 and the
decision is to adopt free scripting for specific features of particular
use cases to keep the software core as light as possible. Performance is
a concern as Monte Carlo simulations coupled with sensitivity analyses
can require large amounts of computing power. Some of the post treatment
could be interfaced with the AFT.

## License

Copyright (c) CERN 2021. Released under the GPL 3.0 only license. All
rights not expressly granted are reserved.

## Bibliography

[1] <https://sckcen.be/en/Technology_future/MYRRHA>

[2] <https://edms.cern.ch/document/2308131/1>, Reliability studies for
HL-LHC Inner Triplet magnets protection, internal note
[3] <https://indico.cern.ch/event/730849/>, Common Input Format and
OpenMars, O. Rey Orozco, 30/05/2018 RASWG meeting, slide 9

[4] <https://aft.cern.ch/>

[5] <https://en.wikipedia.org/wiki/Quasi-Monte_Carlo_method>

[6] ELMAS official website: <http://www.ramentor.com>

[7] Isograph official website: <https://www.isograph.com/>

[8] K.D. Tocher, The Art of Simulation, English
Universit yPress, Great Britain, 1963.

[9] M. Pidd, Computer Simulation in Management Science,
fourth ed., Wiley, Great Britain, 1998

[10] ROBINSON,S.,2005. Discrete-event simulation: from the pioneers to the
present, what next? Journal of the Operational Research So ciety, 56(6),
pp.619-629 <https://core.ac.uk/download/pdf/9689714.pdf>

## Footnotes

\* HTCondor is an interface used to schedule jobs over cluster/grid,
the main cluster at CERN uses HTCondor and it is often referenced as
HTCondor itself
