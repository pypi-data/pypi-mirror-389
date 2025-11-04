# Copyright (C) 2015 Jonathan Laperle. All Rights Reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# =============================================================================
"""Unit tests for 'error' module."""
from __future__ import absolute_import, division, print_function

import pytest

from epigeec.python.core.error import MultiValidationError, ValidationError

# --- Tests for ValidationError ---


def test_validation_error_message():
    """Verify that the string representation of ValidationError is its message."""
    err_msg = "test"
    with pytest.raises(ValidationError) as excinfo:
        raise ValidationError(err_msg)
    # Check that the exception's message is correct
    assert str(excinfo.value) == err_msg


def test_validation_error_is_raised():
    """Verify that ValidationError can be raised and caught."""
    with pytest.raises(ValidationError):
        raise ValidationError("test")


# --- Tests for MultiValidationError ---


def test_multi_validation_error_message():
    """Verify the string representation of a MultiValidationError."""
    err_msg = "\ntest"

    with pytest.raises(MultiValidationError) as excinfo:
        # Simulate creating a MultiValidationError from a child error
        try:
            raise ValidationError("test")
        except ValidationError as e:
            raise MultiValidationError([e]) from e

    assert str(excinfo.value) == err_msg


def test_multi_validation_error_is_raised():
    """Verify that MultiValidationError can be raised and caught."""
    with pytest.raises(MultiValidationError):
        try:
            raise ValidationError("test")
        except ValidationError as e:
            raise MultiValidationError([e]) from e
