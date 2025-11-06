# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from enum import Enum


class Status(Enum):
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    DEGRADED = "DEGRADED"
    BLIND_FAILED = "BLIND_FAILED"
    BLIND_DEGRADED = "BLIND_DEGRADED"
    UNDER_REPAIR = "UNDER_REPAIR"
    INSPECTION = "INSPECTION"
    HELD = "HELD"

    def __str__(self):
        return str(self.name)
