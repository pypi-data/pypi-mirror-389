# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for Failure class
"""

from enum import Enum


class FailureType(Enum):
    """
    Enumerative-style class for two types of a failure
    """

    DETECTABLE = "DETECTABLE"
    BLIND = "BLIND"

    def __str__(self):
        return str(self.name)

    def __eq__(self, other):
        return self.value == other.value


class Failure:
    """
    Objects of this class represent failures
    """

    __slots__ = ['type_of_failure']

    def __init__(self, type_of_failure: FailureType):
        self.type_of_failure = type_of_failure

    def __str__(self):
        return f"Failure: {self.type_of_failure}"

    def __eq__(self,other):
        return self.type_of_failure == other.type_of_failure
