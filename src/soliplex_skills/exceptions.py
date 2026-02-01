"""Soliplex-specific exceptions for Skills adapter."""

from __future__ import annotations


class SoliplexSkillsError(Exception):
    """Base exception for soliplex_skills errors."""


class SkillsConfigurationError(SoliplexSkillsError):
    """Configuration-related errors."""


class SkillsAdapterError(SoliplexSkillsError):
    """Adapter operation errors."""
