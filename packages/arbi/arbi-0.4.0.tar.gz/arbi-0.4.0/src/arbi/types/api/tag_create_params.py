# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["TagCreateParams"]


class TagCreateParams(TypedDict, total=False):
    name: Required[str]

    workspace_ext_id: Required[str]

    parent_ext_id: Optional[str]

    shared: Optional[bool]

    workspace_key: Annotated[str, PropertyInfo(alias="workspace-key")]
