# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.context.system import failure_factory
from availsim4core.src.context.system.failure_factory import FailureFactoryError


class test_FailureFactory(unittest.TestCase):

    def test_build_exception(self):
        with self.assertRaises(FailureFactoryError) as context:
            failure_factory.build("impossible_value")
        self.assertTrue("Wrong type of failure" in str(context.exception))
