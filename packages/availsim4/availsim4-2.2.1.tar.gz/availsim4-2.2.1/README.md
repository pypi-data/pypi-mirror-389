# AvailSim4

Availsim 4 is a software to predict reliability and availability of modern particle accelerators and the related
technical systems. It is based on a Monte Carlo Discrete Event Simulation algorithm and allows for advanced availability
and reliability statistics.

## Requirements

Python >=3.7 with external dependencies; the requirements are listed in `pyproject.toml` file and grouped into 4
options: graphs, quasi-mc, test, dev. See the user guide for details on how to use them.

## Installation

The default installation process does not feature optional dependencies for visualization and optimized sampling options. To make those available, make sure to follow the instriuctions for installation of optional elements listed below.

AvailSim4 can be installed as whole Python project by clonning this repository or as a Python package through a package manager. Below you can find instructions for both possibilities.

### PyPI repository

Use the package manager pip to install AvailSim4.

```pip install availsim4```

To install all optional dependencies, follow the instructions provided in sections below and then use the following command:

```pip install 'availsim4[graphs, quasi-mc, test]'```

The optional groups of dependencies are `graphs`, `quasi-mc` and `test`:

- `graphs` enables the `GRAPHS` exporter to produce graphs of the components. Additional pre-requirements described below.
- `quasi-mc` installs the QmcPy library for some optimized sampling features. Additional pre-requirements described below.
- `test` adds dependencies required to run the test suite (not related to standard use of the framework).

You can also select groups of dependencies, for instance `[graphs, quasi-mc]` to only use a selected subset of the optional dependencies.

### Gitlab

To clone and set up the Python project:

- Clone the project from <https://gitlab.cern.ch/availsim4/availsim4core> and enter the projects directory.
- Optionally, create a dedicated virtual environment (`python -m venv env` will create an environment named `env`).
- Trigger an editable installation with setuptools from the local directory using `pip install -e '.[quasi-mc, graphs, test]'`. You can modify the list in the brackets to select only desired groups of dependencies.

### Visualization tools (optional)

To generate a diagram of the architecture tree, AvailSim4 relies on PyGraphviz package and Graphviz tool. For more information and OS-specific installation guide, please refer to the Graphviz webpage: <https://graphviz.org/download/> and PyGraphviz: <https://pygraphviz.github.io/documentation/stable/install.html>.

General instructions:

- **Linux**: install Graphviz through your system package manager and then make sure to install PyGraphviz with `pip`: `apt-get update`, `apt-get install libgraphviz-dev`, `pip install pygraphviz`.
- **Windows**: Graphviz installation wizard can be downloaded manually from the website. Then proceed to install PyGraphviz with `pip` or `conda`. Make sure that `dot` program's plugins are configured by running `dot -c` command in your environment. May also require Microsoft C++ Build Tools.
- **MacOS**: you can install Graphviz using Homebrew package manager by running command `brew install graphviz` and then `pip install pygraphviz`.

### Pre-requirement for Windows users (optional)

The external library used for Quasi-Monte Carlo requires Windows users to install Microsoft Visual C++ 14.0 or greater. It can be downloaded from "Microsoft C++ Build Tools": <https://visualstudio.microsoft.com/visual-cpp-build-tools/>, this requirement is needed to use the Quasi-Monte-Carlo algorithm. CERN's Windows users might prefer to use SWAN notebooks which are running on Linux machines.

## Usage

To run AvailSim4 from a command line, you can use the following:

```bash
availsim4 [-h]
  --system SYSTEM
  --simulation SIMULATION
  --output_folder OUTPUT_FOLDER
  [--sensitivity_analysis SENSITIVITYANALYSIS]
  [--HTCondor]
  [--HTCondor_extra_argument OPTIONAL_EXTRA_ARGUMENT]
  [--nb_processes NB_PROCESS]
  [--children_logic PYTHON_FILE]
```

Example call starting one of the end-to-end tests manually:

```bash
python availsim4.py --system availsim4core/test/E2E/input/convergence/convergence_test_system.xlsx --simulation availsim4core/test/E2E/input/convergence/N1000_simulation.xlsx --output_folder output/E2E_example/
```

You can see the results after the execution finishes in the `output/E2E_example` directory.

Alternatively, Availsim4 can be used as a module from within Python scripts or notebooks:

```python
import availsim4core.main


availsim4core.main.start(path_simulation = 'path/simulation/file.xlsx',
            path_system = 'path/system/file.xlsx',
            output_folder = 'path/output/folder/',
            path_sensitivity_analysis="",
            HTCondor=False,
            nb_processes=1)
```

A notebook, [notebook_example_availsim4.ipynb](notebook_example_availsim4.ipynb), provides more examples of how to use the
framework as a module. It shows basic steps that can be performed with AvailSim4. To use it, you can clone the entire
project or download the file separately -- to use with AvailSim4 already installed in your Python environment.

Support features for running AvailSim4 on the HTCondor grid are described in the user guide.

## Documentation

A user guide is provided in the [user guide](doc/user_guide/user_guide.md). It lists all functionalities of the AvailSim4, along with options and relevant descritions.

For developers wishing to contribute to the code, a dedicated [developer guide](doc/user_guide/developer_guide.md) is being created to provide useful explanations of general implementation concepts and gather all development-specific aspects of the project, such as chosen coding conventions and other decisions - to support coherent approach in the long run.

## Contributing

Contributions are welcome. For any such inquiries please reach out via [email](mailto:availsim4-developers@cern.ch).

This project requires contributors to agree to Developer Certificate of Origin (DCO) by adding a dedicated `Signed-off-by:` line to all commits. Please use `git commit –signoff` in order to automate this. All merge requests must include a signature in the form: `Signed-off-by: Firstname Lastname <email.address@domain.org>`.

## License

Copyright © CERN 2021. Released under the [GPL 3.0 only license](LICENSE). All rights not expressly granted are reserved.
