# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

class SystemModifier:

    def __init__(self,
                 parameter_name,
                 value):
        self.parameter_name = parameter_name
        self.value = value

    def __str__(self):
        return f"parameter {self.parameter_name} -> new value: {self.value}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.parameter_name == other.parameter_name \
               and self.value == other.value
