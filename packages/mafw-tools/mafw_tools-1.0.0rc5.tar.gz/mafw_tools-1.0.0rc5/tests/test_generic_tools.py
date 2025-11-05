#  Copyright 2025 European Union
#  Author: Bulgheroni Antonio (antonio.bulgheroni@ec.europa.eu)
#  SPDX-License-Identifier: EUPL-1.2
#  Copyright 2025 European Union
#  Author: Bulgheroni Antonio (antonio.bulgheroni@ec.europa.eu)
#  SPDX-License-Identifier: EUPL-1.2
"""
Unit tests for generic tools functions.

This module contains unit tests for the functions in generic_tools.py,
focusing on getattr_nested function.
"""

from unittest.mock import Mock

import pytest

from mafw_tools.generic_tools import getattr_nested


class TestGetattrNested:
    """Test cases for getattr_nested function."""

    def test_basic_nested_attribute_access(self):
        """Test basic nested attribute access with multiple levels."""

        class First:
            def __init__(self, a):
                self.a = a

        class Second:
            def __init__(self, b):
                self.b = First(b)

        m = Second(3)
        assert getattr_nested(m, 'b.a') == 3

    def test_single_attribute_access(self):
        """Test accessing a single attribute without nesting."""

        class TestObj:
            def __init__(self, value):
                self.value = value

        obj = TestObj('test_value')
        assert getattr_nested(obj, 'value') == 'test_value'

    def test_empty_string_attribute(self):
        """Test behavior with empty string attribute."""

        class TestObj:
            def __init__(self, value):
                self.value = value

        obj = TestObj('test_value')
        # This should raise AttributeError since there's no empty attribute
        with pytest.raises(AttributeError):
            getattr_nested(obj, '')

    def test_deeply_nested_attributes(self):
        """Test accessing deeply nested attributes."""

        class Level1:
            def __init__(self, val):
                self.val = val

        class Level2:
            def __init__(self, level1):
                self.level1 = level1

        class Level3:
            def __init__(self, level2):
                self.level2 = level2

        level1 = Level1('deep_value')
        level2 = Level2(level1)
        level3 = Level3(level2)

        assert getattr_nested(level3, 'level2.level1.val') == 'deep_value'

    def test_missing_attribute_raises_attribute_error(self):
        """Test that missing attributes raise AttributeError."""

        class TestObj:
            def __init__(self, value):
                self.value = value

        obj = TestObj('test_value')
        with pytest.raises(AttributeError):
            getattr_nested(obj, 'nonexistent')

    def test_missing_intermediate_attribute_raises_attribute_error(self):
        """Test that missing intermediate attributes raise AttributeError."""

        class First:
            def __init__(self, a):
                self.a = a

        class Second:
            def __init__(self, b):
                self.b = First(b)

        m = Second(3)
        with pytest.raises(AttributeError):
            getattr_nested(m, 'b.nonexistent')

    def test_attribute_with_none_value(self):
        """Test accessing attribute with None value."""

        class TestObj:
            def __init__(self):
                self.none_attr = None

        obj = TestObj()
        assert getattr_nested(obj, 'none_attr') is None

    def test_attribute_with_complex_object(self):
        """Test accessing attribute with complex object value."""

        class Inner:
            def __init__(self, data):
                self.data = data

        class Outer:
            def __init__(self):
                self.inner = Inner([1, 2, 3])

        obj = Outer()
        assert getattr_nested(obj, 'inner.data') == [1, 2, 3]

    def test_invalid_input_type(self):
        """Test behavior with invalid input types."""
        # Test with None object
        with pytest.raises(AttributeError):
            getattr_nested(None, 'any_attr')

        # Test with non-string attribute
        class TestObj:
            def __init__(self, value):
                self.value = value

        obj = TestObj('test')
        with pytest.raises(AttributeError):
            getattr_nested(obj, 123)  # Should fail because 123 is not a string

    def test_mocked_objects(self):
        """Test with mocked objects to avoid real dependencies."""
        mock_obj = Mock()
        mock_obj.attribute = 'mocked_value'

        result = getattr_nested(mock_obj, 'attribute')
        assert result == 'mocked_value'

    def test_multiple_dots_in_path(self):
        """Test paths with multiple dots."""

        class A:
            def __init__(self):
                self.b = B()

        class B:
            def __init__(self):
                self.c = C()

        class C:
            def __init__(self):
                self.d = 'final_value'

        obj = A()
        assert getattr_nested(obj, 'b.c.d') == 'final_value'
