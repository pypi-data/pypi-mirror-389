# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

class ExplorationStrategy:
    """
    Represents the available strategies for a {sensitivity_analysis}.
    """

    def __init__(self, parameter_name, values):
        self.parameter_name = parameter_name
        self.values = values

    def __iter__(self):
        for value in self.values:
            yield value

    def __eq__(self, other):
        return self.parameter_name == other.parameter_name \
               and self.values == other.values

    def __repr__(self):
        return f"ExplorationStrategy {self.__class__.__name__}: {self.parameter_name}, values {self.values} "


class Inner(ExplorationStrategy):
    def __init__(self, parameter_name, values):
        super().__init__(parameter_name, values)


class Outer(ExplorationStrategy):
    def __init__(self, parameter_name, values):
        super().__init__(parameter_name, values)

class Zip(ExplorationStrategy):
    def __init__(self, parameter_name, values):
        super().__init__(parameter_name, values)
