# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .._models import BaseModel

__all__ = ["RepoTokenCreateResponse"]


class RepoTokenCreateResponse(BaseModel):
    token: str
    """The generated repo token (starts with 'rlcr-')"""

    name: str

    repo_ids: List[str]
