# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for the Event class
"""

from availsim4core.src.context.context import Context


class Event:
    """
    Global Interface to define an event (b_event or c_event)
    event are processed in the Discrete event simulation algorithm.
    Events are immutable objects.
    """
    __slots__ = ['context']

    def __init__(self,
                 context: Context):
        self.context = context
