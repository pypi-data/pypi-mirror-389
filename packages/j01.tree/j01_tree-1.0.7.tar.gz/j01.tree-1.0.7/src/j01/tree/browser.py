##############################################################################
#
# Copyright (c) 2007 Projekt01 GmbH and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
from __future__ import absolute_import
"""
$Id: browser.py 5700 2025-10-28 08:47:39Z rodrigo.ristow $
"""
__docformat__ = 'restructuredtext'

import zope.interface
import zope.component
from zope.publisher.interfaces.browser import IBrowserRequest

from j01.tree import interfaces
from j01.tree.interfaces import JSON_TREE_ID
from j01.tree import base


# simple trees
@zope.interface.implementer(interfaces.ISimpleJSONTree)
class SimpleJSONTree(base.TreeBase, base.PythonRendererMixin, 
    base.IdGeneratorMixin):
    """Simple JSON tree using inline methods for rendering elements and
    using traversable path for item lookup.
    """


    def update(self):
        super(SimpleJSONTree, self).update()


# generic template based tree
@zope.interface.implementer(interfaces.ILITagProvider)
class LITagProvider(base.ProviderBase, base.IdGeneratorMixin):
    """LI tag content provider."""

    zope.component.adapts(zope.interface.Interface, IBrowserRequest, 
        interfaces.ITemplateRenderer)

    j01TreeId = JSON_TREE_ID


@zope.interface.implementer(interfaces.IULTagProvider)
class ULTagProvider(base.ProviderBase, base.IdGeneratorMixin):
    """UL tag contet provider."""

    zope.component.adapts(zope.interface.Interface, IBrowserRequest, 
        interfaces.ITemplateRenderer)

    childTags = None

    j01TreeId = JSON_TREE_ID


@zope.interface.implementer(interfaces.ITreeProvider)
class TreeProvider(base.ProviderBase, base.IdGeneratorMixin):
    """UL tag contet provider."""

    zope.component.adapts(zope.interface.Interface, IBrowserRequest, 
        interfaces.ITemplateRenderer)

    # provider id, class and name
    j01TreeId = JSON_TREE_ID
    j01TreeClass = JSON_TREE_ID
    j01TreeName = JSON_TREE_ID
    childTags = None


@zope.interface.implementer(interfaces.IGenericJSONTree)
class GenericJSONTree(base.TreeBase, base.TemplateRendererMixin, 
    base.IdGeneratorMixin):
    """IntId base object lookup and template base rendering.
    
    This implementation uses IContentProvider for element tag rendering.
    This content provider are resonsible for represent a node. This allows us 
    to embed html or javascript calls in the html representation in a smart 
    way.
    """


    liProviderName = 'li'
    ulProviderName = 'ul'
    treeProviderName = 'tree'

    def update(self):
        super(GenericJSONTree, self).update()