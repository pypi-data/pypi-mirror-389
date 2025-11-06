###############################################################################
#
# Copyright (c) 2015 Projekt01 GmbH.
# All Rights Reserved.
#
###############################################################################
"""Tests
$Id:$
"""
__docformat__ = "reStructuredText"

import unittest
import doctest


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('checker.txt'),
        ))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')