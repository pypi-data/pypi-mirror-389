# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

from .._types import SequenceNotStr

__all__ = ["RepoTokenCreateParams"]


class RepoTokenCreateParams(TypedDict, total=False):
    name: Required[str]
    """Human-readable name for the token"""

    repo_ids: Required[SequenceNotStr[str]]
    """List of repository UUIDs this token can access"""
