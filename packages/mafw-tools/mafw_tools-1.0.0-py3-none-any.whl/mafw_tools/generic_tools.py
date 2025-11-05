#  Copyright 2025 European Union
#  Author: Bulgheroni Antonio (antonio.bulgheroni@ec.europa.eu)
#  SPDX-License-Identifier: EUPL-1.2
"""
Generic utility functions for common operations.

This module provides utility functions that can be used across different parts
of the application. Currently, it contains a function for retrieving nested
attributes from objects using dotted notation.

.. versionadded:: 1.0.0

"""

from typing import Any


def getattr_nested(obj: Any, attr: str) -> Any:
    """
    Retrieve the value of a nested attribute from an object using a dotted path.

    This function allows accessing nested attributes using dot notation.
    For example, given an object with a nested structure like ``obj.attr1.attr2``,
    this function will traverse the path and return the final value.

    :param obj: The object from which to retrieve the attribute.
    :type obj: Any
    :param attr: The dotted path of the attribute to retrieve.
    :type attr: str
    :return: The value of the nested attribute.
    :rtype: Any
    :raises AttributeError: If any attribute in the path does not exist.

    :Example:

    >>> class First:
    ...     def __init__(self, a):
    ...         self.a = a

    >>> class Second:
    ...     def __init__(self, b):
    ...         self.b = First(b)

    >>> m = Second(3)
    >>> getattr_nested(m, 'b.a')
    3
    """
    attrs = attr.split('.')
    for a in attrs:
        obj = getattr(obj, a)
    return obj
