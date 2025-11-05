###############################################################################
#
# Copyright (c) 2012 Projekt01 GmbH and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
###############################################################################
"""
$Id: tests.py 5713 2025-11-04 16:28:58Z roger.ineichen $
"""
__docformat__ = "reStructuredText"

import unittest
import doctest

import m01.fs.testing

def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('README.txt',
            setUp=m01.fs.testing.setUpStubMongo,
            tearDown=m01.fs.testing.tearDownStubMongo,
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
            ),
        ))


if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
