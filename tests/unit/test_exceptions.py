"""Tests for soliplex_skills.exceptions module."""

from __future__ import annotations

import pytest

from soliplex_skills.exceptions import SkillsAdapterError
from soliplex_skills.exceptions import SkillsConfigurationError
from soliplex_skills.exceptions import SoliplexSkillsError


class TestExceptionHierarchy:
    """Test exception class hierarchy."""

    def test_base_exception(self):
        """Test SoliplexSkillsError is an Exception."""
        exc = SoliplexSkillsError("test error")
        assert isinstance(exc, Exception)
        assert str(exc) == "test error"

    def test_configuration_error_inherits_base(self):
        """Test SkillsConfigurationError inherits from base."""
        exc = SkillsConfigurationError("config error")
        assert isinstance(exc, SoliplexSkillsError)
        assert isinstance(exc, Exception)

    def test_adapter_error_inherits_base(self):
        """Test SkillsAdapterError inherits from base."""
        exc = SkillsAdapterError("adapter error")
        assert isinstance(exc, SoliplexSkillsError)
        assert isinstance(exc, Exception)

    def test_can_catch_all_with_base(self):
        """Test catching all errors with base exception."""
        errors = [
            SoliplexSkillsError("base"),
            SkillsConfigurationError("config"),
            SkillsAdapterError("adapter"),
        ]
        for error in errors:
            with pytest.raises(SoliplexSkillsError):
                raise error
